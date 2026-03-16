"""
Pydantic schemas for Reading Practice API endpoints.
"""

from typing import Optional, List
from pydantic import BaseModel, Field
from enum import Enum

from cefr_config import CEFRLevel as DifficultyLevel


class TextLength(str, Enum):
    SHORT = "short"          # 50-100 words
    MEDIUM = "medium"        # 150-250 words
    LONG = "long"            # 300-500 words
    VERY_LONG = "very_long"  # 500-800 words


class ContentType(str, Enum):
    ARTICLE = "article"              # News article, blog post
    STORY = "story"                  # Short story, narrative
    EMAIL = "email"                  # Formal or informal email
    LETTER = "letter"                # Formal or informal letter
    ESSAY = "essay"                  # Academic or opinion essay
    DIALOGUE = "dialogue"            # Conversation transcript
    DESCRIPTION = "description"      # Descriptive text
    INSTRUCTIONS = "instructions"    # How-to guide, manual
    REVIEW = "review"                # Product/movie/book review
    REPORT = "report"                # Business or academic report


class WritingStyle(str, Enum):
    FORMAL = "formal"
    INFORMAL = "informal"
    NEUTRAL = "neutral"
    ACADEMIC = "academic"
    CONVERSATIONAL = "conversational"
    PROFESSIONAL = "professional"


class TensePreference(str, Enum):
    PAST = "past"                    # Past tenses focus
    PRESENT = "present"              # Present tenses focus
    FUTURE = "future"                # Future tenses focus
    MIXED = "mixed"                  # Natural mix of tenses
    NARRATIVE = "narrative"          # Past simple/continuous for storytelling


class GenerateTextRequest(BaseModel):
    """Request model for generating a reading text."""
    
    concept: str = Field(
        ...,
        description="The main topic or concept for the text",
        example="Climate change and its effects on wildlife"
    )
    content_type: ContentType = Field(
        ...,
        description="The type of text to generate",
        example="article"
    )
    difficulty: DifficultyLevel = Field(
        ...,
        description="The difficulty level of the text"
    )
    length: TextLength = Field(
        ...,
        description="The approximate length of the text"
    )
    required_words: List[str] = Field(
        ...,
        description="List of words that MUST appear in the text (at least once each)",
        min_length=1,
        max_length=20,
        example=["environment", "pollution", "sustainable", "habitat", "endangered"]
    )
    writing_style: Optional[WritingStyle] = Field(
        None,
        description="The writing style/register (formal, informal, etc.)"
    )
    tense_preference: Optional[TensePreference] = Field(
        None,
        description="Preferred tense usage in the text"
    )
    target_grammar: Optional[List[str]] = Field(
        None,
        description="Optional target grammar structures to incorporate in the text",
        max_length=10,
        example=["Passive Voice", "Relative Clauses", "Present Perfect"]
    )
    additional_details: Optional[str] = Field(
        None,
        description="Any additional requirements or context for the text",
        example="Include statistics and expert opinions. Target audience is university students."
    )
    textbook_grade: Optional[str] = Field(
        None,
        description="Grade level for textbook RAG context (e.g., '5', '9'). If set, retrieves relevant textbook content to align the generated text.",
        example="5"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "concept": "The importance of learning a second language",
                "content_type": "article",
                "difficulty": "B1",
                "length": "medium",
                "required_words": ["bilingual", "communication", "culture", "opportunity", "brain", "skills"],
                "writing_style": "neutral",
                "tense_preference": "present",
                "additional_details": "Include benefits for career and personal development"
            }
        }


class GeneratedText(BaseModel):
    """Response model for a generated text."""
    
    success: bool = Field(..., description="Whether the request was successful")
    concept: str = Field(..., description="The topic/concept of the text")
    content_type: str = Field(..., description="The type of text generated")
    difficulty: str = Field(..., description="The difficulty level")
    length: str = Field(..., description="The length category")
    title: str = Field(..., description="The title of the generated text")
    text: str = Field(..., description="The generated reading text")
    word_count: int = Field(..., description="Actual word count of the text")
    required_words_used: List[str] = Field(..., description="List of required words that were used")
    required_words_missing: List[str] = Field(..., description="List of required words NOT found (should be empty)")
    writing_style: Optional[str] = Field(None, description="The writing style used")
    tense_preference: Optional[str] = Field(None, description="The tense preference used")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "concept": "The importance of learning a second language",
                "content_type": "article",
                "difficulty": "B1",
                "length": "medium",
                "title": "Why Learning a Second Language Matters",
                "text": "In today's interconnected world, being bilingual has become more valuable than ever...",
                "word_count": 187,
                "required_words_used": ["bilingual", "communication", "culture", "opportunity", "brain", "skills"],
                "required_words_missing": [],
                "writing_style": "neutral",
                "tense_preference": "present"
            }
        }


class ErrorResponse(BaseModel):
    """Error response model."""
    success: bool = Field(default=False)
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")


class ContentTypeInfo(BaseModel):
    """Information about a content type."""
    value: str
    name: str
    description: str


class ContentTypesResponse(BaseModel):
    """Response model for content types listing."""
    content_types: List[ContentTypeInfo]


class WritingStyleInfo(BaseModel):
    """Information about a writing style."""
    value: str
    name: str
    description: str


class WritingStylesResponse(BaseModel):
    """Response model for writing styles listing."""
    writing_styles: List[WritingStyleInfo]


class TenseInfo(BaseModel):
    """Information about a tense preference."""
    value: str
    name: str
    description: str


class TensesResponse(BaseModel):
    """Response model for tense preferences listing."""
    tense_preferences: List[TenseInfo]


# ==================== Question Generation Schemas ====================

# Use CEFRLevel as QuestionDifficulty (same as DifficultyLevel)
QuestionDifficulty = DifficultyLevel


class GenerateQuestionsRequest(BaseModel):
    """Request model for generating multiple choice questions."""
    
    reading_text: str = Field(
        ...,
        description="The reading passage to generate questions from",
        min_length=50,
        example="Climate change is one of the most pressing issues facing our planet today..."
    )
    difficulty: QuestionDifficulty = Field(
        ...,
        description="The difficulty level for the questions"
    )
    question_count: int = Field(
        ...,
        ge=1,
        le=10,
        description="Number of questions to generate (1-10)",
        example=5
    )
    keywords: Optional[List[str]] = Field(
        None,
        description="Optional list of keywords/vocabulary from the text to focus questions on",
        max_length=20,
        example=["climate change", "greenhouse gases", "renewable energy"]
    )
    additional_instructions: Optional[str] = Field(
        None,
        description="Optional additional requirements or instructions for question generation",
        example="Focus on vocabulary and main idea questions"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "reading_text": "Climate change is one of the most pressing issues facing our planet today. Scientists have observed significant changes in global temperatures over the past century, with the average temperature rising by approximately 1.1 degrees Celsius since the pre-industrial era. The main cause of this warming is the increased concentration of greenhouse gases in the atmosphere, primarily carbon dioxide from burning fossil fuels.",
                "difficulty": "B1",
                "question_count": 5,
                "keywords": ["climate change", "greenhouse gases", "temperature"],
                "additional_instructions": "Include at least one vocabulary question"
            }
        }


class QuestionOptionResponse(BaseModel):
    """Response model for a single question option."""
    label: str = Field(..., description="Option label (A, B, C, or D)")
    text: str = Field(..., description="Option text")
    is_correct: bool = Field(..., description="Whether this option is the correct answer")


class QuestionResponse(BaseModel):
    """Response model for a single question."""
    question_number: int = Field(..., description="Question number")
    question_text: str = Field(..., description="The question text")
    options: List[QuestionOptionResponse] = Field(..., description="List of 4 options")
    correct_answer: str = Field(..., description="The correct answer label (A, B, C, or D)")
    explanation: str = Field(..., description="Explanation of why the correct answer is correct")


class GeneratedQuestionsResponse(BaseModel):
    """Response model for generated questions."""
    
    success: bool = Field(..., description="Whether the request was successful")
    reading_text: str = Field(..., description="The original reading text")
    difficulty: str = Field(..., description="The difficulty level used")
    question_count: int = Field(..., description="Number of questions generated")
    questions: List[QuestionResponse] = Field(..., description="List of generated questions")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "reading_text": "Climate change is one of the most pressing issues...",
                "difficulty": "B1",
                "question_count": 3,
                "questions": [
                    {
                        "question_number": 1,
                        "question_text": "What is the main topic of the passage?",
                        "options": [
                            {"label": "A", "text": "Ocean pollution", "is_correct": False},
                            {"label": "B", "text": "Climate change", "is_correct": True},
                            {"label": "C", "text": "Deforestation", "is_correct": False},
                            {"label": "D", "text": "Air quality", "is_correct": False}
                        ],
                        "correct_answer": "B",
                        "explanation": "The passage explicitly states that climate change is the main topic."
                    }
                ]
            }
        }


# ==================== Fill in the Blank Schemas ====================

class GenerateFillBlankRequest(BaseModel):
    """Request model for generating fill-in-the-blank questions."""
    
    reading_text: str = Field(
        ...,
        description="The reading passage to base fill-in-the-blank questions on",
        min_length=50
    )
    difficulty: QuestionDifficulty = Field(
        ...,
        description="The difficulty level for the questions"
    )
    question_count: int = Field(
        ...,
        ge=1,
        le=10,
        description="Number of questions to generate (1-10)",
        example=5
    )
    additional_instructions: Optional[str] = Field(
        None,
        description="Optional additional requirements for question generation"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "reading_text": "Climate change affects weather patterns worldwide...",
                "difficulty": "B1",
                "question_count": 5,
                "additional_instructions": "Focus on vocabulary related to environment"
            }
        }


class FillBlankOptionResponse(BaseModel):
    """Response model for a fill-in-the-blank option."""
    label: str = Field(..., description="Option label (A, B, C, or D)")
    text: str = Field(..., description="Option text (the word)")
    is_correct: bool = Field(..., description="Whether this option is correct")


class FillBlankQuestionResponse(BaseModel):
    """Response model for a single fill-in-the-blank question."""
    question_number: int = Field(..., description="Question number")
    sentence_with_blank: str = Field(..., description="Sentence with _____ for the blank")
    complete_sentence: str = Field(..., description="Complete sentence with the answer")
    options: List[FillBlankOptionResponse] = Field(..., description="List of 4 options")
    correct_answer: str = Field(..., description="Correct answer label (A, B, C, or D)")
    correct_word: str = Field(..., description="The correct word that fills the blank")
    explanation: str = Field(..., description="Explanation of why this is correct")


class GeneratedFillBlankResponse(BaseModel):
    """Response model for generated fill-in-the-blank questions."""
    
    success: bool = Field(..., description="Whether the request was successful")
    reading_text: str = Field(..., description="The original reading text")
    difficulty: str = Field(..., description="The difficulty level used")
    question_count: int = Field(..., description="Number of questions generated")
    questions: List[FillBlankQuestionResponse] = Field(..., description="List of questions")


# ==================== Sentence Builder Schemas ====================

class GenerateSentenceBuilderRequest(BaseModel):
    """Request model for generating sentence building questions."""
    
    reading_text: str = Field(
        ...,
        description="The reading passage to base sentences on",
        min_length=50
    )
    difficulty: QuestionDifficulty = Field(
        ...,
        description="The difficulty level for the sentences"
    )
    question_count: int = Field(
        ...,
        ge=1,
        le=10,
        description="Number of questions to generate (1-10)",
        example=5
    )
    additional_instructions: Optional[str] = Field(
        None,
        description="Optional additional requirements for sentence generation"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "reading_text": "Technology has changed how we communicate...",
                "difficulty": "B1",
                "question_count": 5,
                "additional_instructions": "Include sentences with phrasal verbs"
            }
        }


class SentenceBuilderQuestionResponse(BaseModel):
    """Response model for a single sentence builder question."""
    question_number: int = Field(..., description="Question number")
    correct_sentence: str = Field(..., description="The complete correct sentence")
    scrambled_words: List[str] = Field(..., description="Words in scrambled order")
    word_count: int = Field(..., description="Number of words in the sentence")
    hint: Optional[str] = Field(None, description="Optional hint for the user")


class GeneratedSentenceBuilderResponse(BaseModel):
    """Response model for generated sentence builder questions."""
    
    success: bool = Field(..., description="Whether the request was successful")
    reading_text: str = Field(..., description="The original reading text")
    difficulty: str = Field(..., description="The difficulty level used")
    question_count: int = Field(..., description="Number of questions generated")
    questions: List[SentenceBuilderQuestionResponse] = Field(..., description="List of questions")


# ==================== Vocabulary Audio Quiz Schemas ====================

class GenerateVocabQuizRequest(BaseModel):
    """Request model for generating vocabulary audio quiz questions."""
    
    difficulty: QuestionDifficulty = Field(
        ...,
        description="The difficulty level for vocabulary selection"
    )
    question_count: int = Field(
        ...,
        ge=1,
        le=10,
        description="Number of questions to generate (1-10)",
        example=5
    )
    word_list: Optional[List[str]] = Field(
        None,
        description="Optional specific words to create questions for",
        max_length=10,
        example=["apple", "beautiful", "environment"]
    )
    topic: Optional[str] = Field(
        None,
        description="Optional topic to generate vocabulary from",
        example="food and cooking"
    )
    additional_instructions: Optional[str] = Field(
        None,
        description="Optional additional requirements"
    )
    generate_audio: bool = Field(
        True,
        description="Whether to generate audio pronunciation"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "difficulty": "B1",
                "question_count": 5,
                "topic": "technology",
                "generate_audio": True
            }
        }


class VocabOptionResponse(BaseModel):
    """Response model for a vocabulary quiz option."""
    label: str = Field(..., description="Option label (A, B, C, or D)")
    text: str = Field(..., description="Turkish meaning")
    is_correct: bool = Field(..., description="Whether this is the correct meaning")


class VocabQuizQuestionResponse(BaseModel):
    """Response model for a single vocabulary quiz question."""
    question_number: int = Field(..., description="Question number")
    english_word: str = Field(..., description="The English word")
    phonetic: str = Field(..., description="IPA phonetic transcription")
    audio_base64: Optional[str] = Field(None, description="Base64 encoded audio")
    audio_format: str = Field(..., description="Audio format (mp3, wav, none)")
    options: List[VocabOptionResponse] = Field(..., description="4 Turkish meaning options")
    correct_answer: str = Field(..., description="Correct answer label (A, B, C, or D)")
    correct_meaning: str = Field(..., description="The correct Turkish meaning")
    example_sentence: str = Field(..., description="Example sentence using the word")
    word_type: str = Field(..., description="Word type (noun, verb, adjective, etc.)")


class GeneratedVocabQuizResponse(BaseModel):
    """Response model for generated vocabulary quiz questions."""
    
    success: bool = Field(..., description="Whether the request was successful")
    difficulty: str = Field(..., description="The difficulty level used")
    question_count: int = Field(..., description="Number of questions generated")
    questions: List[VocabQuizQuestionResponse] = Field(..., description="List of questions")


class SingleWordQuizRequest(BaseModel):
    """Request model for generating a quiz for a single word."""
    
    word: str = Field(
        ...,
        description="The English word to create a quiz for",
        example="environment"
    )
    generate_audio: bool = Field(
        True,
        description="Whether to generate audio pronunciation"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "word": "beautiful",
                "generate_audio": True
            }
        }
