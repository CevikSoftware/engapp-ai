"""
Pydantic schemas for Textbook / RAG system.
"""

from typing import Optional, List
from pydantic import BaseModel, Field
from enum import Enum


class GradeLevel(str, Enum):
    """Turkish education grade levels for textbook classification."""
    GRADE_2 = "2"
    GRADE_3 = "3"
    GRADE_4 = "4"
    GRADE_5 = "5"
    GRADE_6 = "6"
    GRADE_7 = "7"
    GRADE_8 = "8"
    GRADE_9 = "9"
    GRADE_10 = "10"
    GRADE_11 = "11"
    GRADE_12 = "12"


GRADE_LABELS = {
    "2": "2. Sınıf",
    "3": "3. Sınıf",
    "4": "4. Sınıf",
    "5": "5. Sınıf",
    "6": "6. Sınıf",
    "7": "7. Sınıf",
    "8": "8. Sınıf",
    "9": "9. Sınıf (Lise 1)",
    "10": "10. Sınıf (Lise 2)",
    "11": "11. Sınıf (Lise 3)",
    "12": "12. Sınıf (Lise 4)",
}


# ─── Upload / Management ───

class UploadTextbookResponse(BaseModel):
    """Response after uploading a textbook PDF."""
    success: bool
    message: str
    textbook_id: str = ""
    grade: str = ""
    filename: str = ""
    total_chunks: int = 0
    units_detected: List[str] = Field(default_factory=list)


class TextbookInfo(BaseModel):
    """Information about a stored textbook."""
    textbook_id: str
    filename: str
    grade: str
    total_chunks: int
    units: List[str] = Field(default_factory=list)
    uploaded_at: str = ""


class ListTextbooksResponse(BaseModel):
    """Response listing all uploaded textbooks."""
    success: bool
    textbooks: List[TextbookInfo] = Field(default_factory=list)
    total: int = 0


class DeleteTextbookResponse(BaseModel):
    """Response after deleting a textbook."""
    success: bool
    message: str


# ─── RAG / Search ───

class RAGSearchRequest(BaseModel):
    """Request to search textbook content."""
    query: str = Field(..., description="Search query text")
    grade: str = Field(..., description="Grade level to search in")
    unit: Optional[str] = Field(None, description="Optional: specific unit to search in")
    top_k: int = Field(5, description="Number of results to return", ge=1, le=20)


class RAGChunk(BaseModel):
    """A single retrieved chunk from the vector store."""
    text: str
    grade: str
    unit: str
    page: int = 0
    score: float = 0.0
    textbook_filename: str = ""


class RAGSearchResponse(BaseModel):
    """Response from a RAG search."""
    success: bool
    query: str
    grade: str
    results: List[RAGChunk] = Field(default_factory=list)
    total_results: int = 0
