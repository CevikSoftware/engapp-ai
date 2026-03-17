"""
FastAPI router for Listening Practice endpoints.
"""

from fastapi import APIRouter, HTTPException
from typing import Optional
import os
import base64
from pathlib import Path

from .schemas import (
    ConversationRequest,
    ConversationResponse,
    ConversationWithAudioRequest,
    ConversationWithAudioResponse,
    AudioFileInfo,
    ErrorResponse,
    DifficultyLevel,
    ConversationLength,
    Gender,
    VoicesResponse,
    VoiceInfo,
    # Question generation schemas
    GenerateMCQuestionRequest,
    GeneratedMCQuestionsResponse,
    MCQuestionResponse,
    MCOptionResponse,
    GenerateFillBlankRequest,
    GeneratedFillBlankResponse,
    FillBlankQuestionResponse,
    BlankInfoResponse,
    GenerateSentenceBuilderRequest,
    GeneratedSentenceBuilderResponse,
    SentenceBuilderQuestionResponse,
    GenerateVocabQuizRequest,
    GeneratedVocabQuizResponse,
    VocabQuestionResponse,
    VocabOptionResponse
)
from .conversation_generator import ConversationGenerator
from .question_generator import ListeningQuestionGenerator

# RAG service for textbook context
def _get_rag_context(topic: str, grade: str) -> str:
    """Retrieve textbook RAG context if grade is provided."""
    if not grade:
        return ""
    try:
        from textbook.rag_service import get_rag_service
        rag = get_rag_service()
        return rag.build_context_prompt(query=topic, grade=grade)
    except Exception:
        return ""

router = APIRouter(
    prefix="/listening",
    tags=["Listening Practice"],
    responses={
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)


def get_generator() -> ConversationGenerator:
    """Get or create a ConversationGenerator instance."""
    api_key = os.getenv("TOGETHER_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="TOGETHER_API_KEY environment variable is not set"
        )
    return ConversationGenerator(api_key=api_key)


@router.post(
    "/generate-conversation",
    response_model=ConversationResponse,
    summary="Generate a Conversation (Text Only)",
    description="""
Generate an educational English conversation between two characters for listening practice.

The conversation is designed for English language learners and adapts vocabulary,
grammar complexity, and sentence structure based on the CEFR difficulty level.

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

**Conversation Lengths:**
- **short**: 4-6 exchanges (8-12 total lines)
- **medium**: 8-12 exchanges (16-24 total lines)
- **long**: 14-20 exchanges (28-40 total lines)
"""
)
async def generate_conversation(request: ConversationRequest):
    """
    Generate an educational conversation for English listening practice.
    
    The generated conversation alternates between the two characters,
    starting with character1.
    """
    try:
        generator = get_generator()
        
        # Both schemas and generators use CEFRLevel directly
        from .conversation_generator import ConversationLength as GenLength
        
        length_enum = GenLength(request.length.value)
        
        conversation = generator.generate(
            topic=request.topic,
            difficulty=request.difficulty,
            length=length_enum,
            character1=request.character1,
            character2=request.character2,
            special_details=request.special_details,
            target_vocabulary=request.target_vocabulary,
            target_grammar=request.target_grammar,
            rag_context=_get_rag_context(request.topic, getattr(request, 'textbook_grade', None))
        )
        
        return ConversationResponse(
            success=True,
            topic=conversation.topic,
            difficulty=conversation.difficulty,
            character1=conversation.character1,
            character2=conversation.character2,
            dialogue=[
                {"speaker": line.speaker, "text": line.text}
                for line in conversation.dialogue
            ]
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate conversation: {str(e)}")


@router.post(
    "/generate-conversation-with-audio",
    response_model=ConversationWithAudioResponse,
    summary="Generate Conversation with Audio Files",
    description="""
Generate an educational English conversation and convert each dialogue line to audio.

Each speaker's line is converted to a separate audio file with the naming convention:
- `{SPEAKER}_{dialogue_number}.{turn_number}.wav`

For example, if John speaks first and Alex responds:
- `JOHN_1.1.wav` - John's first line (dialogue 1, turn 1)
- `ALEX_1.2.wav` - Alex's response (dialogue 1, turn 2)
- `ALEX_2.1.wav` - Alex's next line (dialogue 2, turn 1)
- `JOHN_2.2.wav` - John's response (dialogue 2, turn 2)

**Gender Selection:**
Voice selection is based on the gender specified for each character:
- `male`: Uses a male voice
- `female`: Uses a female voice

You can also specify exact voice IDs using `voice_id1` and `voice_id2` parameters.
Use the `/voices` endpoint to see all available voices.

**Speech Speed:**
Control the speech speed with `speech_speed` parameter:
- `0.5` - Very fast (50% duration)
- `0.75` - Fast (75% duration)
- `1.0` - Normal speed (default)
- `1.25` - Slow (125% duration)
- `1.5` - Very slow (150% duration)
- `2.0` - Extra slow (200% duration)
"""
)
async def generate_conversation_with_audio(request: ConversationWithAudioRequest):
    """
    Generate an educational conversation with audio files for each dialogue line.
    Audio data is returned directly as Base64 encoded strings (no files saved on server).
    """
    try:
        # First, generate the conversation text
        generator = get_generator()
        
        from .conversation_generator import ConversationLength as GenLength
        
        length_enum = GenLength(request.length.value)
        
        conversation = generator.generate(
            topic=request.topic,
            difficulty=request.difficulty,
            length=length_enum,
            character1=request.character1,
            character2=request.character2,
            special_details=request.special_details,
            target_vocabulary=request.target_vocabulary,
            target_grammar=request.target_grammar,
            rag_context=_get_rag_context(request.topic, getattr(request, 'textbook_grade', None))
        )
        
        # Import TTS service and generate audio
        try:
            from .tts_service import TTSService, Gender as TTSGender
            
            tts = TTSService()
            
            gender1_enum = TTSGender(request.gender1.value)
            gender2_enum = TTSGender(request.gender2.value)
            
            dialogue_data = [
                {"speaker": line.speaker, "text": line.text}
                for line in conversation.dialogue
            ]
            
            # Generate audio without saving to disk (output_dir=None)
            # Use specific voice IDs and speech speed if provided
            audio_files = tts.generate_conversation_audio(
                dialogue=dialogue_data,
                character1=request.character1,
                character2=request.character2,
                gender1=gender1_enum,
                gender2=gender2_enum,
                output_dir=None,  # Don't save to disk
                conversation_id="",
                voice_id1=request.voice_id1,
                voice_id2=request.voice_id2,
                speech_speed=request.speech_speed or 1.0
            )
            
            # Convert audio bytes to Base64 and create response
            audio_file_infos = [
                AudioFileInfo(
                    filename=af.filename,
                    speaker=af.speaker,
                    dialogue_index=af.dialogue_index,
                    turn_index=af.turn_index,
                    text=af.text,
                    audio_data=base64.b64encode(af.audio_data).decode('utf-8')
                )
                for af in audio_files
            ]
            
        except Exception as tts_error:
            raise HTTPException(
                status_code=500,
                detail=f"TTS generation failed: {str(tts_error)}"
            )
        
        return ConversationWithAudioResponse(
            success=True,
            topic=conversation.topic,
            difficulty=conversation.difficulty,
            character1=conversation.character1,
            character2=conversation.character2,
            gender1=request.gender1.value,
            gender2=request.gender2.value,
            dialogue=[
                {"speaker": line.speaker, "text": line.text}
                for line in conversation.dialogue
            ],
            audio_files=audio_file_infos
        )
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate conversation: {str(e)}")


@router.get(
    "/voices",
    response_model=VoicesResponse,
    summary="Get Available Voices",
    description="""
Returns all available voices organized by gender.

Each voice has:
- **voice_id**: Unique identifier to use in `voice_id1` or `voice_id2` parameters
- **name**: Human-readable voice name
- **description**: Description of voice characteristics
- **speaker_id**: Internal speaker ID (for reference)

Use the `voice_id` values when making requests to `/generate-conversation-with-audio`.
"""
)
async def get_available_voices():
    """Get all available voices for TTS."""
    from .tts_service import TTSService
    
    voices = TTSService.get_available_voices()
    
    return VoicesResponse(
        male=[VoiceInfo(**v) for v in voices["male"]],
        female=[VoiceInfo(**v) for v in voices["female"]]
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
            {"value": "A1", "name": "A1 (Beginner)", "description": "Very basic, everyday words. Simple present tense only. Very short sentences."},
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
    "/genders",
    summary="Get Available Genders",
    description="Returns available gender options for voice selection."
)
async def get_genders():
    """Get available gender options for voice selection."""
    return {
        "genders": [
            {
                "value": "male",
                "name": "Male",
                "description": "Male voice"
            },
            {
                "value": "female",
                "name": "Female",
                "description": "Female voice"
            }
        ]
    }


@router.get(
    "/conversation-lengths",
    summary="Get Available Conversation Lengths",
    description="Returns a list of available conversation length options."
)
async def get_conversation_lengths():
    """Get all available conversation length options."""
    return {
        "conversation_lengths": [
            {
                "value": "short",
                "name": "Short",
                "description": "4-6 exchanges (8-12 total dialogue lines)",
                "estimated_duration": "1-2 minutes"
            },
            {
                "value": "medium",
                "name": "Medium",
                "description": "8-12 exchanges (16-24 total dialogue lines)",
                "estimated_duration": "3-5 minutes"
            },
            {
                "value": "long",
                "name": "Long",
                "description": "14-20 exchanges (28-40 total dialogue lines)",
                "estimated_duration": "6-10 minutes"
            }
        ]
    }


@router.get(
    "/topic-suggestions",
    summary="Get Topic Suggestions",
    description="Returns suggested conversation topics organized by category."
)
async def get_topic_suggestions():
    """Get suggested conversation topics for listening practice."""
    return {
        "topic_categories": [
            {
                "category": "Daily Life",
                "topics": [
                    "Morning routines",
                    "Going shopping",
                    "Cooking dinner together",
                    "Planning the weekend",
                    "Discussing household chores"
                ]
            },
            {
                "category": "Travel & Tourism",
                "topics": [
                    "Booking a hotel room",
                    "Asking for directions",
                    "At the airport",
                    "Planning a vacation",
                    "Discussing travel experiences"
                ]
            },
            {
                "category": "Food & Dining",
                "topics": [
                    "Ordering at a restaurant",
                    "Discussing favorite foods",
                    "Making a reservation",
                    "Trying new cuisine",
                    "Food allergies and preferences"
                ]
            },
            {
                "category": "Work & Business",
                "topics": [
                    "Job interview",
                    "Meeting a new colleague",
                    "Discussing a project",
                    "Asking for time off",
                    "Business negotiation"
                ]
            },
            {
                "category": "Health & Wellness",
                "topics": [
                    "Visiting the doctor",
                    "At the pharmacy",
                    "Discussing exercise habits",
                    "Mental health conversation",
                    "Healthy eating discussion"
                ]
            },
            {
                "category": "Education",
                "topics": [
                    "Discussing classes",
                    "Study group meeting",
                    "Talking about exams",
                    "Career planning",
                    "Learning a new skill"
                ]
            },
            {
                "category": "Social Situations",
                "topics": [
                    "Meeting someone new",
                    "Making plans with friends",
                    "Birthday party planning",
                    "Catching up with an old friend",
                    "Resolving a misunderstanding"
                ]
            }
        ]
    }


# ==================== Question Generation Endpoints ====================

def get_question_generator() -> ListeningQuestionGenerator:
    """Get or create a ListeningQuestionGenerator instance."""
    api_key = os.getenv("TOGETHER_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="TOGETHER_API_KEY environment variable is not set"
        )
    return ListeningQuestionGenerator(api_key=api_key)


@router.post(
    "/generate-mc-questions",
    response_model=GeneratedMCQuestionsResponse,
    summary="Generate Multiple Choice Questions from Dialogue",
    description="""
Generate multiple choice comprehension questions based on a dialogue excerpt.

Each question has 4 options (A, B, C, D) with exactly one correct answer.
Questions test understanding of the dialogue content, speaker intentions, and implied meanings.

**Use Case:**
After generating a conversation, extract dialogue lines and create comprehension questions.

**Difficulty affects:**
- Question complexity (direct facts vs. inference)
- Distractor difficulty (obviously wrong vs. plausible)
"""
)
async def generate_mc_questions(request: GenerateMCQuestionRequest):
    """Generate multiple choice questions from dialogue."""
    try:
        generator = get_question_generator()
        
        result = generator.generate_multiple_choice(
            dialogue_excerpt=request.dialogue_excerpt,
            speaker=request.speaker,
            difficulty=request.difficulty,
            question_count=request.question_count,
            additional_details=request.additional_details
        )
        
        questions_response = [
            MCQuestionResponse(
                question_number=q.question_number,
                question_text=q.question_text,
                options=[MCOptionResponse(label=o.label, text=o.text, is_correct=o.is_correct) for o in q.options],
                correct_answer=q.correct_answer,
                explanation=q.explanation,
                related_dialogue=q.related_dialogue
            )
            for q in result.questions
        ]
        
        return GeneratedMCQuestionsResponse(
            success=True,
            dialogue_excerpt=result.dialogue_excerpt,
            speaker=result.speaker,
            difficulty=result.difficulty,
            question_count=result.question_count,
            questions=questions_response
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate questions: {str(e)}")


@router.post(
    "/generate-fill-blank",
    response_model=GeneratedFillBlankResponse,
    summary="Generate Fill-in-the-Blank Questions from Dialogue",
    description="""
Generate fill-in-the-blank questions where words are removed from dialogue sentences.

**Features:**
- Blanks are marked as ___1___, ___2___, etc.
- Word options include correct words + 3 extra distractors
- Each blank's correct word is clearly specified

**Difficulty affects number of blanks:**
- Beginner/Elementary: 1 blank per sentence
- Intermediate/Upper-Intermediate: 2 blanks per sentence  
- Advanced: 3 blanks per sentence

**Word options:** Always (number of blanks + 3) words provided.
Example: 2 blanks = 5 word options (2 correct + 3 distractors)
"""
)
async def generate_fill_blank(request: GenerateFillBlankRequest):
    """Generate fill-in-the-blank questions from dialogue."""
    try:
        generator = get_question_generator()
        
        result = generator.generate_fill_blank(
            dialogue_excerpt=request.dialogue_excerpt,
            speaker=request.speaker,
            difficulty=request.difficulty,
            question_count=request.question_count,
            additional_details=request.additional_details
        )
        
        questions_response = [
            FillBlankQuestionResponse(
                question_number=q.question_number,
                original_sentence=q.original_sentence,
                sentence_with_blanks=q.sentence_with_blanks,
                blanks=[BlankInfoResponse(
                    blank_number=b.blank_number,
                    correct_word=b.correct_word,
                    position_in_sentence=b.position_in_sentence
                ) for b in q.blanks],
                word_options=q.word_options,
                correct_words=q.correct_words,
                speaker=q.speaker
            )
            for q in result.questions
        ]
        
        return GeneratedFillBlankResponse(
            success=True,
            dialogue_excerpt=result.dialogue_excerpt,
            speaker=result.speaker,
            difficulty=result.difficulty,
            question_count=result.question_count,
            questions=questions_response
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate questions: {str(e)}")


@router.post(
    "/generate-sentence-builder",
    response_model=GeneratedSentenceBuilderResponse,
    summary="Generate Sentence Builder Questions from Dialogue",
    description="""
Generate sentence ordering/building questions from dialogue.

**Response includes:**
- `original_sentence`: The correct complete sentence
- `scrambled_words`: Words in randomized order
- `word_order`: Array showing correct position for each scrambled word
- `hint`: Clue about the sentence meaning

**Example:**
- Original: "How are you today?"
- Scrambled: ["today?", "are", "How", "you"]
- Word order: [2, 1, 0, 3] (meaning scrambled[0] goes to position 2, etc.)

**Difficulty affects sentence length:**
- Beginner: 4-6 words
- Elementary: 5-8 words
- Intermediate: 7-12 words
- Upper-Intermediate: 10-15 words
- Advanced: 12-18 words
"""
)
async def generate_sentence_builder(request: GenerateSentenceBuilderRequest):
    """Generate sentence builder questions from dialogue."""
    try:
        generator = get_question_generator()
        
        result = generator.generate_sentence_builder(
            dialogue_excerpt=request.dialogue_excerpt,
            speaker=request.speaker,
            difficulty=request.difficulty,
            question_count=request.question_count,
            additional_details=request.additional_details
        )
        
        questions_response = [
            SentenceBuilderQuestionResponse(
                question_number=q.question_number,
                original_sentence=q.original_sentence,
                scrambled_words=q.scrambled_words,
                word_order=q.word_order,
                word_count=q.word_count,
                speaker=q.speaker,
                hint=q.hint
            )
            for q in result.questions
        ]
        
        return GeneratedSentenceBuilderResponse(
            success=True,
            dialogue_excerpt=result.dialogue_excerpt,
            speaker=result.speaker,
            difficulty=result.difficulty,
            question_count=result.question_count,
            questions=questions_response
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate questions: {str(e)}")


@router.post(
    "/generate-vocab-quiz",
    response_model=GeneratedVocabQuizResponse,
    summary="Generate Vocabulary Quiz from Dialogue",
    description="""
Generate vocabulary quiz questions with audio and Turkish translations.

**Each question includes:**
- `english_word`: The vocabulary word from dialogue
- `phonetic`: IPA phonetic transcription (e.g., /ˈæpəl/)
- `audio_base64`: Base64 encoded MP3 pronunciation (if generate_audio=true)
- `options`: 4 Turkish meaning options (1 correct, 3 distractors)
- `example_sentence`: Example usage of the word
- `word_type`: Part of speech (noun, verb, adjective, etc.)

**Example:**
Word: "restaurant"
Phonetic: /ˈrɛstərɑnt/
Options: A) restoran ✓, B) market, C) hastane, D) okul

**Audio:** MP3 format, decode base64 to play.
"""
)
async def generate_vocab_quiz(request: GenerateVocabQuizRequest):
    """Generate vocabulary quiz questions from dialogue."""
    try:
        generator = get_question_generator()
        
        result = generator.generate_vocabulary_quiz(
            dialogue_excerpt=request.dialogue_excerpt,
            speaker=request.speaker,
            difficulty=request.difficulty,
            question_count=request.question_count,
            additional_details=request.additional_details,
            generate_audio=request.generate_audio
        )
        
        questions_response = [
            VocabQuestionResponse(
                question_number=q.question_number,
                english_word=q.english_word,
                phonetic=q.phonetic,
                audio_base64=q.audio_base64,
                audio_format=q.audio_format,
                options=[VocabOptionResponse(label=o.label, text=o.text, is_correct=o.is_correct) for o in q.options],
                correct_answer=q.correct_answer,
                correct_meaning=q.correct_meaning,
                example_sentence=q.example_sentence,
                word_type=q.word_type
            )
            for q in result.questions
        ]
        
        return GeneratedVocabQuizResponse(
            success=True,
            dialogue_excerpt=result.dialogue_excerpt,
            speaker=result.speaker,
            difficulty=result.difficulty,
            question_count=result.question_count,
            questions=questions_response
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate questions: {str(e)}")


@router.get(
    "/question-types",
    summary="Get Available Question Types",
    description="Returns information about all available question types for listening practice."
)
async def get_question_types():
    """Get all available question types and their descriptions."""
    return {
        "question_types": [
            {
                "type": "multiple_choice",
                "name": "Multiple Choice",
                "endpoint": "/listening/generate-mc-questions",
                "description": "4-option comprehension questions about dialogue content",
                "features": ["Tests comprehension", "Explanations provided", "Difficulty-scaled"]
            },
            {
                "type": "fill_blank",
                "name": "Fill in the Blank",
                "endpoint": "/listening/generate-fill-blank",
                "description": "Complete sentences by filling missing words",
                "features": ["Multiple blanks per sentence", "Word bank provided", "Blank positions tracked"]
            },
            {
                "type": "sentence_builder",
                "name": "Sentence Builder",
                "endpoint": "/listening/generate-sentence-builder",
                "description": "Arrange scrambled words to form correct sentences",
                "features": ["Words randomized", "Correct order provided", "Hints available"]
            },
            {
                "type": "vocabulary_quiz",
                "name": "Vocabulary Quiz",
                "endpoint": "/listening/generate-vocab-quiz",
                "description": "Match English words with Turkish meanings",
                "features": ["Audio pronunciation", "Phonetic transcription", "Example sentences"]
            }
        ]
    }
