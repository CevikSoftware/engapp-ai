"""
Pydantic schemas for Writing Practice API endpoints.
"""

from typing import List, Optional
from pydantic import BaseModel, Field
from enum import Enum

from cefr_config import CEFRLevel as DifficultyLevel


class TenseType(str, Enum):
    """Tense types for writing tasks."""
    PAST_SIMPLE = "past_simple"
    PAST_CONTINUOUS = "past_continuous"
    PAST_PERFECT = "past_perfect"
    PRESENT_SIMPLE = "present_simple"
    PRESENT_CONTINUOUS = "present_continuous"
    PRESENT_PERFECT = "present_perfect"
    FUTURE_SIMPLE = "future_simple"
    FUTURE_CONTINUOUS = "future_continuous"
    CONDITIONAL = "conditional"
    MIXED = "mixed"


class WritingType(str, Enum):
    """Types of writing tasks."""
    EMAIL = "email"
    ESSAY = "essay"
    LETTER = "letter"
    REPORT = "report"
    STORY = "story"
    REVIEW = "review"
    ARTICLE = "article"
    DESCRIPTION = "description"


class ErrorType(str, Enum):
    """Types of errors in writing."""
    GRAMMAR = "grammar"
    VOCABULARY = "vocabulary"
    STYLE = "style"
    PUNCTUATION = "punctuation"
    SPELLING = "spelling"
    WORD_ORDER = "word_order"
    TENSE = "tense"
    ARTICLE = "article"
    PREPOSITION = "preposition"


# ==================== Task Generation ====================

class GenerateTaskRequest(BaseModel):
    """Request model for generating a writing task."""
    topic: str = Field(
        ...,
        description="The topic or subject for the writing task",
        min_length=3,
        max_length=500,
        examples=["Job application for a software developer position at a tech company"]
    )
    writing_type: Optional[WritingType] = Field(
        default=None,
        description="Type of writing (email, essay, letter, etc.)"
    )
    target_tense: Optional[TenseType] = Field(
        default=None,
        description="Target tense to use in the writing"
    )
    target_vocabulary: Optional[List[str]] = Field(
        default=None,
        description="List of vocabulary words that should be used",
        max_length=20
    )
    target_grammar: Optional[List[str]] = Field(
        default=None,
        description="List of grammar structures to practice (e.g., Passive Voice, Reported Speech, Conditionals)",
        max_length=10
    )
    additional_details: Optional[str] = Field(
        default=None,
        description="Additional instructions or details for the task",
        max_length=1000
    )
    difficulty: Optional[DifficultyLevel] = Field(
        default=DifficultyLevel.B1,
        description="CEFR difficulty level (A1, A2, A1-A2, B1, B2, A2-B1, B1-B2, C1, C2, B2-C1, C1-C2)"
    )
    textbook_grade: Optional[str] = Field(
        default=None,
        description="Grade level for textbook RAG context (e.g., '5', '9')."
    )


class GeneratedTask(BaseModel):
    """Generated writing task."""
    task_instruction: str = Field(..., description="The writing task instruction in English")
    topic: str = Field(..., description="Original topic")
    writing_type: Optional[str] = Field(None, description="Type of writing")
    target_tense: Optional[str] = Field(None, description="Target tense to practice")
    target_vocabulary: Optional[List[str]] = Field(None, description="Vocabulary to include")
    target_grammar: Optional[List[str]] = Field(None, description="Grammar structures to practice")
    additional_details: Optional[str] = Field(None, description="Additional details")
    tips: List[str] = Field(default=[], description="Tips for completing the task")
    suggested_word_count: int = Field(..., description="Suggested word count")


class GenerateTaskResponse(BaseModel):
    """Response model for task generation."""
    success: bool = Field(..., description="Whether the request was successful")
    task: GeneratedTask = Field(..., description="The generated writing task")


# ==================== Writing Analysis ====================

class AnalyzeWritingRequest(BaseModel):
    """Request model for analyzing a piece of writing."""
    task_instruction: str = Field(
        ...,
        description="The original writing task/instruction",
        min_length=10,
        max_length=1000
    )
    user_response: str = Field(
        ...,
        description="The user's written response to analyze",
        min_length=20,
        max_length=10000
    )
    target_tense: Optional[TenseType] = Field(
        default=None,
        description="Target tense that should have been used"
    )
    target_vocabulary: Optional[List[str]] = Field(
        default=None,
        description="Vocabulary words that should have been included"
    )
    target_grammar: Optional[List[str]] = Field(
        default=None,
        description="Grammar structures that should have been used",
        max_length=10
    )
    additional_details: Optional[str] = Field(
        default=None,
        description="Additional context or requirements"
    )
    difficulty: Optional[DifficultyLevel] = Field(
        default=DifficultyLevel.B1,
        description="CEFR difficulty level for evaluation strictness"
    )
    tips: Optional[List[str]] = Field(
        default=None,
        description="Tips that were given to the user - AI will check if they were followed",
        max_length=10
    )
    textbook_grade: Optional[str] = Field(
        default=None,
        description="Grade level for textbook RAG context."
    )


class ErrorDetail(BaseModel):
    """Details about a single error found in the writing."""
    original_sentence: str = Field(
        ..., 
        description="The original sentence with error marked as [wrong]word[wrong]"
    )
    corrected_sentence: str = Field(
        ..., 
        description="The corrected sentence with fix marked as [correct]word[correct]"
    )
    error_type: ErrorType = Field(..., description="Type of error (grammar, vocabulary, style, etc.)")
    note: str = Field(..., description="Explanation of why it was wrong (in English)")


class Scores(BaseModel):
    """Scores for different aspects of the writing."""
    grammar: int = Field(..., ge=0, le=100, description="Grammar score (0-100)")
    fluency: int = Field(..., ge=0, le=100, description="Fluency score (0-100)")
    vocabulary: int = Field(..., ge=0, le=100, description="Vocabulary richness score (0-100)")
    structure: int = Field(..., ge=0, le=100, description="Structure/Organization score (0-100)")
    task_completion: int = Field(..., ge=0, le=100, description="How well the task was completed (0-100)")
    overall: int = Field(..., ge=0, le=100, description="Overall score (0-100)")


class AnalysisResult(BaseModel):
    """Complete analysis result."""
    errors: List[ErrorDetail] = Field(default=[], description="List of errors found")
    scores: Scores = Field(..., description="Scores for different aspects")
    strengths: List[str] = Field(..., description="Strong points of the writing (1-5 items)")
    areas_for_improvement: List[str] = Field(..., description="Areas that need improvement (1-5 items)")
    tips_feedback: Optional[List[str]] = Field(None, description="Feedback on whether tips were followed")


class AnalyzeWritingResponse(BaseModel):
    """Response model for writing analysis."""
    success: bool = Field(..., description="Whether the analysis was successful")
    task_instruction: str = Field(..., description="The original task instruction")
    user_response: str = Field(..., description="The user's response")
    word_count: int = Field(..., description="Word count of the user's response")
    analysis: AnalysisResult = Field(..., description="Detailed analysis results")


class ErrorResponse(BaseModel):
    """Error response model."""
    success: bool = Field(default=False, description="Always false for errors")
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")
