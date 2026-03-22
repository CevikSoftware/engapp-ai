"""
FastAPI router for Textbook management — upload, list, delete, search.
"""

import os
import traceback
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from typing import Optional

from .schemas import (
    UploadTextbookResponse,
    ListTextbooksResponse,
    TextbookInfo,
    DeleteTextbookResponse,
    RAGSearchRequest,
    RAGSearchResponse,
    RAGChunk,
    GRADE_LABELS,
)
from .pdf_processor import process_pdf
from .vector_store import get_vector_store
from .rag_service import get_rag_service


router = APIRouter(
    prefix="/textbook",
    tags=["Textbook / RAG"],
    responses={500: {"description": "Internal server error"}},
)


# ─── Upload ───

@router.post("/upload", response_model=UploadTextbookResponse)
async def upload_textbook(
    file: UploadFile = File(..., description="PDF file of the textbook"),
    grade: str = Form(..., description="Grade level (e.g., '5', '9')"),
):
    """
    Upload a textbook PDF, process it, and add to the vector store.
    The PDF will be chunked by units and stored with grade-level metadata.
    """
    # Validate grade
    if grade not in GRADE_LABELS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid grade '{grade}'. Must be one of: {list(GRADE_LABELS.keys())}",
        )

    # Validate file type
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted.")

    # Read file
    try:
        pdf_bytes = await file.read()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read uploaded file: {e}")

    if len(pdf_bytes) < 100:
        raise HTTPException(status_code=400, detail="File is too small or empty.")

    # Process PDF
    try:
        chunks, unit_labels = process_pdf(
            pdf_bytes=pdf_bytes,
            grade=grade,
            filename=file.filename,
            max_chunk_size=800,
            overlap=100,
        )
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"PDF processing failed: {e}")

    if not chunks:
        raise HTTPException(
            status_code=400,
            detail="No text could be extracted from this PDF. It may be image-based or empty.",
        )

    # Store in vector DB
    try:
        store = get_vector_store()
        textbook_id = store._generate_textbook_id(file.filename, grade)

        # Check if already exists — re-upload replaces
        if textbook_id in store._metadata.get("textbooks", {}):
            store.delete_textbook(textbook_id)

        num_added = store.add_chunks(
            chunks=chunks,
            textbook_id=textbook_id,
            filename=file.filename,
            grade=grade,
            units=unit_labels,
        )
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Vector store error: {e}")

    return UploadTextbookResponse(
        success=True,
        message=f"Textbook uploaded and processed: {num_added} chunks from {file.filename}",
        textbook_id=textbook_id,
        grade=grade,
        filename=file.filename,
        total_chunks=num_added,
        units_detected=unit_labels,
    )


# ─── List ───

@router.get("/list", response_model=ListTextbooksResponse)
async def list_textbooks():
    """List all uploaded textbooks in the vector store."""
    try:
        store = get_vector_store()
        books = store.list_textbooks()
        return ListTextbooksResponse(
            success=True,
            textbooks=[TextbookInfo(**b) for b in books],
            total=len(books),
        )
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to list textbooks: {e}")


# ─── Delete ───

@router.delete("/delete/{textbook_id}", response_model=DeleteTextbookResponse)
async def delete_textbook(textbook_id: str):
    """Delete a textbook and all its chunks from the vector store."""
    store = get_vector_store()
    ok = store.delete_textbook(textbook_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Textbook not found.")
    return DeleteTextbookResponse(success=True, message="Textbook deleted.")


# ─── Search ───

@router.post("/search", response_model=RAGSearchResponse)
async def search_textbook(req: RAGSearchRequest):
    """
    Semantic search across textbook content for a given grade.
    Returns the most relevant chunks.
    """
    rag = get_rag_service()
    results = rag.retrieve_context(
        query=req.query,
        grade=req.grade,
        unit=req.unit,
        top_k=req.top_k,
    )

    return RAGSearchResponse(
        success=True,
        query=req.query,
        grade=req.grade,
        results=[
            RAGChunk(
                text=r.text,
                grade=r.grade,
                unit=r.unit,
                page=r.page_start,
                score=r.score,
                textbook_filename=r.textbook_filename,
            )
            for r in results
        ],
        total_results=len(results),
    )


# ─── Available grades ───

@router.get("/grades")
async def get_available_grades():
    """Get all grades that have uploaded textbooks."""
    store = get_vector_store()
    grades = store.get_available_grades()
    return {"success": True, "grades": grades}


# ─── Units for a grade ───

@router.get("/units/{grade}")
async def get_units_for_grade(grade: str):
    """Get all detected units for a given grade."""
    store = get_vector_store()
    units = store.get_units_for_grade(grade)
    return {"success": True, "grade": grade, "units": units}
