"""
FastAPI router for Reading Practice endpoints.
"""

from fastapi import APIRouter, HTTPException
from typing import Optional
import os

from .schemas import (
    GenerateTextRequest,
    GeneratedText,
    ErrorResponse,
    DifficultyLevel,
    TextLength,
    ContentType,
    WritingStyle,
    TensePreference,
    ContentTypeInfo,
    ContentTypesResponse,
    WritingStyleInfo,
    WritingStylesResponse,
    TenseInfo,
    TensesResponse,
    # Question generation schemas
    QuestionDifficulty,
    GenerateQuestionsRequest,
    GeneratedQuestionsResponse,
    QuestionResponse,
    QuestionOptionResponse,
    # Fill in the blank schemas
    GenerateFillBlankRequest,
    GeneratedFillBlankResponse,
    FillBlankQuestionResponse,
    FillBlankOptionResponse,
    # Sentence builder schemas
    GenerateSentenceBuilderRequest,
    GeneratedSentenceBuilderResponse,
    SentenceBuilderQuestionResponse,
    # Vocabulary quiz schemas
    GenerateVocabQuizRequest,
    GeneratedVocabQuizResponse,
    VocabQuizQuestionResponse,
    VocabOptionResponse,
    SingleWordQuizRequest
)
from .text_generator import TextGenerator
from .question_generator import QuestionGenerator
from .fill_blank_generator import FillBlankGenerator
from .sentence_builder_generator import SentenceBuilderGenerator
from .vocab_quiz_generator import VocabQuizGenerator

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
    prefix="/reading",
    tags=["Reading Practice"],
    responses={
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)


def get_generator() -> TextGenerator:
    """Get or create a TextGenerator instance."""
    api_key = os.getenv("TOGETHER_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="TOGETHER_API_KEY environment variable is not set"
        )
    return TextGenerator(api_key=api_key)


@router.post(
    "/generate-text",
    response_model=GeneratedText,
    summary="Generate a Reading Text",
    description="""
Generate an educational English reading text based on specified parameters.

The text is designed for English language learners and adapts vocabulary,
grammar complexity, and sentence structure based on the CEFR difficulty level.

**Key Features:**
- All required words will be used at least once in the generated text
- Text length and difficulty are customizable
- Multiple content types available (article, story, email, etc.)
- Optional writing style and tense preferences

**CEFR Difficulty Levels:**
- **A1**: Beginner - Very simple vocabulary, present tenses only
- **A2**: Elementary - Basic vocabulary, simple past tense
- **A1-A2**: Beginner to Elementary transition
- **B1**: Pre-Intermediate - Moderate vocabulary, phrasal verbs
- **A2-B1**: Elementary to Pre-Intermediate transition
- **B2**: Intermediate - Rich vocabulary, complex structures
- **B1-B2**: Pre-Intermediate to Intermediate transition
- **C1**: Upper-Intermediate - Sophisticated vocabulary, all structures
- **B2-C1**: Intermediate to Upper-Intermediate transition
- **C2**: Advanced - Near-native, academic and literary vocabulary
- **C1-C2**: Upper-Intermediate to Advanced transition

**Text Lengths:**
- **short**: 50-100 words
- **medium**: 150-250 words
- **long**: 300-500 words
- **very_long**: 500-800 words

**Content Types:**
- article, story, email, letter, essay, dialogue, description, instructions, review, report

**Optional Parameters:**
- **writing_style**: formal, informal, neutral, academic, conversational, professional
- **tense_preference**: past, present, future, mixed, narrative
- **additional_details**: Any extra requirements or context
"""
)
async def generate_text(request: GenerateTextRequest):
    """
    Generate an educational reading text with required vocabulary words.
    
    All words in the required_words list will appear at least once in the generated text.
    """
    try:
        generator = get_generator()
        
        # Convert non-difficulty enums to module enums
        from .text_generator import (
            TextLength as GenLength,
            ContentType as GenContentType,
            WritingStyle as GenStyle,
            TensePreference as GenTense
        )
        
        length_enum = GenLength(request.length.value)
        content_type_enum = GenContentType(request.content_type.value)
        
        style_enum = GenStyle(request.writing_style.value) if request.writing_style else None
        tense_enum = GenTense(request.tense_preference.value) if request.tense_preference else None
        
        result = generator.generate(
            concept=request.concept,
            content_type=content_type_enum,
            difficulty=request.difficulty,
            length=length_enum,
            required_words=request.required_words,
            writing_style=style_enum,
            tense_preference=tense_enum,
            additional_details=request.additional_details,
            target_grammar=request.target_grammar,
            rag_context=_get_rag_context(request.concept, getattr(request, 'textbook_grade', None))
        )
        
        return GeneratedText(
            success=True,
            concept=result.concept,
            content_type=result.content_type,
            difficulty=result.difficulty,
            length=result.length,
            title=result.title,
            text=result.text,
            word_count=result.word_count,
            required_words_used=result.required_words_used,
            required_words_missing=result.required_words_missing,
            writing_style=result.writing_style,
            tense_preference=result.tense_preference
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate text: {str(e)}")


@router.get(
    "/content-types",
    response_model=ContentTypesResponse,
    summary="Get Available Content Types",
    description="Returns a list of available content types for text generation."
)
async def get_content_types():
    """Get all available content types."""
    return ContentTypesResponse(
        content_types=[
            ContentTypeInfo(
                value="article",
                name="Article",
                description="News article or blog post with headline and body paragraphs"
            ),
            ContentTypeInfo(
                value="story",
                name="Story",
                description="Short narrative story with characters, setting, and plot"
            ),
            ContentTypeInfo(
                value="email",
                name="Email",
                description="Formal or informal email with greeting, body, and closing"
            ),
            ContentTypeInfo(
                value="letter",
                name="Letter",
                description="Formal or informal letter with proper structure"
            ),
            ContentTypeInfo(
                value="essay",
                name="Essay",
                description="Academic or opinion essay with introduction, body, and conclusion"
            ),
            ContentTypeInfo(
                value="dialogue",
                name="Dialogue",
                description="Conversation transcript between two or more people"
            ),
            ContentTypeInfo(
                value="description",
                name="Description",
                description="Descriptive text with sensory details and vivid language"
            ),
            ContentTypeInfo(
                value="instructions",
                name="Instructions",
                description="Step-by-step how-to guide or manual"
            ),
            ContentTypeInfo(
                value="review",
                name="Review",
                description="Product, movie, or book review with opinions and recommendations"
            ),
            ContentTypeInfo(
                value="report",
                name="Report",
                description="Business or academic report with factual information"
            )
        ]
    )


@router.get(
    "/writing-styles",
    response_model=WritingStylesResponse,
    summary="Get Available Writing Styles",
    description="Returns a list of available writing styles/registers."
)
async def get_writing_styles():
    """Get all available writing styles."""
    return WritingStylesResponse(
        writing_styles=[
            WritingStyleInfo(
                value="formal",
                name="Formal",
                description="Professional language, no contractions, objective tone"
            ),
            WritingStyleInfo(
                value="informal",
                name="Informal",
                description="Casual language, contractions, friendly tone"
            ),
            WritingStyleInfo(
                value="neutral",
                name="Neutral",
                description="Balanced language, neither too formal nor casual"
            ),
            WritingStyleInfo(
                value="academic",
                name="Academic",
                description="Scholarly language, precise terminology, objective analysis"
            ),
            WritingStyleInfo(
                value="conversational",
                name="Conversational",
                description="Friendly, engaging, as if speaking to the reader"
            ),
            WritingStyleInfo(
                value="professional",
                name="Professional",
                description="Business-appropriate, concise, respectful"
            )
        ]
    )


@router.get(
    "/tense-preferences",
    response_model=TensesResponse,
    summary="Get Available Tense Preferences",
    description="Returns a list of available tense preference options."
)
async def get_tense_preferences():
    """Get all available tense preferences."""
    return TensesResponse(
        tense_preferences=[
            TenseInfo(
                value="past",
                name="Past Tenses",
                description="Focus on past simple, past continuous, past perfect"
            ),
            TenseInfo(
                value="present",
                name="Present Tenses",
                description="Focus on present simple, present continuous, present perfect"
            ),
            TenseInfo(
                value="future",
                name="Future Forms",
                description="Focus on will, going to, future continuous"
            ),
            TenseInfo(
                value="mixed",
                name="Mixed Tenses",
                description="Natural mix of tenses as appropriate"
            ),
            TenseInfo(
                value="narrative",
                name="Narrative Tenses",
                description="Past simple for events, past continuous for background"
            )
        ]
    )


@router.get(
    "/difficulty-levels",
    summary="Get Available Difficulty Levels",
    description="Returns a list of available difficulty levels with descriptions."
)
async def get_difficulty_levels():
    """Get all available CEFR difficulty levels and their descriptions."""
    return {
        "difficulty_levels": [
            {"value": "A1", "name": "A1 (Beginner)", "description": "Very basic, everyday words. Simple present tense only. Very short sentences (3-6 words)."},
            {"value": "A2", "name": "A2 (Elementary)", "description": "Simple vocabulary, present and past tenses, common expressions."},
            {"value": "A1-A2", "name": "A1-A2 (Beginner - Elementary)", "description": "Transition level between A1 and A2."},
            {"value": "B1", "name": "B1 (Pre-Intermediate)", "description": "Moderate vocabulary, various tenses, some phrasal verbs."},
            {"value": "B2", "name": "B2 (Intermediate)", "description": "Good vocabulary range, complex structures, common idioms."},
            {"value": "A2-B1", "name": "A2-B1 (Elementary - Pre-Int.)", "description": "Transition level between A2 and B1."},
            {"value": "B1-B2", "name": "B1-B2 (Pre-Int. - Intermediate)", "description": "Transition level between B1 and B2."},
            {"value": "C1", "name": "C1 (Upper-Intermediate)", "description": "Rich vocabulary, all grammatical structures, idioms and nuanced expressions."},
            {"value": "C2", "name": "C2 (Advanced)", "description": "Near-native vocabulary, sophisticated structures, subtle nuances."},
            {"value": "B2-C1", "name": "B2-C1 (Intermediate - Upper-Int.)", "description": "Transition level between B2 and C1."},
            {"value": "C1-C2", "name": "C1-C2 (Upper-Int. - Advanced)", "description": "Transition level between C1 and C2."}
        ]
    }


@router.get(
    "/text-lengths",
    summary="Get Available Text Lengths",
    description="Returns a list of available text length options."
)
async def get_text_lengths():
    """Get all available text length options."""
    return {
        "text_lengths": [
            {
                "value": "short",
                "name": "Short",
                "description": "50-100 words",
                "word_range": {"min": 50, "max": 100}
            },
            {
                "value": "medium",
                "name": "Medium",
                "description": "150-250 words",
                "word_range": {"min": 150, "max": 250}
            },
            {
                "value": "long",
                "name": "Long",
                "description": "300-500 words",
                "word_range": {"min": 300, "max": 500}
            },
            {
                "value": "very_long",
                "name": "Very Long",
                "description": "500-800 words",
                "word_range": {"min": 500, "max": 800}
            }
        ]
    }


# ==================== Question Generation Endpoints ====================

def get_question_generator() -> QuestionGenerator:
    """Get or create a QuestionGenerator instance."""
    api_key = os.getenv("TOGETHER_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="TOGETHER_API_KEY environment variable is not set"
        )
    return QuestionGenerator(api_key=api_key)


@router.post(
    "/generate-questions",
    response_model=GeneratedQuestionsResponse,
    summary="Generate Multiple Choice Questions",
    description="""
Generate multiple choice reading comprehension questions based on a given reading text.

Each question has exactly 4 options (A, B, C, D) with only one correct answer.
Questions are designed to test reading comprehension at the specified difficulty level.

**Key Features:**
- Questions are based solely on the provided reading text
- 4 options per question with exactly one correct answer
- Explanations provided for each correct answer
- Optional keywords to focus questions on specific vocabulary
- Customizable difficulty and question count

**Difficulty Levels:**
- **beginner**: Simple, direct factual questions with obvious correct answers
- **elementary**: Straightforward comprehension with some inference questions
- **intermediate**: Main ideas, vocabulary-in-context, cause and effect
- **upper_intermediate**: Complex comprehension, interpretation, tone analysis
- **advanced**: Critical analysis, subtle implications, rhetorical analysis

**Question Count:** 1-10 questions per request

**Optional Parameters:**
- **keywords**: List of words/vocabulary from the text to focus questions on
- **additional_instructions**: Any extra requirements for question generation
"""
)
async def generate_questions(request: GenerateQuestionsRequest):
    """
    Generate multiple choice questions based on a reading text.
    
    All questions will be in English and based on the content of the provided text.
    """
    try:
        generator = get_question_generator()
        
        result = generator.generate_questions(
            reading_text=request.reading_text,
            difficulty=request.difficulty,
            question_count=request.question_count,
            keywords=request.keywords,
            additional_instructions=request.additional_instructions
        )
        
        # Convert to response model
        questions_response = []
        for q in result.questions:
            options_response = [
                QuestionOptionResponse(
                    label=opt.label,
                    text=opt.text,
                    is_correct=opt.is_correct
                )
                for opt in q.options
            ]
            questions_response.append(QuestionResponse(
                question_number=q.question_number,
                question_text=q.question_text,
                options=options_response,
                correct_answer=q.correct_answer,
                explanation=q.explanation
            ))
        
        return GeneratedQuestionsResponse(
            success=True,
            reading_text=result.reading_text,
            difficulty=result.difficulty,
            question_count=result.question_count,
            questions=questions_response
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate questions: {str(e)}")


@router.get(
    "/question-difficulty-levels",
    summary="Get Available Question Difficulty Levels",
    description="Returns a list of available difficulty levels for question generation."
)
async def get_question_difficulty_levels():
    """Get all available CEFR difficulty levels for question generation."""
    return {
        "difficulty_levels": [
            {"value": "A1", "name": "A1 (Beginner)", "description": "Simple, direct factual questions about explicitly stated information."},
            {"value": "A2", "name": "A2 (Elementary)", "description": "Straightforward comprehension questions focusing on main ideas."},
            {"value": "A1-A2", "name": "A1-A2 (Beginner - Elementary)", "description": "Transition between A1 and A2 question difficulty."},
            {"value": "B1", "name": "B1 (Pre-Intermediate)", "description": "Questions about main ideas, vocabulary-in-context, cause-effect."},
            {"value": "B2", "name": "B2 (Intermediate)", "description": "Complex comprehension including inference and interpretation."},
            {"value": "A2-B1", "name": "A2-B1 (Elementary - Pre-Int.)", "description": "Transition between A2 and B1 question difficulty."},
            {"value": "B1-B2", "name": "B1-B2 (Pre-Int. - Intermediate)", "description": "Transition between B1 and B2 question difficulty."},
            {"value": "C1", "name": "C1 (Upper-Intermediate)", "description": "Analytical questions requiring critical evaluation."},
            {"value": "C2", "name": "C2 (Advanced)", "description": "Sophisticated analytical questions requiring nuanced understanding."},
            {"value": "B2-C1", "name": "B2-C1 (Intermediate - Upper-Int.)", "description": "Transition between B2 and C1 question difficulty."},
            {"value": "C1-C2", "name": "C1-C2 (Upper-Int. - Advanced)", "description": "Transition between C1 and C2 question difficulty."}
        ]
    }


# ==================== Fill in the Blank Endpoints ====================

def get_fill_blank_generator() -> FillBlankGenerator:
    """Get or create a FillBlankGenerator instance."""
    api_key = os.getenv("TOGETHER_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="TOGETHER_API_KEY environment variable is not set"
        )
    return FillBlankGenerator(api_key=api_key)


@router.post(
    "/generate-fill-blank",
    response_model=GeneratedFillBlankResponse,
    summary="Generate Fill-in-the-Blank Questions",
    description="""
Generate fill-in-the-blank vocabulary questions based on a reading text.

Each question presents a sentence with a blank (___) and 4 word options.
Only one option correctly completes the sentence both grammatically and contextually.

**Key Features:**
- Sentences are relevant to the reading text's topic
- 4 word options per question with exactly one correct answer
- Tests vocabulary knowledge and contextual understanding
- Explanations provided for correct answers

**Difficulty Levels:**
- **beginner**: Common, everyday vocabulary with obvious correct answers
- **elementary**: Simple vocabulary with plausible distractors
- **intermediate**: Moderate vocabulary, collocations, phrasal verbs
- **upper_intermediate**: Sophisticated vocabulary, idioms
- **advanced**: Academic/professional vocabulary, subtle distinctions
"""
)
async def generate_fill_blank(request: GenerateFillBlankRequest):
    """Generate fill-in-the-blank questions based on a reading text."""
    try:
        generator = get_fill_blank_generator()
        
        result = generator.generate_questions(
            reading_text=request.reading_text,
            difficulty=request.difficulty,
            question_count=request.question_count,
            additional_instructions=request.additional_instructions
        )
        
        questions_response = []
        for q in result.questions:
            options_response = [
                FillBlankOptionResponse(
                    label=opt.label,
                    text=opt.text,
                    is_correct=opt.is_correct
                )
                for opt in q.options
            ]
            questions_response.append(FillBlankQuestionResponse(
                question_number=q.question_number,
                sentence_with_blank=q.sentence_with_blank,
                complete_sentence=q.complete_sentence,
                options=options_response,
                correct_answer=q.correct_answer,
                correct_word=q.correct_word,
                explanation=q.explanation
            ))
        
        return GeneratedFillBlankResponse(
            success=True,
            reading_text=result.reading_text,
            difficulty=result.difficulty,
            question_count=result.question_count,
            questions=questions_response
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate fill-blank questions: {str(e)}")


# ==================== Sentence Builder Endpoints ====================

def get_sentence_builder_generator() -> SentenceBuilderGenerator:
    """Get or create a SentenceBuilderGenerator instance."""
    api_key = os.getenv("TOGETHER_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="TOGETHER_API_KEY environment variable is not set"
        )
    return SentenceBuilderGenerator(api_key=api_key)


@router.post(
    "/generate-sentence-builder",
    response_model=GeneratedSentenceBuilderResponse,
    summary="Generate Sentence Building Questions",
    description="""
Generate sentence building/ordering questions based on a reading text.

Each question provides scrambled words that the user must arrange to form a correct sentence.
The response includes both the correct sentence and the scrambled words.

**Key Features:**
- Sentences are relevant to the reading text's topic
- Words are randomly scrambled for each question
- Hints provided to help users
- Word count included for each sentence

**Difficulty Levels:**
- **beginner**: 4-6 words, simple subject-verb-object
- **elementary**: 5-8 words, basic connectors
- **intermediate**: 7-12 words, compound sentences
- **upper_intermediate**: 10-15 words, complex structures
- **advanced**: 12-18 words, sophisticated grammar

**Response includes:**
- `correct_sentence`: The properly formed sentence
- `scrambled_words`: Array of words in random order
- `word_count`: Number of words to arrange
- `hint`: Optional clue about the sentence
"""
)
async def generate_sentence_builder(request: GenerateSentenceBuilderRequest):
    """Generate sentence building questions based on a reading text."""
    try:
        generator = get_sentence_builder_generator()
        
        result = generator.generate_questions(
            reading_text=request.reading_text,
            difficulty=request.difficulty,
            question_count=request.question_count,
            additional_instructions=request.additional_instructions
        )
        
        questions_response = [
            SentenceBuilderQuestionResponse(
                question_number=q.question_number,
                correct_sentence=q.correct_sentence,
                scrambled_words=q.scrambled_words,
                word_count=q.word_count,
                hint=q.hint
            )
            for q in result.questions
        ]
        
        return GeneratedSentenceBuilderResponse(
            success=True,
            reading_text=result.reading_text,
            difficulty=result.difficulty,
            question_count=result.question_count,
            questions=questions_response
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate sentence builder questions: {str(e)}")


# ==================== Vocabulary Audio Quiz Endpoints ====================

def get_vocab_quiz_generator() -> VocabQuizGenerator:
    """Get or create a VocabQuizGenerator instance."""
    api_key = os.getenv("TOGETHER_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="TOGETHER_API_KEY environment variable is not set"
        )
    return VocabQuizGenerator(api_key=api_key)


@router.post(
    "/generate-vocab-quiz",
    response_model=GeneratedVocabQuizResponse,
    summary="Generate Vocabulary Audio Quiz",
    description="""
Generate vocabulary quiz questions with audio pronunciation and Turkish meanings.

Each question includes:
- An English word with audio pronunciation
- IPA phonetic transcription
- 4 Turkish meaning options (1 correct, 3 distractors)
- Example sentence using the word

**Key Features:**
- Audio pronunciation generated via TTS (gTTS)
- IPA phonetic transcription included
- Turkish translations for meanings
- Distractors are plausible but incorrect Turkish words

**Parameters:**
- `difficulty`: Vocabulary complexity level
- `question_count`: Number of words (1-10)
- `word_list`: Optional specific words to quiz
- `topic`: Optional topic for vocabulary selection
- `generate_audio`: Whether to include audio (default: true)

**Audio Format:**
- Base64 encoded MP3 audio
- Can be decoded and played directly
"""
)
async def generate_vocab_quiz(request: GenerateVocabQuizRequest):
    """Generate vocabulary audio quiz questions."""
    try:
        generator = get_vocab_quiz_generator()
        
        result = generator.generate_questions(
            difficulty=request.difficulty,
            question_count=request.question_count,
            word_list=request.word_list,
            topic=request.topic,
            additional_instructions=request.additional_instructions,
            generate_audio=request.generate_audio
        )
        
        questions_response = []
        for q in result.questions:
            options_response = [
                VocabOptionResponse(
                    label=opt.label,
                    text=opt.text,
                    is_correct=opt.is_correct
                )
                for opt in q.options
            ]
            questions_response.append(VocabQuizQuestionResponse(
                question_number=q.question_number,
                english_word=q.english_word,
                phonetic=q.phonetic,
                audio_base64=q.audio_base64,
                audio_format=q.audio_format,
                options=options_response,
                correct_answer=q.correct_answer,
                correct_meaning=q.correct_meaning,
                example_sentence=q.example_sentence,
                word_type=q.word_type
            ))
        
        return GeneratedVocabQuizResponse(
            success=True,
            difficulty=result.difficulty,
            question_count=result.question_count,
            questions=questions_response
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate vocabulary quiz: {str(e)}")


@router.post(
    "/generate-single-word-quiz",
    response_model=VocabQuizQuestionResponse,
    summary="Generate Quiz for a Single Word",
    description="""
Generate a vocabulary quiz question for a specific English word.

Returns:
- Audio pronunciation of the word
- IPA phonetic transcription
- 4 Turkish meaning options
- Example sentence

This is useful when you want to quiz a specific word rather than generating random vocabulary.
"""
)
async def generate_single_word_quiz(request: SingleWordQuizRequest):
    """Generate a quiz question for a single specific word."""
    try:
        generator = get_vocab_quiz_generator()
        
        result = generator.generate_single_word_quiz(
            word=request.word,
            generate_audio=request.generate_audio
        )
        
        options_response = [
            VocabOptionResponse(
                label=opt.label,
                text=opt.text,
                is_correct=opt.is_correct
            )
            for opt in result.options
        ]
        
        return VocabQuizQuestionResponse(
            question_number=result.question_number,
            english_word=result.english_word,
            phonetic=result.phonetic,
            audio_base64=result.audio_base64,
            audio_format=result.audio_format,
            options=options_response,
            correct_answer=result.correct_answer,
            correct_meaning=result.correct_meaning,
            example_sentence=result.example_sentence,
            word_type=result.word_type
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate word quiz: {str(e)}")
