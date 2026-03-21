"""
Ultra-fast Async Conversation Service
Optimized for minimal latency with streaming and async operations.
"""

import os
import asyncio
from typing import Optional, Tuple
from openai import AsyncOpenAI

from .session_manager import SessionData
from cefr_config import get_conversation_prompt, get_cefr_spec


class ConversationService:
    """
    High-performance async conversation service.
    Uses OpenAI-compatible async client for maximum speed.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("TOGETHER_API_KEY")
        if not self.api_key:
            raise ValueError("TOGETHER_API_KEY required")
        
        # Async OpenAI client with Together AI
        self.client = AsyncOpenAI(
            api_key=self.api_key,
            base_url="https://api.together.xyz/v1"
        )
        self.model = "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo"
    
    def _build_system_prompt(self, session: SessionData, remaining_steps: int) -> str:
        """Build compact system prompt with step awareness and CEFR difficulty."""
        parts = [f"You are {session.partner_name}, {session.llm_role}."]
        
        # Add CEFR-based difficulty instructions
        cefr_prompt = get_conversation_prompt(session.difficulty)
        spec = get_cefr_spec(session.difficulty)
        parts.append(f"\nDIFFICULTY: CEFR {session.difficulty}\n{cefr_prompt}")
        
        if session.topic:
            parts.append(f"Topic: {session.topic}.")
        
        if session.details:
            parts.append(session.details)
        
        if session.vocabulary:
            parts.append(f"""⚠️ MANDATORY TARGET VOCABULARY: {', '.join(session.vocabulary)}
CRITICAL RULES:
- You MUST use at least 70-80% of these vocabulary words during the conversation.
- Use them naturally in your responses so the student hears them in context.
- Gently encourage the student to use these words too.
- If the student doesn't use them, guide the conversation to create opportunities for these words.
- This is a STRICT REQUIREMENT, not optional.""")
        
        if session.target_grammar:
            parts.append(f"""⚠️ MANDATORY TARGET GRAMMAR STRUCTURES: {', '.join(session.target_grammar)}
CRITICAL RULES:
- You MUST use ALL of these grammar structures during the conversation.
- Demonstrate each grammar pattern naturally in your responses.
- Encourage the student to practice these grammar patterns.
- If the student makes grammar errors with these structures, gently correct them.
- This is a STRICT REQUIREMENT — do NOT skip any grammar structure.""")
        
        # Textbook RAG context
        if session.textbook_grade:
            try:
                from textbook.rag_service import get_rag_service
                rag = get_rag_service()
                query = session.topic or session.llm_role
                rag_context = rag.build_context_prompt(query=query, grade=session.textbook_grade)
                if rag_context:
                    parts.append(rag_context)
            except Exception:
                pass
        
        # Add step-aware behavior instructions
        if remaining_steps <= 1:
            # Final step - wrap up, absolutely no questions
            parts.append("""
⚠️ FINAL STEP RULES:
- Do NOT ask ANY questions
- Do NOT use question marks (?)
- Do NOT offer new options or suggestions
- Give only conclusive, closing statements
- End with a definitive goodbye""")
        elif remaining_steps == 2:
            # Second to last - start wrapping up, minimal questions
            parts.append("⚠️ WRAPPING UP (2 turns left): Keep response brief. Only ask a simple yes/no question if absolutely necessary. Start moving toward conclusion.")
        elif remaining_steps == 3:
            # Third to last - begin gentle transition  
            parts.append("Conversation ending soon (3 turns left). Keep responses shorter, avoid complex new topics.")
        else:
            # Normal conversation - adjust response length by CEFR level
            sentence_length = spec.get("sentence_length", {}).get("average_words", 10)
            if sentence_length <= 7:
                parts.append("Keep responses very short and simple (1-2 sentences).")
            elif sentence_length >= 18:
                parts.append("Feel free to give detailed, engaging responses (3-5 sentences).")
            else:
                parts.append("Keep responses natural, conversational, and concise (2-4 sentences max).")
        
        parts.append("Respond ONLY in English.")
        
        return " ".join(parts)
    
    def _build_closing_prompt(self, session: SessionData, is_overtime: bool = False) -> str:
        """Build prompt for final turn - NO summary needed."""
        overtime_note = ""
        if is_overtime:
            overtime_note = "The user continued chatting beyond the planned steps - they're really engaged! "
        
        return f"""⚠️ CRITICAL: This is the ABSOLUTE FINAL turn of this conversation. {overtime_note}

STRICT RULES - YOU MUST FOLLOW:
❌ DO NOT ask ANY questions (no "Would you like...?", "Do you want...?", "How about...?", etc.)
❌ DO NOT suggest anything new or offer additional options
❌ DO NOT use question marks in your response
❌ DO NOT extend the conversation in any way
✅ ONLY give a final, conclusive statement that ends the interaction

YOUR RESPONSE MUST:
1. Directly address/complete what the user asked for (e.g., "Your americano will be ready in 5 minutes.")
2. Add a warm, definitive goodbye (e.g., "Have a wonderful day! Goodbye!")

EXAMPLE (Coffee shop scenario):
"Perfect, your americano will be ready in about 5 minutes. It was lovely chatting with you today! Have a great day, goodbye!"

Remember: NO QUESTIONS, NO OFFERS, just conclude and say goodbye."""
    
    async def generate_opening(self, session: SessionData) -> str:
        """Generate opening message - fast async call."""
        remaining_steps = session.total_steps  # Full steps available at start
        system = self._build_system_prompt(session, remaining_steps)
        
        user_prompt = f"Start the conversation naturally as {session.partner_name}. Give a friendly opening that invites the user to respond. Keep it short (1-2 sentences)."
        
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=150,
            temperature=0.8
        )
        
        return response.choices[0].message.content.strip()
    
    async def generate_response(
        self, 
        session: SessionData, 
        user_message: str
    ) -> Tuple[str, Optional[str], bool]:
        """
        Generate AI response to user message.
        
        Returns:
            Tuple of (ai_message, summary_if_done, is_done)
        """
        # Check if we've reached or exceeded total steps - time to close
        is_final = session.current_step >= session.total_steps
        is_overtime = session.current_step > session.total_steps  # User continued beyond planned steps
        remaining_steps = session.get_remaining_steps()
        
        # Build messages with step awareness
        system = self._build_system_prompt(session, remaining_steps)
        
        messages = [{"role": "system", "content": system}]
        
        # Add conversation history (last 6 messages max for speed)
        history = session.get_conversation_history()[-6:]
        messages.extend(history)
        
        # Add current user message
        messages.append({"role": "user", "content": user_message})
        
        # Add closing instruction if final (including overtime)
        if is_final:
            messages.append({
                "role": "system", 
                "content": self._build_closing_prompt(session, is_overtime)
            })
        
        # Async LLM call
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=350 if is_final else 200,
            temperature=0.7
        )
        
        content = response.choices[0].message.content.strip()
        
        # Parse response - remove any accidental summary if LLM added it
        if "---SUMMARY---" in content:
            content = content.split("---SUMMARY---")[0].strip()
        
        # Return - no summary needed
        return content, None, is_final


# Global instance
_service: Optional[ConversationService] = None


def get_conversation_service() -> ConversationService:
    """Get or create conversation service singleton."""
    global _service
    if _service is None:
        _service = ConversationService()
    return _service
