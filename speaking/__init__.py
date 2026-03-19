"""
Speaking Practice Module
Provides word pronunciation and phonetics API endpoints.
"""

from .router import router
from .word_service import WordPronunciationService

__all__ = ["router", "WordPronunciationService"]
