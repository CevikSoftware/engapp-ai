"""
FastAPI router for Writing Practice endpoints.
Writing task generation and analysis API.
"""

import os
from fastapi import APIRouter, HTTPException
from typing import Optional

from .schemas import (
    GenerateTaskRequest,
    GenerateTaskResponse,
    GeneratedTask,
    AnalyzeWritingRequest,
    AnalyzeWritingResponse,
    AnalysisResult,
    ErrorDetail,
    Scores,
    ErrorResponse
)
from .task_generator import WritingTaskGenerator
from .writing_analyzer import WritingAnalyzer

# RAG service for textbook context
def _get_rag_context(query: str, grade: str) -> str:
    """Retrieve textbook RAG context if grade is provided."""
    if not grade:
        return ""
    try:
        from textbook.rag_service import get_rag_service
        rag = get_rag_service()
        return rag.build_context_prompt(query=query, grade=grade)
    except Exception:
        return ""

router = APIRouter(
    prefix="/writing",
    tags=["Writing Practice"],
    responses={
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)


def get_task_generator() -> WritingTaskGenerator:
    """Get a WritingTaskGenerator instance."""
    api_key = os.getenv("TOGETHER_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="TOGETHER_API_KEY environment variable is not set"
        )
    return WritingTaskGenerator(api_key=api_key)


def get_analyzer() -> WritingAnalyzer:
    """Get a WritingAnalyzer instance."""
    api_key = os.getenv("TOGETHER_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="TOGETHER_API_KEY environment variable is not set"
        )
    return WritingAnalyzer(api_key=api_key)


@router.post(
    "/generate-task",
    response_model=GenerateTaskResponse,
    summary="Generate a Writing Task",
    description="""
Generate a writing task based on a given topic.

**Parameters:**
- `topic`: The main topic or subject for the writing task (required)
- `writing_type`: Type of writing - email, essay, letter, report, story, etc. (optional)
- `target_tense`: Tense to practice - past_simple, present_perfect, future_simple, etc. (optional)
- `target_vocabulary`: List of words that should be used in the writing (optional)
- `additional_details`: Any extra instructions or context (optional)
- `difficulty`: CEFR level - A1, A2, A1-A2, B1, B2, A2-B1, B1-B2, C1, C2, B2-C1, C1-C2 (default: B1)

**Example Request:**
```json
{
    "topic": "Job application for a software developer position at a tech company",
    "writing_type": "email",
    "target_tense": "present_perfect",
    "target_vocabulary": ["experience", "skills", "qualification", "contribute"],
    "additional_details": "The company is Google and the position requires Python experience",
    "difficulty": "B1"
}
```
"""
)
async def generate_writing_task(request: GenerateTaskRequest):
    """Generate a writing task based on the given topic and requirements."""
    try:
        generator = get_task_generator()
        
        task = generator.generate_task(
            topic=request.topic,
            writing_type=request.writing_type.value if request.writing_type else None,
            target_tense=request.target_tense.value if request.target_tense else None,
            target_vocabulary=request.target_vocabulary,
            target_grammar=request.target_grammar,
            additional_details=request.additional_details,
            difficulty=request.difficulty.value if request.difficulty else "B1",
            rag_context=_get_rag_context(request.topic, getattr(request, 'textbook_grade', None))
        )
        
        return GenerateTaskResponse(
            success=True,
            task=GeneratedTask(
                task_instruction=task.task_instruction,
                topic=task.topic,
                writing_type=task.writing_type,
                target_tense=task.target_tense,
                target_vocabulary=task.target_vocabulary,
                target_grammar=task.target_grammar,
                additional_details=task.additional_details,
                tips=task.tips,
                suggested_word_count=task.suggested_word_count
            )
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating task: {str(e)}"
        )


@router.post(
    "/analyze",
    response_model=AnalyzeWritingResponse,
    summary="Analyze Writing Response",
    description="""
Analyze a user's written response and provide detailed feedback.

**Parameters:**
- `task_instruction`: The original writing task (required)
- `user_response`: The user's written text to analyze (required)
- `target_tense`: Expected tense (optional)
- `target_vocabulary`: Words that should have been used (optional)
- `additional_details`: Additional context (optional)
- `difficulty`: CEFR evaluation level - A1 (very lenient) to C2 (very strict) (optional, default: B1)
- `tips`: Tips given to the user - AI will check if they were followed (optional)

**Response includes:**
- List of errors with:
  - Original sentence with [wrong]error[wrong] markers around ONLY the erroneous part
  - Corrected sentence with [correct]fix[correct] markers around ONLY the corrected part
  - Error type (grammar, vocabulary, style, punctuation, spelling, word_order, tense, article, preposition)
  - Explanation note in English
- Scores (0-100) adjusted by CEFR level for: grammar, fluency, vocabulary, structure, task_completion, overall
- 1-5 strengths
- 1-5 areas for improvement
- Feedback on tips (if provided)

**Example Request:**
```json
{
    "task_instruction": "Write an email applying for a software developer position at Google.",
    "user_response": "Dear Sir, I am writing to apply for the software developer position. I have work at my company for 5 years. I am very experience in Python...",
    "target_tense": "present_perfect",
    "target_vocabulary": ["experience", "skills", "contribute"],
    "difficulty": "B1",
    "tips": ["Use formal language", "Mention your qualifications", "Express enthusiasm for the role"]
}
```

**Example Error in Response:**
```json
{
    "original_sentence": "I have [wrong]work[wrong] at my company for 5 years.",
    "corrected_sentence": "I have [correct]worked[correct] at my company for 5 years.",
    "error_type": "grammar",
    "note": "Present perfect tense requires the past participle form. 'Work' should be 'worked'."
}
```
"""
)
async def analyze_writing(request: AnalyzeWritingRequest):
    """Analyze a user's writing and provide detailed feedback."""
    try:
        analyzer = get_analyzer()
        
        result = analyzer.analyze(
            task_instruction=request.task_instruction,
            user_response=request.user_response,
            target_tense=request.target_tense.value if request.target_tense else None,
            target_vocabulary=request.target_vocabulary,
            target_grammar=request.target_grammar,
            additional_details=request.additional_details,
            difficulty=request.difficulty.value if request.difficulty else "B1",
            tips=request.tips,
            rag_context=_get_rag_context(request.task_instruction, getattr(request, 'textbook_grade', None))
        )
        
        # Convert dataclasses to Pydantic models
        error_details = [
            ErrorDetail(
                original_sentence=err.original_sentence,
                corrected_sentence=err.corrected_sentence,
                error_type=err.error_type,
                note=err.note
            )
            for err in result.errors
        ]
        
        scores = Scores(
            grammar=result.scores.grammar,
            fluency=result.scores.fluency,
            vocabulary=result.scores.vocabulary,
            structure=result.scores.structure,
            task_completion=result.scores.task_completion,
            overall=result.scores.overall
        )
        
        # Process tips_feedback - convert dict format to string format if needed
        processed_tips_feedback = None
        if result.tips_feedback:
            processed_tips_feedback = []
            for tip_item in result.tips_feedback:
                if isinstance(tip_item, dict):
                    # Convert dict to string: "Tip: status - feedback"
                    tip_text = tip_item.get('tip', '')
                    status = tip_item.get('status', '')
                    feedback = tip_item.get('feedback', '')
                    processed_tips_feedback.append(f"{tip_text}: {status} - {feedback}")
                elif isinstance(tip_item, str):
                    processed_tips_feedback.append(tip_item)
        
        analysis = AnalysisResult(
            errors=error_details,
            scores=scores,
            strengths=result.strengths,
            areas_for_improvement=result.areas_for_improvement,
            tips_feedback=processed_tips_feedback
        )
        
        # Count words
        word_count = len(request.user_response.split())
        
        return AnalyzeWritingResponse(
            success=True,
            task_instruction=request.task_instruction,
            user_response=request.user_response,
            word_count=word_count,
            analysis=analysis
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error analyzing writing: {str(e)}"
        )


@router.get(
    "/health",
    summary="Writing Service Health Check",
    description="Check if the writing practice service is operational."
)
async def writing_health_check():
    """Check the health of the writing practice service."""
    together_api_configured = bool(os.getenv("TOGETHER_API_KEY"))
    
    return {
        "status": "healthy" if together_api_configured else "degraded",
        "service": "writing",
        "together_api": "configured" if together_api_configured else "not_configured"
    }
