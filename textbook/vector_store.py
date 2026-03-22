"""
Vector Store — ChromaDB-based vector storage for textbook chunks.
Uses ChromaDB's built-in ONNX embedding function (all-MiniLM-L6-v2).
"""

import os
import json
import hashlib
from typing import List, Optional, Dict
from pathlib import Path
from dataclasses import dataclass

from .pdf_processor import TextChunk

# ─── Constants ───
COLLECTION_NAME = "textbook_chunks"
METADATA_FILE = "textbook_metadata.json"

# Persist directory
_BASE_DIR = Path(__file__).parent
VECTOR_DB_DIR = _BASE_DIR / "vector_db"
METADATA_PATH = _BASE_DIR / "vector_db" / METADATA_FILE


@dataclass
class SearchResult:
    """A single search result from the vector store."""
    text: str
    grade: str
    unit: str
    page_start: int
    page_end: int
    score: float
    textbook_filename: str


class VectorStore:
    """ChromaDB-backed vector store for textbook chunks."""

    def __init__(self):
        import chromadb
        from chromadb.config import Settings
        from chromadb.utils.embedding_functions import DefaultEmbeddingFunction

        VECTOR_DB_DIR.mkdir(parents=True, exist_ok=True)

        self._embed_fn = DefaultEmbeddingFunction()

        self._client = chromadb.PersistentClient(
            path=str(VECTOR_DB_DIR),
            settings=Settings(anonymized_telemetry=False),
        )

        self._collection = self._client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
            embedding_function=self._embed_fn,
        )

        self._metadata = self._load_metadata()

    # ─── Metadata persistence ───

    def _load_metadata(self) -> Dict:
        """Load textbook metadata from JSON file."""
        if METADATA_PATH.exists():
            with open(METADATA_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        return {"textbooks": {}}

    def _save_metadata(self):
        """Save textbook metadata to JSON file."""
        METADATA_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(METADATA_PATH, "w", encoding="utf-8") as f:
            json.dump(self._metadata, f, ensure_ascii=False, indent=2)

    # ─── Textbook ID generation ───

    @staticmethod
    def _generate_textbook_id(filename: str, grade: str) -> str:
        """Generate deterministic textbook ID from filename + grade."""
        raw = f"{grade}_{filename}"
        return hashlib.md5(raw.encode()).hexdigest()[:12]

    # ─── Add chunks ───

    def add_chunks(
        self,
        chunks: List[TextChunk],
        textbook_id: str,
        filename: str,
        grade: str,
        units: List[str],
    ) -> int:
        """
        Add text chunks to the vector store.
        Returns number of chunks added.
        """
        if not chunks:
            return 0

        # Prepare data
        ids = []
        documents = []
        metadatas = []

        for i, chunk in enumerate(chunks):
            chunk_id = f"{textbook_id}_{i}"
            ids.append(chunk_id)
            documents.append(chunk.text)
            metadatas.append({
                "grade": chunk.grade,
                "unit": chunk.unit,
                "page_start": chunk.page_start,
                "page_end": chunk.page_end,
                "textbook_id": textbook_id,
                "textbook_filename": chunk.textbook_filename,
            })

        # Add to ChromaDB (batch add — ChromaDB generates embeddings automatically)
        batch_size = 500
        for start in range(0, len(ids), batch_size):
            end = min(start + batch_size, len(ids))
            self._collection.add(
                ids=ids[start:end],
                documents=documents[start:end],
                metadatas=metadatas[start:end],
            )

        # Update metadata
        self._metadata["textbooks"][textbook_id] = {
            "filename": filename,
            "grade": grade,
            "total_chunks": len(chunks),
            "units": units,
        }
        self._save_metadata()

        return len(chunks)

    # ─── Search ───

    def search(
        self,
        query: str,
        grade: str,
        unit: Optional[str] = None,
        top_k: int = 5,
    ) -> List[SearchResult]:
        """
        Semantic search in the vector store filtered by grade (and optionally unit).
        Returns a list of SearchResult objects.
        """
        # Build where filter
        where_filter: Dict = {"grade": grade}
        if unit:
            where_filter = {
                "$and": [
                    {"grade": grade},
                    {"unit": {"$eq": unit}},
                ]
            }

        # Query — ChromaDB handles embedding the query text automatically
        try:
            results = self._collection.query(
                query_texts=[query],
                n_results=top_k,
                where=where_filter,
                include=["documents", "metadatas", "distances"],
            )
        except Exception:
            # If filter yields nothing, return empty
            return []

        # Parse results
        search_results: List[SearchResult] = []
        if results and results["documents"]:
            docs = results["documents"][0]
            metas = results["metadatas"][0]
            distances = results["distances"][0]

            for doc, meta, dist in zip(docs, metas, distances):
                # ChromaDB cosine distance: 0 = identical, 2 = opposite
                # Convert to similarity score: 1 - (dist / 2)
                score = round(1.0 - (dist / 2.0), 4)
                search_results.append(SearchResult(
                    text=doc,
                    grade=meta.get("grade", ""),
                    unit=meta.get("unit", ""),
                    page_start=meta.get("page_start", 0),
                    page_end=meta.get("page_end", 0),
                    score=score,
                    textbook_filename=meta.get("textbook_filename", ""),
                ))

        return search_results

    # ─── List textbooks ───

    def list_textbooks(self) -> List[Dict]:
        """List all uploaded textbooks."""
        books = []
        for tid, info in self._metadata.get("textbooks", {}).items():
            books.append({
                "textbook_id": tid,
                "filename": info["filename"],
                "grade": info["grade"],
                "total_chunks": info["total_chunks"],
                "units": info.get("units", []),
            })
        return books

    # ─── Delete textbook ───

    def delete_textbook(self, textbook_id: str) -> bool:
        """Delete a textbook's chunks from the vector store."""
        if textbook_id not in self._metadata.get("textbooks", {}):
            return False

        # Delete all chunks with this textbook_id
        try:
            self._collection.delete(
                where={"textbook_id": textbook_id},
            )
        except Exception:
            pass

        # Remove from metadata
        del self._metadata["textbooks"][textbook_id]
        self._save_metadata()
        return True

    # ─── Get available grades ───

    def get_available_grades(self) -> List[str]:
        """Return a sorted list of all grades that have textbooks."""
        grades = set()
        for info in self._metadata.get("textbooks", {}).values():
            grades.add(info["grade"])
        return sorted(grades, key=lambda g: int(g) if g.isdigit() else 0)

    # ─── Get units for a grade ───

    def get_units_for_grade(self, grade: str) -> List[str]:
        """Return all detected units for a given grade."""
        units = []
        for info in self._metadata.get("textbooks", {}).values():
            if info["grade"] == grade:
                units.extend(info.get("units", []))
        return sorted(set(units))


# ─── Singleton instance ───
_store_instance: Optional[VectorStore] = None


def get_vector_store() -> VectorStore:
    """Get or create the singleton VectorStore instance."""
    global _store_instance
    if _store_instance is None:
        _store_instance = VectorStore()
    return _store_instance
