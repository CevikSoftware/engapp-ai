"""
PDF Processor — Extracts text from PDF, detects units, and performs smart chunking.
Uses PyMuPDF (fitz) for high-quality text extraction.
"""

import re
import fitz  # PyMuPDF
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field


@dataclass
class TextChunk:
    """Represents a chunk of text from a textbook."""
    text: str
    grade: str
    unit: str
    page_start: int
    page_end: int
    chunk_index: int
    textbook_filename: str = ""

    def to_dict(self) -> dict:
        return {
            "text": self.text,
            "grade": self.grade,
            "unit": self.unit,
            "page_start": self.page_start,
            "page_end": self.page_end,
            "chunk_index": self.chunk_index,
            "textbook_filename": self.textbook_filename,
        }


# ────────── Unit Detection Patterns ──────────
# Turkish and English patterns for detecting unit/chapter boundaries in textbooks.
UNIT_PATTERNS = [
    # English patterns
    r"(?i)^[\s]*unit\s+(\d+)\b",
    r"(?i)^[\s]*chapter\s+(\d+)\b",
    r"(?i)^[\s]*module\s+(\d+)\b",
    r"(?i)^[\s]*lesson\s+(\d+)\b",
    r"(?i)^[\s]*theme\s+(\d+)\b",
    r"(?i)^[\s]*section\s+(\d+)\b",
    # Turkish patterns
    r"(?i)^[\s]*ünite\s+(\d+)\b",
    r"(?i)^[\s]*bölüm\s+(\d+)\b",
    r"(?i)^[\s]*konu\s+(\d+)\b",
    r"(?i)^[\s]*ders\s+(\d+)\b",
    # Numbered patterns — "1.", "2." etc. at the start of a bold/large line
    r"(?i)^[\s]*(\d{1,2})\.\s*(unit|chapter|module|ünite|bölüm|theme|lesson)\b",
]


def _detect_unit_from_line(line: str) -> Optional[str]:
    """Try to detect a unit label from a single line of text."""
    line_stripped = line.strip()
    if not line_stripped or len(line_stripped) > 200:
        return None

    for pattern in UNIT_PATTERNS:
        m = re.search(pattern, line_stripped)
        if m:
            # Build label from the matched line (keep first ~80 chars)
            clean = re.sub(r'\s+', ' ', line_stripped).strip()
            return clean[:100]
    return None


def extract_text_with_pages(pdf_bytes: bytes) -> List[Tuple[int, str]]:
    """
    Extract text from a PDF, returning a list of (page_number, page_text) tuples.
    Page numbers are 1-based.
    """
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    pages = []
    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text("text")
        if text and text.strip():
            pages.append((page_num + 1, text))
    doc.close()
    return pages


def detect_units(pages: List[Tuple[int, str]]) -> List[Dict]:
    """
    Detect unit boundaries from page texts.
    Returns a list of dicts: {"unit": label, "page_start": int, "page_end": int}
    """
    units = []
    for page_num, text in pages:
        lines = text.split("\n")
        # Check the first ~10 lines of each page for unit headers
        for line in lines[:15]:
            unit_label = _detect_unit_from_line(line)
            if unit_label:
                # Avoid duplicate detection on the same page
                if units and units[-1]["page_start"] == page_num:
                    continue
                units.append({
                    "unit": unit_label,
                    "page_start": page_num,
                    "page_end": page_num,  # will be updated
                })
                break  # one unit per page

    # Set page_end for each unit
    for i in range(len(units)):
        if i + 1 < len(units):
            units[i]["page_end"] = units[i + 1]["page_start"] - 1
        else:
            units[i]["page_end"] = pages[-1][0] if pages else units[i]["page_start"]

    return units


def _assign_unit_to_page(page_num: int, units: List[Dict]) -> str:
    """Determine which unit a page belongs to."""
    for u in reversed(units):
        if page_num >= u["page_start"]:
            return u["unit"]
    return "General"


def smart_chunk(
    pages: List[Tuple[int, str]],
    units: List[Dict],
    grade: str,
    filename: str,
    max_chunk_size: int = 800,
    overlap: int = 100,
) -> List[TextChunk]:
    """
    Split page texts into overlapping chunks, tagged by unit and grade.
    
    - Groups pages by unit.
    - Within each unit, concatenates text and splits into chunks of ~max_chunk_size words.
    - Adds `overlap` word overlap between consecutive chunks.
    """
    # Group pages by unit
    unit_pages: Dict[str, List[Tuple[int, str]]] = {}
    for page_num, text in pages:
        unit_label = _assign_unit_to_page(page_num, units) if units else "General"
        if unit_label not in unit_pages:
            unit_pages[unit_label] = []
        unit_pages[unit_label].append((page_num, text))

    chunks: List[TextChunk] = []
    chunk_idx = 0

    for unit_label, upages in unit_pages.items():
        # Concatenate all text in this unit
        combined_text = ""
        page_start = upages[0][0]
        page_end = upages[-1][0]

        for _, text in upages:
            combined_text += text + "\n"

        # Clean text
        combined_text = re.sub(r'\n{3,}', '\n\n', combined_text)
        combined_text = combined_text.strip()

        if not combined_text:
            continue

        # Split into word-based chunks with overlap
        words = combined_text.split()
        total_words = len(words)

        if total_words == 0:
            continue

        start = 0
        while start < total_words:
            end = min(start + max_chunk_size, total_words)
            chunk_words = words[start:end]
            chunk_text = " ".join(chunk_words)

            # Only add non-trivial chunks
            if len(chunk_text.strip()) > 50:
                chunks.append(TextChunk(
                    text=chunk_text,
                    grade=grade,
                    unit=unit_label,
                    page_start=page_start,
                    page_end=page_end,
                    chunk_index=chunk_idx,
                    textbook_filename=filename,
                ))
                chunk_idx += 1

            # Move forward by (max_chunk_size - overlap)
            start += max(max_chunk_size - overlap, 200)

    return chunks


def process_pdf(
    pdf_bytes: bytes,
    grade: str,
    filename: str,
    max_chunk_size: int = 800,
    overlap: int = 100,
) -> Tuple[List[TextChunk], List[str]]:
    """
    Full pipeline: extract text → detect units → smart chunk.
    Returns (chunks, unit_labels).
    """
    pages = extract_text_with_pages(pdf_bytes)
    if not pages:
        return [], []

    units = detect_units(pages)
    unit_labels = [u["unit"] for u in units]

    chunks = smart_chunk(
        pages=pages,
        units=units,
        grade=grade,
        filename=filename,
        max_chunk_size=max_chunk_size,
        overlap=overlap,
    )

    return chunks, unit_labels
