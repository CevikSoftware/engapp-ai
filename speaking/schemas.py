"""
Pydantic schemas for Speaking Practice API endpoints.
"""

from typing import List, Optional
from pydantic import BaseModel, Field
from enum import Enum

from cefr_config import CEFRLevel


class VoiceGender(str, Enum):
    """Voice gender options."""
    MALE = "male"
    FEMALE = "female"


class WordPronunciationRequest(BaseModel):
    """Request model for word pronunciation generation."""
    words: List[str] = Field(
        ...,
        description="List of words to get pronunciation and phonetics for",
        min_length=1,
        max_length=50,
        examples=[["hello", "world", "pronunciation"]]
    )
    difficulty: Optional[CEFRLevel] = Field(
        default=CEFRLevel.B1,
        description="CEFR difficulty level. Affects example sentences, usage notes, and speech speed recommendation. A1-C2."
    )
    voice_id: Optional[str] = Field(
        default="female_1",
        description="Voice ID to use for audio generation (e.g., 'male_1', 'female_3')"
    )
    speech_speed: Optional[float] = Field(
        default=None,
        ge=0.5,
        le=2.0,
        description="Speech speed: 0.5=fast, 1.0=normal, 2.0=slow. If not set, auto-adjusted based on CEFR level."
    )


class WordPronunciationItem(BaseModel):
    """Single word pronunciation result."""
    word: str = Field(..., description="The original word")
    phonetic_ipa: str = Field(..., description="IPA phonetic transcription")
    phonetic_simple: str = Field(..., description="Simplified phonetic representation")
    audio_base64: str = Field(..., description="Base64 encoded WAV audio data")
    syllable_count: int = Field(..., description="Number of syllables in the word")
    stress_pattern: Optional[str] = Field(None, description="Stress pattern of the word")
    example_sentence: Optional[str] = Field(None, description="Example sentence using the word, appropriate for the CEFR level")
    usage_note: Optional[str] = Field(None, description="Brief usage note appropriate for the CEFR level")
    cefr_level: Optional[str] = Field(None, description="CEFR difficulty level used")


class WordPronunciationResponse(BaseModel):
    """Response model for word pronunciation generation."""
    success: bool = Field(..., description="Whether the request was successful")
    total_words: int = Field(..., description="Total number of words processed")
    voice_id: str = Field(..., description="Voice ID used for generation")
    words: List[WordPronunciationItem] = Field(..., description="Pronunciation data for each word")


class ErrorResponse(BaseModel):
    """Error response model."""
    success: bool = Field(default=False, description="Always false for errors")
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")


class AvailableVoicesResponse(BaseModel):
    """Response model for available voices."""
    male: List[dict] = Field(..., description="List of available male voices")
    female: List[dict] = Field(..., description="List of available female voices")
