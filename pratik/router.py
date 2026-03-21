"""
FastAPI router for Practice (Pratik) endpoints.
Ultra-fast async implementation with TTS support.
"""

import asyncio
from fastapi import APIRouter, HTTPException

from .schemas import (
    StartConversationRequest,
    StartConversationResponse,
    ChatRequest,
    ChatResponse,
    ErrorResponse
)
from .session_manager import session_manager
from .conversation_service import get_conversation_service
from .tts_service import get_tts_service, FastTTSService, Gender


router = APIRouter(
    prefix="/practice",
    tags=["Practice - Interactive Conversation"],
    responses={
        500: {"model": ErrorResponse},
        404: {"model": ErrorResponse}
    }
)


def _resolve_voice_id(voice_gender: str = None, voice_id: str = None) -> str:
    """Resolve voice ID from gender or direct voice_id."""
    if voice_id:
        voice = FastTTSService.get_voice_by_id(voice_id)
        if voice:
            return voice.voice_id
    
    # Default by gender
    gender = Gender.FEMALE if voice_gender == "female" else Gender.MALE if voice_gender == "male" else Gender.FEMALE
    return FastTTSService.get_voice_by_gender(gender).voice_id


# ============== API 1: Start Conversation ==============

@router.post(
    "/start",
    response_model=StartConversationResponse,
    summary="Start a New Conversation",
    description="""
Start a new practice conversation with TTS support.

**Required:**
- `partner_name`: Name of the AI partner (e.g., "Sarah")
- `llm_role`: Role description (e.g., "friendly coffee shop barista")
- `total_steps`: Number of conversation turns (3-30)

**Optional:**
- `topic`: Conversation topic
- `details`: Additional context
- `vocabulary`: Words to practice
- `difficulty`: CEFR level - A1, A2, A1-A2, B1, B2, A2-B1, B1-B2, C1, C2, B2-C1, C1-C2 (default: B1)
- `voice_gender`: "male" or "female" (default: female)
- `voice_id`: Specific voice ID (see below)
- `speech_rate`: Speech speed 0.5-1.5 (0.75=slow, 1.0=normal, 1.25=fast)
- `enable_tts`: Enable audio output (default: true)

**CEFR Difficulty Levels:**
- `A1`: Very basic vocabulary, very short sentences, patient pace
- `A2`: Simple vocabulary, short sentences, slow pace
- `B1`: Normal vocabulary, natural conversation flow
- `B2`: Good vocabulary range, natural expressions
- `C1`: Advanced vocabulary, idioms, varied grammar
- `C2`: Sophisticated vocabulary, complex grammar, challenging responses
- Combined levels (A1-A2, A2-B1, B1-B2, B2-C1, C1-C2) for transitional students

**Available Female Voices:**
- `female_1` - Emily: Warm, friendly female voice
- `female_2` - Sarah: Clear, professional female
- `female_3` - Jessica: Soft, gentle female
- `female_4` - Ashley: Young, cheerful female
- `female_5` - Amanda: Confident female voice
- `female_6` - Rachel: Calm, soothing female
- `female_7` - Olivia: Bright, energetic female
- `female_8` - Emma: Natural, conversational female

**Available Male Voices:**
- `male_1` - David: Deep, calm male voice
- `male_2` - Michael: Clear, professional male
- `male_3` - James: Warm, friendly male
- `male_4` - Robert: Authoritative male voice
- `male_5` - William: Young, energetic male
- `male_6` - Daniel: Mature, steady male
- `male_7` - Thomas: Rich, resonant male
- `male_8` - Christopher: Strong, confident male

Returns `session_id`, AI's opening message, and audio (base64).
"""
)
async def start_conversation(request: StartConversationRequest):
    """Start a new conversation session with TTS."""
    try:
        # Resolve voice
        voice_id = _resolve_voice_id(request.voice_gender, request.voice_id)
        
        # Create session
        session = await session_manager.create_session(
            partner_name=request.partner_name,
            llm_role=request.llm_role,
            total_steps=request.total_steps,
            topic=request.topic,
            details=request.details,
            vocabulary=request.vocabulary,
            target_grammar=request.target_grammar,
            voice_id=voice_id,
            enable_tts=request.enable_tts,
            difficulty=request.difficulty.value if hasattr(request.difficulty, 'value') else request.difficulty,
            speech_rate=request.speech_rate,
            textbook_grade=getattr(request, 'textbook_grade', None)
        )
        
        # Generate opening message
        service = get_conversation_service()
        opening = await service.generate_opening(session)
        
        # Generate TTS in parallel if enabled
        audio_base64 = None
        if request.enable_tts:
            try:
                tts = await get_tts_service()
                voice = FastTTSService.get_voice_by_id(voice_id)
                audio_base64 = await tts.synthesize_to_base64(opening, voice.speaker_id, session.speech_rate)
            except Exception as e:
                # TTS failure shouldn't break the API
                print(f"TTS warning: {e}")
        
        # Store opening in session
        session.add_message("assistant", opening)
        await session_manager.update_session(session)
        
        return StartConversationResponse(
            session_id=session.session_id,
            opening_message=opening,
            partner_name=session.partner_name,
            total_steps=session.total_steps,
            audio_base64=audio_base64,
            voice_id=voice_id
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============== API 2: Chat ==============

@router.post(
    "/chat",
    response_model=ChatResponse,
    summary="Send Message in Conversation",
    description="""
Send a message and get AI response with audio.

**Required:**
- `session_id`: From /start endpoint
- `user_message`: Your response

**Response includes:**
- `ai_message`: AI's response
- `audio_base64`: Base64 WAV audio of the response
- `current_step`: Current turn number
- `remaining_steps`: Steps left in conversation
- `is_done`: True when conversation ends

**Step-aware behavior:**
- LLM adjusts responses based on remaining steps
- Starts wrapping up 2-3 steps before the end
- Final step gives a natural conclusion without new questions
"""
)
async def chat(request: ChatRequest):
    """Process user message and generate response with TTS."""
    
    # Get session
    session = await session_manager.get_session(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # If conversation is already done, return a friendly message
    if session.is_done:
        return ChatResponse(
            session_id=session.session_id,
            ai_message="This conversation has already been completed. Great job! Please start a new practice session to continue learning.",
            current_step=session.current_step,
            total_steps=session.total_steps,
            remaining_steps=0,
            is_done=True,
            audio_base64=None
        )
    
    try:
        # Add user message to history
        session.add_message("user", request.user_message)
        session.increment_step()
        
        # Generate response
        service = get_conversation_service()
        ai_message, _, is_done = await service.generate_response(
            session, 
            request.user_message
        )
        
        # Generate TTS in parallel if enabled
        audio_base64 = None
        if session.enable_tts:
            try:
                tts = await get_tts_service()
                voice = FastTTSService.get_voice_by_id(session.voice_id)
                if voice:
                    audio_base64 = await tts.synthesize_to_base64(ai_message, voice.speaker_id, session.speech_rate)
            except Exception as e:
                print(f"TTS warning: {e}")
        
        # Add AI response to history
        session.add_message("assistant", ai_message)
        session.is_done = is_done
        
        # Update session
        await session_manager.update_session(session)
        
        remaining = session.get_remaining_steps()
        
        return ChatResponse(
            session_id=session.session_id,
            ai_message=ai_message,
            current_step=session.current_step,
            total_steps=session.total_steps,
            remaining_steps=remaining,
            is_done=is_done,
            audio_base64=audio_base64
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============== API 3: Get Available Voices ==============

@router.get(
    "/voices",
    summary="Get Available Voices",
    description="Get list of all available TTS voices organized by gender."
)
async def get_voices():
    """Get all available TTS voices."""
    return FastTTSService.get_available_voices()
