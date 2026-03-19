"""
FastAPI router for Speaking Practice endpoints.
Word pronunciation and phonetics API.
"""

from fastapi import APIRouter, HTTPException
from typing import Optional

from .schemas import (
    WordPronunciationRequest,
    WordPronunciationResponse,
    WordPronunciationItem,
    ErrorResponse,
    AvailableVoicesResponse
)
from .word_service import WordPronunciationService, CEFR_SPEECH_SPEED

router = APIRouter(
    prefix="/speaking",
    tags=["Speaking Practice"],
    responses={
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)

# Global TTS service instance (lazy loaded)
_tts_service: Optional[WordPronunciationService] = None


def get_tts_service() -> WordPronunciationService:
    """Get or create the TTS service instance."""
    global _tts_service
    if _tts_service is None:
        try:
            _tts_service = WordPronunciationService()
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to initialize TTS service: {str(e)}"
            )
    return _tts_service


@router.post(
    "/word-pronunciation",
    response_model=WordPronunciationResponse,
    summary="Get Word Pronunciations with Audio",
    description="""
Generate audio pronunciation and phonetic information for a list of words.

Returns JSON with:
- **IPA phonetic transcription** for each word
- **Simplified phonetic** representation for learners
- **Base64 encoded WAV audio** for each word
- **Syllable count** and **stress pattern**
- **Example sentence** appropriate for the CEFR level
- **Usage note** appropriate for the CEFR level

**Parameters:**
- `words`: List of words (1-50 words)
- `difficulty`: CEFR level - A1, A2, A1-A2, B1, B2, A2-B1, B1-B2, C1, C2, B2-C1, C1-C2 (default: B1). Affects example sentence complexity, usage notes, and auto speech speed.
- `voice_id`: Voice to use (default: female_1). See /voices endpoint for options.
- `speech_speed`: Speed multiplier (0.5=fast, 1.0=normal, 2.0=slow). If not set, auto-adjusted based on CEFR level (slower for A1/A2, faster for C1/C2).

**Example Request:**
```json
{
    "words": ["hello", "world", "pronunciation"],
    "difficulty": "B1",
    "voice_id": "female_1"
}
```
"""
)
async def get_word_pronunciations(request: WordPronunciationRequest):
    """
    Get pronunciation audio and phonetics for a list of words.
    """
    try:
        tts_service = get_tts_service()
        
        # Determine CEFR level
        difficulty = request.difficulty.value if request.difficulty else "B1"
        
        # Auto-adjust speech speed based on CEFR level if not explicitly set
        speech_speed = request.speech_speed
        if speech_speed is None:
            speech_speed = CEFR_SPEECH_SPEED.get(difficulty, 1.0)
        
        # Process the word list
        results = tts_service.process_word_list(
            words=request.words,
            voice_id=request.voice_id or "female_1",
            speech_speed=speech_speed,
            difficulty=difficulty
        )
        
        # Convert to response format
        word_items = [
            WordPronunciationItem(
                word=r.word,
                phonetic_ipa=r.phonetic_ipa,
                phonetic_simple=r.phonetic_simple,
                audio_base64=r.audio_base64,
                syllable_count=r.syllable_count,
                stress_pattern=r.stress_pattern,
                example_sentence=r.example_sentence or None,
                usage_note=r.usage_note or None,
                cefr_level=r.cefr_level
            )
            for r in results
        ]
        
        return WordPronunciationResponse(
            success=True,
            total_words=len(word_items),
            voice_id=request.voice_id or "female_1",
            words=word_items
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating pronunciations: {str(e)}"
        )


@router.get(
    "/voices",
    response_model=AvailableVoicesResponse,
    summary="Get Available Voices",
    description="""
Get a list of all available voices for word pronunciation.

Voices are organized by gender (male/female) and each has:
- `voice_id`: Unique identifier to use in requests
- `name`: Human-friendly name
- `description`: Voice characteristics
- `speaker_id`: Internal speaker ID
"""
)
async def get_available_voices():
    """
    Get all available voice options for pronunciation generation.
    """
    try:
        voices = WordPronunciationService.get_available_voices()
        return AvailableVoicesResponse(
            male=voices["male"],
            female=voices["female"]
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting voices: {str(e)}"
        )


@router.get(
    "/health",
    summary="Speaking Service Health Check",
    description="Check if the speaking practice TTS service is operational."
)
async def speaking_health_check():
    """
    Check the health of the speaking practice service.
    """
    try:
        tts_service = get_tts_service()
        return {
            "status": "healthy",
            "service": "speaking",
            "tts_loaded": tts_service.voice is not None
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "speaking",
            "error": str(e)
        }
