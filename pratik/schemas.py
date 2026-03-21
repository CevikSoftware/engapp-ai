"""
Pydantic schemas for Practice (Pratik) API endpoints.
Simplified for fast, async conversation handling.
"""

from typing import Optional, List, Literal
from pydantic import BaseModel, Field

from cefr_config import CEFRLevel


# ============== API 1: Start Conversation ==============

class StartConversationRequest(BaseModel):
    """Request model for starting a new conversation."""
    
    partner_name: str = Field(
        ...,
        description="Name of the conversation partner (AI's name)",
        example="Sarah",
        min_length=1,
        max_length=50
    )
    llm_role: str = Field(
        ...,
        description="The role/persona of the AI (e.g., 'friendly coffee shop barista', 'job interviewer at tech company')",
        example="friendly coffee shop barista",
        min_length=5,
        max_length=300
    )
    total_steps: int = Field(
        ...,
        description="Approximate number of conversation turns",
        ge=3,
        le=30,
        example=8
    )
    topic: Optional[str] = Field(
        None,
        description="Optional conversation topic",
        example="ordering coffee",
        max_length=200
    )
    details: Optional[str] = Field(
        None,
        description="Optional additional details/context for the conversation",
        example="Focus on polite expressions and asking about menu items",
        max_length=500
    )
    vocabulary: Optional[List[str]] = Field(
        None,
        description="Optional list of vocabulary words to practice",
        example=["latte", "espresso", "pastry"],
        max_items=20
    )
    target_grammar: Optional[List[str]] = Field(
        None,
        description="Optional target grammar structures to practice in conversation",
        example=["Present Perfect", "Would like", "Comparatives"],
        max_items=10
    )
    # Difficulty settings
    difficulty: CEFRLevel = Field(
        CEFRLevel.B1,
        description="CEFR difficulty level. A1/A2: simple words, short sentences. B1/B2: natural flow. C1/C2: complex vocabulary, idioms."
    )
    # Voice settings
    voice_gender: Optional[Literal["male", "female"]] = Field(
        "female",
        description="Gender of the AI voice (male/female)"
    )
    voice_id: Optional[str] = Field(
        None,
        description="Specific voice ID (e.g., 'female_1', 'male_2'). Overrides voice_gender if provided."
    )
    speech_rate: float = Field(
        1.0,
        description="Speech rate/speed. 0.75 = slow (good for beginners), 1.0 = normal, 1.25 = fast. Range: 0.5-1.5",
        ge=0.5,
        le=1.5
    )
    enable_tts: bool = Field(
        True,
        description="Enable text-to-speech audio output"
    )
    textbook_grade: Optional[str] = Field(
        None,
        description="Grade level for textbook RAG context (e.g., '5', '9'). Retrieves relevant textbook content to enrich the conversation.",
        example="5"
    )


class StartConversationResponse(BaseModel):
    """Response model for starting a conversation."""
    
    session_id: str = Field(..., description="Unique session ID for this conversation")
    opening_message: str = Field(..., description="AI's opening message to start the conversation")
    partner_name: str = Field(..., description="Name of the conversation partner")
    total_steps: int = Field(..., description="Total conversation steps")
    audio_base64: Optional[str] = Field(None, description="Base64 encoded WAV audio of the opening message")
    voice_id: str = Field(..., description="Voice ID being used for this conversation")


# ============== API 2: Chat ==============

class ChatRequest(BaseModel):
    """Request model for chat - send user's response."""
    
    session_id: str = Field(
        ...,
        description="The session ID from start conversation"
    )
    user_message: str = Field(
        ...,
        description="User's response message",
        min_length=1,
        max_length=2000
    )


class ChatResponse(BaseModel):
    """Response model for chat."""
    
    session_id: str = Field(..., description="The session ID")
    ai_message: str = Field(..., description="AI's response message")
    current_step: int = Field(..., description="Current conversation step")
    total_steps: int = Field(..., description="Total conversation steps")
    remaining_steps: int = Field(..., description="Remaining conversation steps")
    is_done: bool = Field(default=False, description="Whether the conversation has ended")
    audio_base64: Optional[str] = Field(None, description="Base64 encoded WAV audio of the AI message")


# ============== Error Response ==============

class ErrorResponse(BaseModel):
    """Standard error response."""
    
    error: str = Field(..., description="Error type")
    detail: str = Field(..., description="Detailed error message")
