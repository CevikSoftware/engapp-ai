"""
Reading Practice - Sentence Builder Question Generator
Generates sentence building/ordering questions based on reading texts using Together AI.
User needs to arrange scrambled words to form a correct sentence.
"""

import json
import os
import re
import random
from typing import Optional, List
from dataclasses import dataclass
from enum import Enum
from together import Together

from cefr_config import CEFRLevel as SentenceBuilderDifficulty, get_cefr_spec


@dataclass
class SentenceBuilderQuestion:
    """Represents a single sentence building question."""
    question_number: int
    correct_sentence: str           # The complete correct sentence
    scrambled_words: List[str]      # Words in scrambled order
    word_count: int                 # Number of words in the sentence
    hint: Optional[str] = None      # Optional hint for the user


@dataclass
class GeneratedSentenceBuilderQuestions:
    """Represents the complete generated sentence builder questions response."""
    reading_text: str
    difficulty: str
    question_count: int
    questions: List[SentenceBuilderQuestion]
    
    def to_dict(self) -> dict:
        return {
            "reading_text": self.reading_text,
            "difficulty": self.difficulty,
            "question_count": self.question_count,
            "questions": [
                {
                    "question_number": q.question_number,
                    "correct_sentence": q.correct_sentence,
                    "scrambled_words": q.scrambled_words,
                    "word_count": q.word_count,
                    "hint": q.hint
                }
                for q in self.questions
            ]
        }


class SentenceBuilderGenerator:
    """
    Generates sentence building questions based on reading texts using Together AI.
    Creates sentences that users must reconstruct from scrambled words.
    """
    
    MODEL = "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo"
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the sentence builder generator."""
        self.api_key = api_key or os.getenv("TOGETHER_API_KEY")
        if not self.api_key:
            raise ValueError("Together API key is required.")
        
        self.client = Together(api_key=self.api_key)
    
    def _get_difficulty_instruction(self, difficulty: SentenceBuilderDifficulty) -> str:
        """Get instructions based on CEFR difficulty level."""
        spec = get_cefr_spec(difficulty.value)
        assess = spec["assessment"]
        grammar = spec["grammar"]
        sent = spec["sentence_length"]
        return f"""CEFR Level: {difficulty.value} - {spec['label']}
- Create sentences with {assess['builder_words']}
- Target sentence length: {sent['words_per_sentence']}
- Allowed grammar: {grammar['tenses']}
- Structures: {grammar['structures']}
- Restrictions: {grammar['restrictions']}"""
    
    def _scramble_words(self, sentence: str) -> List[str]:
        """Scramble the words in a sentence."""
        # Remove punctuation for scrambling, but keep track of it
        words = sentence.split()
        
        # Clean words but preserve original for display
        cleaned_words = []
        for word in words:
            # Keep the word as-is (including punctuation attached)
            cleaned_words.append(word)
        
        # Shuffle until we get a different order
        scrambled = cleaned_words.copy()
        attempts = 0
        while scrambled == cleaned_words and attempts < 10:
            random.shuffle(scrambled)
            attempts += 1
        
        return scrambled
    
    def _build_prompt(
        self,
        reading_text: str,
        difficulty: SentenceBuilderDifficulty,
        question_count: int,
        additional_instructions: Optional[str] = None
    ) -> str:
        """Build the prompt for sentence builder question generation."""
        
        difficulty_instructions = self._get_difficulty_instruction(difficulty)
        
        additional_section = ""
        if additional_instructions:
            additional_section = f"""
**Additional Requirements:**
{additional_instructions}
"""
        
        prompt = f"""You are an expert English language assessment designer. Your task is to create sentence building exercises based on the given reading text.

**Reading Text:**
{reading_text}

**Difficulty Level:** {difficulty.value}
{difficulty_instructions}

**Number of Questions:** {question_count}
{additional_section}

**IMPORTANT RULES:**
1. Create sentences that are relevant to the reading text's topic and context
2. Each sentence should be grammatically correct and natural
3. Sentences should be appropriate for the difficulty level
4. Include a helpful hint for each sentence
5. Write all sentences in English
6. Make sure sentences are meaningful and educational

**OUTPUT FORMAT:**
Return a valid JSON object with the following structure:
{{
    "questions": [
        {{
            "question_number": 1,
            "correct_sentence": "The scientist studies climate change.",
            "hint": "This sentence is about a researcher's work."
        }},
        {{
            "question_number": 2,
            "correct_sentence": "Global temperatures have increased significantly.",
            "hint": "This sentence describes a change in weather patterns."
        }}
    ]
}}

Generate exactly {question_count} sentences. Return ONLY the JSON object, no additional text."""
        
        return prompt
    
    def _parse_response(self, response_text: str, reading_text: str, difficulty: str, question_count: int) -> GeneratedSentenceBuilderQuestions:
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
            correct_sentence = q_data.get("correct_sentence", "")
            scrambled_words = self._scramble_words(correct_sentence)
            
            questions.append(SentenceBuilderQuestion(
                question_number=q_data.get("question_number", len(questions) + 1),
                correct_sentence=correct_sentence,
                scrambled_words=scrambled_words,
                word_count=len(scrambled_words),
                hint=q_data.get("hint")
            ))
        
        return GeneratedSentenceBuilderQuestions(
            reading_text=reading_text,
            difficulty=difficulty,
            question_count=len(questions),
            questions=questions
        )
    
    def generate_questions(
        self,
        reading_text: str,
        difficulty: SentenceBuilderDifficulty = SentenceBuilderDifficulty.B1,
        question_count: int = 5,
        additional_instructions: Optional[str] = None
    ) -> GeneratedSentenceBuilderQuestions:
        """
        Generate sentence building questions based on a reading text.
        
        Args:
            reading_text: The reading passage to base sentences on
            difficulty: The difficulty level for the sentences
            question_count: Number of questions to generate (1-10)
            additional_instructions: Optional additional requirements
            
        Returns:
            GeneratedSentenceBuilderQuestions object containing all generated questions
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
