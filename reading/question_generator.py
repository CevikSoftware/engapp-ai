"""
Reading Practice - Question Generator Module
Generates multiple choice questions based on reading texts using Together AI's Meta-Llama model.
"""

import json
import os
import re
from typing import Optional, List
from dataclasses import dataclass, field
from enum import Enum
from together import Together

from cefr_config import CEFRLevel as QuestionDifficulty, get_assessment_prompt, get_cefr_spec


@dataclass
class QuestionOption:
    """Represents a single option in a multiple choice question."""
    label: str  # A, B, C, D
    text: str
    is_correct: bool


@dataclass
class Question:
    """Represents a single multiple choice question."""
    question_number: int
    question_text: str
    options: List[QuestionOption]
    correct_answer: str  # A, B, C, or D
    explanation: str  # Why the correct answer is correct


@dataclass
class GeneratedQuestions:
    """Represents the complete generated questions response."""
    reading_text: str
    difficulty: str
    question_count: int
    questions: List[Question]
    
    def to_dict(self) -> dict:
        return {
            "reading_text": self.reading_text,
            "difficulty": self.difficulty,
            "question_count": self.question_count,
            "questions": [
                {
                    "question_number": q.question_number,
                    "question_text": q.question_text,
                    "options": [
                        {
                            "label": opt.label,
                            "text": opt.text,
                            "is_correct": opt.is_correct
                        }
                        for opt in q.options
                    ],
                    "correct_answer": q.correct_answer,
                    "explanation": q.explanation
                }
                for q in self.questions
            ]
        }


class QuestionGenerator:
    """
    Generates multiple choice questions based on reading texts using Together AI.
    Designed for English language learning assessment purposes.
    """
    
    MODEL = "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo"
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the question generator.
        
        Args:
            api_key: Together AI API key. If not provided, uses TOGETHER_API_KEY env variable.
        """
        self.api_key = api_key or os.getenv("TOGETHER_API_KEY")
        if not self.api_key:
            raise ValueError("Together API key is required. Set TOGETHER_API_KEY environment variable or pass it directly.")
        
        self.client = Together(api_key=self.api_key)
    
    def _get_difficulty_instruction(self, difficulty: QuestionDifficulty) -> str:
        """Get question complexity instructions based on CEFR difficulty level."""
        return get_assessment_prompt(difficulty.value)
    
    def _build_prompt(
        self,
        reading_text: str,
        difficulty: QuestionDifficulty,
        question_count: int,
        keywords: Optional[List[str]] = None,
        additional_instructions: Optional[str] = None
    ) -> str:
        """Build the prompt for question generation."""
        
        difficulty_instructions = self._get_difficulty_instruction(difficulty)
        
        keywords_section = ""
        if keywords:
            keywords_section = f"""
**Focus Keywords/Vocabulary:**
The following words/concepts appear in the text. Consider creating questions that test understanding of these terms or concepts related to them:
{', '.join(keywords)}
"""
        
        additional_section = ""
        if additional_instructions:
            additional_section = f"""
**Additional Requirements:**
{additional_instructions}
"""
        
        prompt = f"""You are an expert English language assessment designer. Your task is to create multiple choice reading comprehension questions based on the given text.

**Reading Text:**
{reading_text}

**Difficulty Level:** {difficulty.value}
{difficulty_instructions}

**Number of Questions:** {question_count}
{keywords_section}
{additional_section}

**IMPORTANT RULES:**
1. Each question MUST have exactly 4 options labeled A, B, C, and D
2. Exactly ONE option must be correct for each question
3. All questions must be answerable from the text content
4. Questions should test reading comprehension, not external knowledge
5. Distractors (wrong options) should be plausible but clearly incorrect
6. Write all questions and options in English
7. Vary the position of correct answers (don't always put correct answer in the same position)
8. Include a brief explanation for why the correct answer is correct

**OUTPUT FORMAT:**
Return a valid JSON object with the following structure:
{{
    "questions": [
        {{
            "question_number": 1,
            "question_text": "What is the main idea of the passage?",
            "options": [
                {{"label": "A", "text": "Option A text", "is_correct": false}},
                {{"label": "B", "text": "Option B text", "is_correct": true}},
                {{"label": "C", "text": "Option C text", "is_correct": false}},
                {{"label": "D", "text": "Option D text", "is_correct": false}}
            ],
            "correct_answer": "B",
            "explanation": "Brief explanation of why B is correct"
        }}
    ]
}}

Generate exactly {question_count} questions. Return ONLY the JSON object, no additional text."""
        
        return prompt
    
    def _parse_response(self, response_text: str, reading_text: str, difficulty: str, question_count: int) -> GeneratedQuestions:
        """Parse the LLM response into structured question objects."""
        
        # Try to extract JSON from the response
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
                options.append(QuestionOption(
                    label=opt.get("label", ""),
                    text=opt.get("text", ""),
                    is_correct=opt.get("is_correct", False)
                ))
            
            questions.append(Question(
                question_number=q_data.get("question_number", len(questions) + 1),
                question_text=q_data.get("question_text", ""),
                options=options,
                correct_answer=q_data.get("correct_answer", ""),
                explanation=q_data.get("explanation", "")
            ))
        
        return GeneratedQuestions(
            reading_text=reading_text,
            difficulty=difficulty,
            question_count=len(questions),
            questions=questions
        )
    
    def generate_questions(
        self,
        reading_text: str,
        difficulty: QuestionDifficulty = QuestionDifficulty.B1,
        question_count: int = 5,
        keywords: Optional[List[str]] = None,
        additional_instructions: Optional[str] = None
    ) -> GeneratedQuestions:
        """
        Generate multiple choice questions based on a reading text.
        
        Args:
            reading_text: The reading passage to generate questions about
            difficulty: The difficulty level for the questions
            question_count: Number of questions to generate (1-10)
            keywords: Optional list of keywords/vocabulary from the text to focus on
            additional_instructions: Optional additional requirements for question generation
            
        Returns:
            GeneratedQuestions object containing all generated questions
        """
        
        # Validate inputs
        if not reading_text or len(reading_text.strip()) < 50:
            raise ValueError("Reading text must be at least 50 characters long")
        
        if question_count < 1 or question_count > 10:
            raise ValueError("Question count must be between 1 and 10")
        
        # Build the prompt
        prompt = self._build_prompt(
            reading_text=reading_text,
            difficulty=difficulty,
            question_count=question_count,
            keywords=keywords,
            additional_instructions=additional_instructions
        )
        
        # Call the LLM
        try:
            response = self.client.chat.completions.create(
                model=self.MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert English language assessment designer specializing in creating reading comprehension questions. You always respond with valid JSON."
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
        
        # Parse and return the response
        return self._parse_response(
            response_text=response_text,
            reading_text=reading_text,
            difficulty=difficulty.value,
            question_count=question_count
        )


# Standalone function for easy use
def generate_questions(
    reading_text: str,
    difficulty: str = "B1",
    question_count: int = 5,
    keywords: Optional[List[str]] = None,
    additional_instructions: Optional[str] = None,
    api_key: Optional[str] = None
) -> dict:
    """
    Generate multiple choice questions based on a reading text.
    
    This is a convenience function that creates a QuestionGenerator instance
    and generates questions in one call.
    
    Args:
        reading_text: The reading passage to generate questions about
        difficulty: The difficulty level (beginner, elementary, intermediate, upper_intermediate, advanced)
        question_count: Number of questions to generate (1-10)
        keywords: Optional list of keywords/vocabulary from the text
        additional_instructions: Optional additional requirements
        api_key: Together AI API key (optional if TOGETHER_API_KEY env var is set)
        
    Returns:
        Dictionary containing generated questions
    """
    generator = QuestionGenerator(api_key=api_key)
    
    difficulty_enum = QuestionDifficulty(difficulty.lower())
    
    result = generator.generate_questions(
        reading_text=reading_text,
        difficulty=difficulty_enum,
        question_count=question_count,
        keywords=keywords,
        additional_instructions=additional_instructions
    )
    
    return result.to_dict()


if __name__ == "__main__":
    # Test the question generator
    sample_text = """
    Climate change is one of the most pressing issues facing our planet today. 
    Scientists have observed significant changes in global temperatures over the past century, 
    with the average temperature rising by approximately 1.1 degrees Celsius since the pre-industrial era.
    
    The main cause of this warming is the increased concentration of greenhouse gases in the atmosphere, 
    primarily carbon dioxide from burning fossil fuels. These gases trap heat from the sun, 
    creating a "greenhouse effect" that warms the Earth's surface.
    
    The effects of climate change are already visible around the world. Glaciers are melting, 
    sea levels are rising, and extreme weather events are becoming more frequent and severe. 
    Many species are struggling to adapt to these rapid changes in their environments.
    
    To address this crisis, governments and organizations worldwide are working to reduce 
    greenhouse gas emissions and transition to renewable energy sources. Individual actions, 
    such as reducing energy consumption and using public transportation, also play an important role 
    in the fight against climate change.
    """
    
    try:
        result = generate_questions(
            reading_text=sample_text,
            difficulty="B1",
            question_count=3,
            keywords=["climate change", "greenhouse gases", "renewable energy"]
        )
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"Error: {e}")
