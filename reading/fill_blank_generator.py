"""
Reading Practice - Fill in the Blank Question Generator
Generates fill-in-the-blank questions based on reading texts using Together AI.
"""

import json
import os
import re
from typing import Optional, List
from dataclasses import dataclass
from enum import Enum
from together import Together

from cefr_config import CEFRLevel as FillBlankDifficulty, get_assessment_prompt, get_cefr_spec


@dataclass
class FillBlankOption:
    """Represents a single option for fill-in-the-blank question."""
    label: str  # A, B, C, D
    text: str
    is_correct: bool


@dataclass
class FillBlankQuestion:
    """Represents a single fill-in-the-blank question."""
    question_number: int
    sentence_with_blank: str  # The sentence with _____ for the blank
    complete_sentence: str    # The complete sentence with the answer
    options: List[FillBlankOption]
    correct_answer: str       # A, B, C, or D
    correct_word: str         # The actual word that fills the blank
    explanation: str          # Why the correct answer is correct


@dataclass
class GeneratedFillBlankQuestions:
    """Represents the complete generated fill-in-the-blank questions response."""
    reading_text: str
    difficulty: str
    question_count: int
    questions: List[FillBlankQuestion]
    
    def to_dict(self) -> dict:
        return {
            "reading_text": self.reading_text,
            "difficulty": self.difficulty,
            "question_count": self.question_count,
            "questions": [
                {
                    "question_number": q.question_number,
                    "sentence_with_blank": q.sentence_with_blank,
                    "complete_sentence": q.complete_sentence,
                    "options": [
                        {
                            "label": opt.label,
                            "text": opt.text,
                            "is_correct": opt.is_correct
                        }
                        for opt in q.options
                    ],
                    "correct_answer": q.correct_answer,
                    "correct_word": q.correct_word,
                    "explanation": q.explanation
                }
                for q in self.questions
            ]
        }


class FillBlankGenerator:
    """
    Generates fill-in-the-blank questions based on reading texts using Together AI.
    """
    
    MODEL = "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo"
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the fill-in-the-blank generator."""
        self.api_key = api_key or os.getenv("TOGETHER_API_KEY")
        if not self.api_key:
            raise ValueError("Together API key is required.")
        
        self.client = Together(api_key=self.api_key)
    
    def _get_difficulty_instruction(self, difficulty: FillBlankDifficulty) -> str:
        """Get instructions based on CEFR difficulty level."""
        spec = get_cefr_spec(difficulty.value)
        vocab = spec["vocabulary"]
        assess = spec["assessment"]
        return f"""CEFR Level: {difficulty.value} - {spec['label']}
- Vocabulary level: {vocab['description']}
- Example words: {vocab['examples']}
- Restrictions: {vocab['restrictions']}
- Blanks per question: {assess['blanks_per_question']}
- Distractor quality: {assess['distractors']}"""
    
    def _build_prompt(
        self,
        reading_text: str,
        difficulty: FillBlankDifficulty,
        question_count: int,
        additional_instructions: Optional[str] = None
    ) -> str:
        """Build the prompt for fill-in-the-blank question generation."""
        
        difficulty_instructions = self._get_difficulty_instruction(difficulty)
        
        additional_section = ""
        if additional_instructions:
            additional_section = f"""
**Additional Requirements:**
{additional_instructions}
"""
        
        prompt = f"""You are an expert English language assessment designer. Your task is to create fill-in-the-blank vocabulary questions based on the given reading text.

**Reading Text:**
{reading_text}

**Difficulty Level:** {difficulty.value}
{difficulty_instructions}

**Number of Questions:** {question_count}
{additional_section}

**IMPORTANT RULES:**
1. Create sentences that are relevant to the reading text's topic and context
2. Each question should have a sentence with ONE blank (represented as _____)
3. Provide exactly 4 options (A, B, C, D) for each blank
4. Only ONE option should be grammatically and contextually correct
5. Distractors should be the same part of speech as the correct answer
6. The blank should test vocabulary knowledge, not grammar
7. Vary the position of correct answers across questions
8. Write all content in English

**OUTPUT FORMAT:**
Return a valid JSON object with the following structure:
{{
    "questions": [
        {{
            "question_number": 1,
            "sentence_with_blank": "The scientist conducted extensive _____ on climate patterns.",
            "complete_sentence": "The scientist conducted extensive research on climate patterns.",
            "options": [
                {{"label": "A", "text": "research", "is_correct": true}},
                {{"label": "B", "text": "playing", "is_correct": false}},
                {{"label": "C", "text": "sleeping", "is_correct": false}},
                {{"label": "D", "text": "eating", "is_correct": false}}
            ],
            "correct_answer": "A",
            "correct_word": "research",
            "explanation": "Research is the correct word because it fits the context of scientific study."
        }}
    ]
}}

Generate exactly {question_count} questions. Return ONLY the JSON object, no additional text."""
        
        return prompt
    
    def _parse_response(self, response_text: str, reading_text: str, difficulty: str, question_count: int) -> GeneratedFillBlankQuestions:
        """Parse the LLM response into structured question objects."""
        
        json_match = re.search(r'\{[\s\S]*\}', response_text)
        if not json_match:
            raise ValueError("Could not find valid JSON in the response")
        
        json_str = json_match.group()
        
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse JSON response: {e}")
        
        if "questions" not in data:
            raise ValueError("Response does not contain 'questions' field")
        
        questions = []
        for q_data in data["questions"]:
            options = []
            for opt in q_data.get("options", []):
                options.append(FillBlankOption(
                    label=opt.get("label", ""),
                    text=opt.get("text", ""),
                    is_correct=opt.get("is_correct", False)
                ))
            
            questions.append(FillBlankQuestion(
                question_number=q_data.get("question_number", len(questions) + 1),
                sentence_with_blank=q_data.get("sentence_with_blank", ""),
                complete_sentence=q_data.get("complete_sentence", ""),
                options=options,
                correct_answer=q_data.get("correct_answer", ""),
                correct_word=q_data.get("correct_word", ""),
                explanation=q_data.get("explanation", "")
            ))
        
        return GeneratedFillBlankQuestions(
            reading_text=reading_text,
            difficulty=difficulty,
            question_count=len(questions),
            questions=questions
        )
    
    def generate_questions(
        self,
        reading_text: str,
        difficulty: FillBlankDifficulty = FillBlankDifficulty.B1,
        question_count: int = 5,
        additional_instructions: Optional[str] = None
    ) -> GeneratedFillBlankQuestions:
        """
        Generate fill-in-the-blank questions based on a reading text.
        
        Args:
            reading_text: The reading passage to base questions on
            difficulty: The difficulty level for the questions
            question_count: Number of questions to generate (1-10)
            additional_instructions: Optional additional requirements
            
        Returns:
            GeneratedFillBlankQuestions object containing all generated questions
        """
        
        if not reading_text or len(reading_text.strip()) < 50:
            raise ValueError("Reading text must be at least 50 characters long")
        
        if question_count < 1 or question_count > 10:
            raise ValueError("Question count must be between 1 and 10")
        
        prompt = self._build_prompt(
            reading_text=reading_text,
            difficulty=difficulty,
            question_count=question_count,
            additional_instructions=additional_instructions
        )
        
        try:
            response = self.client.chat.completions.create(
                model=self.MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert English language assessment designer. You always respond with valid JSON."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=4000
            )
            
            response_text = response.choices[0].message.content
            
        except Exception as e:
            raise RuntimeError(f"Failed to generate questions from LLM: {e}")
        
        return self._parse_response(
            response_text=response_text,
            reading_text=reading_text,
            difficulty=difficulty.value,
            question_count=question_count
        )
