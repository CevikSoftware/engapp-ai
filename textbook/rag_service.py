"""
RAG Service — Retrieves relevant textbook context for content generation.
Used by all modules (Listening, Reading, Writing, Practice) to enrich
AI-generated content with textbook material.
"""

from typing import Optional, List
from .vector_store import get_vector_store, SearchResult


class RAGService:
    """
    Retrieval-Augmented Generation service.
    Queries the vector store and formats results for LLM prompt injection.
    """

    def __init__(self):
        self.store = get_vector_store()

    def retrieve_context(
        self,
        query: str,
        grade: str,
        unit: Optional[str] = None,
        top_k: int = 5,
    ) -> List[SearchResult]:
        """
        Retrieve relevant textbook chunks for a given query and grade.
        """
        if not grade:
            return []

        return self.store.search(
            query=query,
            grade=grade,
            unit=unit,
            top_k=top_k,
        )

    def build_context_prompt(
        self,
        query: str,
        grade: str,
        unit: Optional[str] = None,
        top_k: int = 5,
    ) -> str:
        """
        Retrieve textbook chunks and format them as an LLM-ready context block.
        Returns an empty string if no textbooks match the grade or query.
        """
        results = self.retrieve_context(
            query=query,
            grade=grade,
            unit=unit,
            top_k=top_k,
        )

        if not results:
            return ""

        # Filter low-relevance results (score < 0.35)
        results = [r for r in results if r.score >= 0.35]
        if not results:
            return ""

        context_parts = []
        for i, r in enumerate(results, 1):
            # Truncate very long chunks
            text = r.text[:1500] if len(r.text) > 1500 else r.text
            context_parts.append(
                f"[Textbook Excerpt {i} — {r.textbook_filename}, "
                f"Grade {r.grade}, {r.unit}, Pages {r.page_start}-{r.page_end}]\n"
                f"{text}"
            )

        context_block = "\n\n".join(context_parts)

        return f"""
📚 TEXTBOOK REFERENCE MATERIAL (Grade {grade}):
The following excerpts come from the student's actual textbook. You MUST use this content
as the primary source for topics, vocabulary, grammar, and context in your generated content.
Align your output with the textbook's themes, vocabulary level, and teaching approach.

{context_block}

⚠️ IMPORTANT: Base your content on the textbook material above. Use similar vocabulary,
topics, and difficulty level. The student is studying from this textbook, so the generated
content should feel like a natural extension of their coursework.
"""


# ─── Singleton ───
_rag_instance: Optional[RAGService] = None


def get_rag_service() -> RAGService:
    """Get or create the singleton RAGService."""
    global _rag_instance
    if _rag_instance is None:
        _rag_instance = RAGService()
    return _rag_instance
