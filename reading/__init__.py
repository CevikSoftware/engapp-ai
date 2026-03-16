"""
Reading Practice Module
Generates educational English reading texts and comprehension questions using AI.
Includes multiple question types: multiple choice, fill-in-the-blank, sentence building, and vocabulary audio quiz.
"""

from .text_generator import TextGenerator, DifficultyLevel, TextLength, ContentType
from .question_generator import QuestionGenerator, QuestionDifficulty, generate_questions
from .fill_blank_generator import FillBlankGenerator, FillBlankDifficulty
from .sentence_builder_generator import SentenceBuilderGenerator, SentenceBuilderDifficulty
from .vocab_quiz_generator import VocabQuizGenerator, VocabQuizDifficulty
from .router import router

__all__ = [
    # Text generation
    "TextGenerator",
    "DifficultyLevel", 
    "TextLength",
    "ContentType",
    # Multiple choice questions
    "QuestionGenerator",
    "QuestionDifficulty",
    "generate_questions",
    # Fill in the blank
    "FillBlankGenerator",
    "FillBlankDifficulty",
    # Sentence builder
    "SentenceBuilderGenerator",
    "SentenceBuilderDifficulty",
    # Vocabulary audio quiz
    "VocabQuizGenerator",
    "VocabQuizDifficulty",
    # Router
    "router"
]
