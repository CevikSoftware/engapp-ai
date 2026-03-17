"""
Pydantic schemas for Listening API endpoints.
"""

from typing import Optional, List
from pydantic import BaseModel, Field
from enum import Enum

from cefr_config import CEFRLevel as DifficultyLevel


class ConversationLength(str, Enum):
    SHORT = "short"
    MEDIUM = "medium"
    LONG = "long"


class Gender(str, Enum):
    MALE = "male"
    FEMALE = "female"


class ConversationRequest(BaseModel):
    """Request model for generating a conversation."""
    
    topic: str = Field(
        ...,
        description="The topic of the conversation",
        example="Ordering food at a restaurant"
    )
    difficulty: DifficultyLevel = Field(
        ...,
        description="The difficulty level of the conversation"
    )
    length: ConversationLength = Field(
        ...,
        description="The approximate length of the conversation"
    )
    character1: str = Field(
        ...,
        description="Name of the first character (starts the conversation)",
        example="Sarah"
    )
    character2: str = Field(
        ...,
        description="Name of the second character",
        example="John"
    )
    gender1: Gender = Field(
        ...,
        description="Gender of the first character (for voice selection)",
        example="female"
    )
    gender2: Gender = Field(
        ...,
        description="Gender of the second character (for voice selection)",
        example="male"
    )
    special_details: Optional[str] = Field(
        None,
        description="Optional specific details or points to include in the conversation",
        example="Include asking about vegetarian options and making a reservation"
    )
    target_vocabulary: Optional[List[str]] = Field(
        None,
        description="Optional target vocabulary words to use naturally in the conversation",
        max_length=20,
        example=["reservation", "appetizer", "vegetarian", "recommend"]
    )
    target_grammar: Optional[List[str]] = Field(
        None,
        description="Optional target grammar structures to practice in the conversation",
        max_length=10,
        example=["Present Perfect", "First Conditional"]
    )
    textbook_grade: Optional[str] = Field(
        None,
        description="Grade level for textbook RAG context (e.g., '5', '9'). If set, retrieves relevant textbook content to enrich the conversation.",
        example="5"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "topic": "Ordering food at a restaurant",
                "difficulty": "B1",
                "length": "medium",
                "character1": "Sarah",
                "character2": "John",
                "gender1": "female",
                "gender2": "male",
                "special_details": "Include asking about vegetarian options",
                "target_vocabulary": ["reservation", "appetizer", "vegetarian"],
                "target_grammar": ["Present Perfect", "Would like"],
                "textbook_grade": "5"
            }
        }


class ConversationWithAudioRequest(BaseModel):
    """Request model for generating a conversation with audio files."""
    
    topic: str = Field(
        ...,
        description="The topic of the conversation",
        example="Ordering food at a restaurant"
    )
    difficulty: DifficultyLevel = Field(
        ...,
        description="The difficulty level of the conversation"
    )
    length: ConversationLength = Field(
        ...,
        description="The approximate length of the conversation"
    )
    character1: str = Field(
        ...,
        description="Name of the first character (starts the conversation)",
        example="Sarah"
    )
    character2: str = Field(
        ...,
        description="Name of the second character",
        example="John"
    )
    gender1: Gender = Field(
        ...,
        description="Gender of the first character (for voice selection)",
        example="female"
    )
    gender2: Gender = Field(
        ...,
        description="Gender of the second character (for voice selection)",
        example="male"
    )
    voice_id1: Optional[str] = Field(
        None,
        description="Optional specific voice ID for character1 (e.g., 'female_1', 'male_3'). Use /voices endpoint to see available options.",
        example="female_1"
    )
    voice_id2: Optional[str] = Field(
        None,
        description="Optional specific voice ID for character2 (e.g., 'female_2', 'male_1'). Use /voices endpoint to see available options.",
        example="male_2"
    )
    speech_speed: Optional[float] = Field(
        1.0,
        description="Speech speed multiplier. Values: 0.5=very fast, 0.75=fast, 1.0=normal, 1.25=slow, 1.5=very slow, 2.0=extra slow",
        ge=0.25,
        le=3.0,
        example=1.0
    )
    special_details: Optional[str] = Field(
        None,
        description="Optional specific details or points to include in the conversation"
    )
    target_vocabulary: Optional[List[str]] = Field(
        None,
        description="Optional target vocabulary words to use naturally in the conversation",
        max_length=20,
        example=["departure", "itinerary", "accommodation"]
    )
    target_grammar: Optional[List[str]] = Field(
        None,
        description="Optional target grammar structures to practice in the conversation",
        max_length=10,
        example=["Going to (future)", "Present Continuous for plans"]
    )
    textbook_grade: Optional[str] = Field(
        None,
        description="Grade level for textbook RAG context (e.g., '5', '9').",
        example="5"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "topic": "Planning a weekend trip",
                "difficulty": "B1",
                "length": "short",
                "character1": "John",
                "character2": "Alex",
                "gender1": "male",
                "gender2": "female",
                "voice_id1": "male_1",
                "voice_id2": "female_2",
                "speech_speed": 1.0,
                "special_details": "Include discussing transportation options",
                "target_vocabulary": ["departure", "itinerary"],
                "target_grammar": ["Going to (future)"],
                "textbook_grade": "5"
            }
        }


class DialogueLine(BaseModel):
    """A single line of dialogue."""
    speaker: str = Field(..., description="The name of the speaker")
    text: str = Field(..., description="The dialogue text")


class AudioFileInfo(BaseModel):
    """Information about a generated audio file."""
    filename: str = Field(..., description="Name of the audio file (e.g., JOHN_1.1.wav)")
    speaker: str = Field(..., description="Name of the speaker")
    dialogue_index: int = Field(..., description="Dialogue exchange number (1, 2, 3...)")
    turn_index: int = Field(..., description="Turn within the exchange (1 or 2)")
    text: str = Field(..., description="The text that was converted to speech")
    audio_data: str = Field(..., description="Base64 encoded WAV audio data")


class ConversationResponse(BaseModel):
    """Response model for a generated conversation."""
    
    success: bool = Field(..., description="Whether the request was successful")
    topic: str = Field(..., description="The topic of the conversation")
    difficulty: str = Field(..., description="The difficulty level")
    character1: str = Field(..., description="Name of the first character")
    character2: str = Field(..., description="Name of the second character")
    dialogue: List[DialogueLine] = Field(..., description="The conversation dialogue")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "topic": "Ordering food at a restaurant",
                "difficulty": "B1",
                "character1": "Sarah",
                "character2": "John",
                "dialogue": [
                    {"speaker": "Sarah", "text": "Hi John, have you been to this restaurant before?"},
                    {"speaker": "John", "text": "Yes, I come here quite often. The food is really good."},
                    {"speaker": "Sarah", "text": "That's great! Do they have any vegetarian options?"},
                    {"speaker": "John", "text": "Absolutely! They have a wonderful vegetarian menu."}
                ]
            }
        }


class ConversationWithAudioResponse(BaseModel):
    """Response model for a conversation with generated audio files."""
    
    success: bool = Field(..., description="Whether the request was successful")
    topic: str = Field(..., description="The topic of the conversation")
    difficulty: str = Field(..., description="The difficulty level")
    character1: str = Field(..., description="Name of the first character")
    character2: str = Field(..., description="Name of the second character")
    gender1: str = Field(..., description="Gender of the first character")
    gender2: str = Field(..., description="Gender of the second character")
    dialogue: List[DialogueLine] = Field(..., description="The conversation dialogue")
    audio_files: List[AudioFileInfo] = Field(..., description="List of generated audio files with Base64 encoded audio data")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "topic": "Planning a weekend trip",
                "difficulty": "B1",
                "character1": "John",
                "character2": "Alex",
                "gender1": "male",
                "gender2": "female",
                "dialogue": [
                    {"speaker": "John", "text": "Hey Alex, are you free this weekend?"},
                    {"speaker": "Alex", "text": "Yes, I am! Do you have any plans?"}
                ],
                "audio_files": [
                    {
                        "filename": "JOHN_1.1.wav",
                        "speaker": "JOHN",
                        "dialogue_index": 1,
                        "turn_index": 1,
                        "text": "Hey Alex, are you free this weekend?",
                        "audio_data": "UklGRi4AAABXQVZFZm10IBAAAAABAAEA... (Base64 encoded WAV)"
                    },
                    {
                        "filename": "ALEX_1.2.wav",
                        "speaker": "ALEX",
                        "dialogue_index": 1,
                        "turn_index": 2,
                        "text": "Yes, I am! Do you have any plans?",
                        "audio_data": "UklGRi4AAABXQVZFZm10IBAAAAABAAEA... (Base64 encoded WAV)"
                    }
                ]
            }
        }


class ErrorResponse(BaseModel):
    """Error response model."""
    success: bool = Field(default=False)
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")


class VoiceInfo(BaseModel):
    """Information about a single voice."""
    voice_id: str = Field(..., description="Unique voice identifier to use in requests")
    name: str = Field(..., description="Human-readable voice name")
    description: str = Field(..., description="Description of the voice characteristics")
    speaker_id: int = Field(..., description="Internal speaker ID")


class VoicesResponse(BaseModel):
    """Response model for available voices."""
    male: List[VoiceInfo] = Field(..., description="List of available male voices")
    female: List[VoiceInfo] = Field(..., description="List of available female voices")
    
    class Config:
        json_schema_extra = {
            "example": {
                "male": [
                    {"voice_id": "male_1", "name": "David", "description": "Deep, calm male voice", "speaker_id": 5},
                    {"voice_id": "male_2", "name": "Michael", "description": "Clear, professional male voice", "speaker_id": 27}
                ],
                "female": [
                    {"voice_id": "female_1", "name": "Emily", "description": "Warm, friendly female voice", "speaker_id": 0},
                    {"voice_id": "female_2", "name": "Sarah", "description": "Clear, professional female voice", "speaker_id": 10}
                ]
            }
        }


# ==================== Question Generation Schemas ====================

class QuestionType(str, Enum):
    """Types of questions that can be generated."""
    MULTIPLE_CHOICE = "multiple_choice"
    FILL_BLANK = "fill_blank"
    SENTENCE_BUILDER = "sentence_builder"
    VOCABULARY_QUIZ = "vocabulary_quiz"


# --- Multiple Choice Schemas ---

class GenerateMCQuestionRequest(BaseModel):
    """Request model for generating multiple choice questions from dialogue."""
    
    dialogue_excerpt: str = Field(
        ...,
        description="The dialogue text to generate questions from",
        min_length=10,
        example="Hi, how are you doing today? I'm doing great, thanks for asking!"
    )
    speaker: str = Field(
        ...,
        description="Name of the speaker in the dialogue",
        example="John"
    )
    difficulty: DifficultyLevel = Field(
        ...,
        description="Difficulty level for the questions"
    )
    question_count: int = Field(
        ...,
        ge=1,
        le=10,
        description="Number of questions to generate",
        example=3
    )
    additional_details: Optional[str] = Field(
        None,
        description="Optional additional requirements for question generation",
        example="Focus on understanding emotions and intentions"
    )


class MCOptionResponse(BaseModel):
    """Multiple choice option."""
    label: str = Field(..., description="Option label (A, B, C, D)")
    text: str = Field(..., description="Option text")
    is_correct: bool = Field(..., description="Whether this is the correct answer")


class MCQuestionResponse(BaseModel):
    """Single multiple choice question."""
    question_number: int
    question_text: str
    options: List[MCOptionResponse]
    correct_answer: str
    explanation: str
    related_dialogue: str


class GeneratedMCQuestionsResponse(BaseModel):
    """Response model for generated multiple choice questions."""
    success: bool = Field(..., description="Whether generation was successful")
    dialogue_excerpt: str
    speaker: str
    difficulty: str
    question_count: int
    questions: List[MCQuestionResponse]


# --- Fill in the Blank Schemas ---

class GenerateFillBlankRequest(BaseModel):
    """Request model for generating fill-in-the-blank questions."""
    
    dialogue_excerpt: str = Field(
        ...,
        description="The dialogue text to generate questions from",
        min_length=10
    )
    speaker: str = Field(
        ...,
        description="Name of the speaker"
    )
    difficulty: DifficultyLevel = Field(
        ...,
        description="Difficulty level (affects number of blanks)"
    )
    question_count: int = Field(
        ...,
        ge=1,
        le=10,
        description="Number of questions to generate",
        example=3
    )
    additional_details: Optional[str] = Field(
        None,
        description="Optional additional requirements"
    )


class BlankInfoResponse(BaseModel):
    """Information about a single blank."""
    blank_number: int = Field(..., description="Blank number (1, 2, 3...)")
    correct_word: str = Field(..., description="The correct word for this blank")
    position_in_sentence: int = Field(..., description="Word position in original sentence")


class FillBlankQuestionResponse(BaseModel):
    """Single fill-in-the-blank question."""
    question_number: int
    original_sentence: str = Field(..., description="The complete original sentence")
    sentence_with_blanks: str = Field(..., description="Sentence with ___1___, ___2___ etc.")
    blanks: List[BlankInfoResponse] = Field(..., description="Information about each blank")
    word_options: List[str] = Field(..., description="All word options (correct + distractors)")
    correct_words: List[str] = Field(..., description="Correct words in order")
    speaker: str


class GeneratedFillBlankResponse(BaseModel):
    """Response model for generated fill-in-the-blank questions."""
    success: bool
    dialogue_excerpt: str
    speaker: str
    difficulty: str
    question_count: int
    questions: List[FillBlankQuestionResponse]


# --- Sentence Builder Schemas ---

class GenerateSentenceBuilderRequest(BaseModel):
    """Request model for generating sentence builder questions."""
    
    dialogue_excerpt: str = Field(
        ...,
        description="The dialogue text to generate questions from",
        min_length=10
    )
    speaker: str = Field(
        ...,
        description="Name of the speaker"
    )
    difficulty: DifficultyLevel = Field(
        ...,
        description="Difficulty level (affects sentence complexity)"
    )
    question_count: int = Field(
        ...,
        ge=1,
        le=10,
        description="Number of questions to generate",
        example=3
    )
    additional_details: Optional[str] = Field(
        None,
        description="Optional additional requirements"
    )


class SentenceBuilderQuestionResponse(BaseModel):
    """Single sentence builder question."""
    question_number: int
    original_sentence: str = Field(..., description="The correct sentence")
    scrambled_words: List[str] = Field(..., description="Words in scrambled order")
    word_order: List[int] = Field(..., description="Correct order indices (index i tells original position of scrambled word i)")
    word_count: int
    speaker: str
    hint: Optional[str] = Field(None, description="Hint about the sentence")


class GeneratedSentenceBuilderResponse(BaseModel):
    """Response model for generated sentence builder questions."""
    success: bool
    dialogue_excerpt: str
    speaker: str
    difficulty: str
    question_count: int
    questions: List[SentenceBuilderQuestionResponse]


# --- Vocabulary Quiz Schemas ---

class GenerateVocabQuizRequest(BaseModel):
    """Request model for generating vocabulary quiz questions."""
    
    dialogue_excerpt: str = Field(
        ...,
        description="The dialogue text to extract vocabulary from",
        min_length=10
    )
    speaker: str = Field(
        ...,
        description="Name of the speaker"
    )
    difficulty: DifficultyLevel = Field(
        ...,
        description="Difficulty level for vocabulary selection"
    )
    question_count: int = Field(
        ...,
        ge=1,
        le=10,
        description="Number of vocabulary questions to generate",
        example=3
    )
    additional_details: Optional[str] = Field(
        None,
        description="Optional additional requirements"
    )
    generate_audio: bool = Field(
        True,
        description="Whether to generate audio pronunciation"
    )


class VocabOptionResponse(BaseModel):
    """Vocabulary quiz option (Turkish meaning)."""
    label: str = Field(..., description="Option label (A, B, C, D)")
    text: str = Field(..., description="Turkish meaning")
    is_correct: bool


class VocabQuestionResponse(BaseModel):
    """Single vocabulary quiz question."""
    question_number: int
    english_word: str = Field(..., description="The English word")
    phonetic: str = Field(..., description="IPA phonetic transcription")
    audio_base64: Optional[str] = Field(None, description="Base64 encoded audio")
    audio_format: str = Field(..., description="Audio format (mp3 or none)")
    options: List[VocabOptionResponse] = Field(..., description="4 Turkish meaning options")
    correct_answer: str = Field(..., description="Correct option label")
    correct_meaning: str = Field(..., description="Correct Turkish meaning")
    example_sentence: str
    word_type: str = Field(..., description="Part of speech (noun, verb, etc.)")


class GeneratedVocabQuizResponse(BaseModel):
    """Response model for generated vocabulary quiz questions."""
    success: bool
    dialogue_excerpt: str
    speaker: str
    difficulty: str
    question_count: int
    questions: List[VocabQuestionResponse]
