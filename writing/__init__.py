"""
Writing Practice Module
Provides writing task generation and analysis API endpoints.
"""

from .router import router
from .writing_analyzer import WritingAnalyzer
from .task_generator import WritingTaskGenerator

__all__ = ["router", "WritingAnalyzer", "WritingTaskGenerator"]
