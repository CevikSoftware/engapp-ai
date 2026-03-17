"""
Listening Practice Module
Generates educational English conversations and comprehension questions using AI.
"""

from .conversation_generator import ConversationGenerator, generate_conversation
from .question_generator import ListeningQuestionGenerator
from .router import router

__all__ = [
    "ConversationGenerator",
    "generate_conversation",
    "ListeningQuestionGenerator",
    "router"
]
