"""
Ultra-fast Session Manager for Practice Conversations
In-memory storage with minimal overhead.
"""

import uuid
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Optional, List
from dataclasses import dataclass, field


@dataclass
class Message:
    """A single message in the conversation."""
    role: str  # 'user' or 'assistant'
    content: str


@dataclass 
class SessionData:
    """Lightweight session data structure."""
    
    session_id: str
    partner_name: str
    llm_role: str
    total_steps: int
    current_step: int = 0
    topic: Optional[str] = None
    details: Optional[str] = None
    vocabulary: List[str] = field(default_factory=list)
    target_grammar: List[str] = field(default_factory=list)
    messages: List[Message] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)
    is_done: bool = False
    voice_id: Optional[str] = None
    enable_tts: bool = True
    difficulty: str = "B1"  # CEFR level: A1, A2, B1, B2, C1, C2, etc.
    speech_rate: float = 1.0  # 0.5-1.5
    textbook_grade: Optional[str] = None  # Grade for textbook RAG context
    
    def add_message(self, role: str, content: str):
        """Add a message to conversation history."""
        self.messages.append(Message(role=role, content=content))
        self.last_activity = datetime.now()
    
    def increment_step(self):
        """Increment conversation step."""
        self.current_step += 1
        self.last_activity = datetime.now()
    
    def get_remaining_steps(self) -> int:
        """Get remaining steps in conversation."""
        return max(0, self.total_steps - self.current_step)
    
    def get_conversation_history(self) -> List[Dict[str, str]]:
        """Get conversation history for LLM context."""
        return [{"role": m.role, "content": m.content} for m in self.messages]


class SessionManager:
    """
    Fast, thread-safe session manager.
    Minimal locking for maximum speed.
    """
    
    def __init__(self, timeout_minutes: int = 60):
        self._sessions: Dict[str, SessionData] = {}
        self._lock = asyncio.Lock()
        self._timeout = timedelta(minutes=timeout_minutes)
        self._cleanup_task: Optional[asyncio.Task] = None
    
    async def start_cleanup(self):
        """Start background cleanup."""
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
    
    async def _cleanup_loop(self):
        """Cleanup expired sessions every 5 minutes."""
        while True:
            try:
                await asyncio.sleep(300)
                await self._cleanup_expired()
            except asyncio.CancelledError:
                break
            except Exception:
                pass
    
    async def _cleanup_expired(self):
        """Remove expired sessions."""
        now = datetime.now()
        async with self._lock:
            expired = [
                sid for sid, s in self._sessions.items()
                if now - s.last_activity > self._timeout
            ]
            for sid in expired:
                del self._sessions[sid]
    
    def _generate_id(self) -> str:
        """Generate short unique ID."""
        return uuid.uuid4().hex[:16]
    
    async def create_session(
        self,
        partner_name: str,
        llm_role: str,
        total_steps: int,
        topic: Optional[str] = None,
        details: Optional[str] = None,
        vocabulary: Optional[List[str]] = None,
        target_grammar: Optional[List[str]] = None,
        voice_id: Optional[str] = None,
        enable_tts: bool = True,
        difficulty: str = "B1",
        speech_rate: float = 1.0,
        textbook_grade: Optional[str] = None
    ) -> SessionData:
        """Create new session - fast, minimal locking."""
        session_id = self._generate_id()
        
        session = SessionData(
            session_id=session_id,
            partner_name=partner_name,
            llm_role=llm_role,
            total_steps=total_steps,
            topic=topic,
            details=details,
            vocabulary=vocabulary or [],
            target_grammar=target_grammar or [],
            voice_id=voice_id,
            enable_tts=enable_tts,
            difficulty=difficulty,
            speech_rate=speech_rate,
            textbook_grade=textbook_grade
        )
        
        async with self._lock:
            self._sessions[session_id] = session
        
        return session
    
    async def get_session(self, session_id: str) -> Optional[SessionData]:
        """Get session by ID - no locking for reads."""
        return self._sessions.get(session_id)
    
    async def update_session(self, session: SessionData):
        """Update session - minimal locking."""
        session.last_activity = datetime.now()
        self._sessions[session.session_id] = session
    
    async def delete_session(self, session_id: str):
        """Delete session."""
        async with self._lock:
            self._sessions.pop(session_id, None)


# Global instance
session_manager = SessionManager()
