"""
Writing Task Generator
Generates writing tasks based on given topics and requirements.
"""

import json
import os
import re
from typing import Optional, List
from dataclasses import dataclass
from together import Together

from cefr_config import get_difficulty_prompt, get_cefr_spec


@dataclass
class WritingTask:
    """Represents a generated writing task."""
    task_instruction: str
    topic: str
    writing_type: Optional[str]
    target_tense: Optional[str]
    target_vocabulary: Optional[List[str]]
    target_grammar: Optional[List[str]]
    additional_details: Optional[str]
    tips: List[str]
    suggested_word_count: int
    
    def to_dict(self) -> dict:
        return {
            "task_instruction": self.task_instruction,
            "topic": self.topic,
            "writing_type": self.writing_type,
            "target_tense": self.target_tense,
            "target_vocabulary": self.target_vocabulary,
            "additional_details": self.additional_details,
            "tips": self.tips,
            "suggested_word_count": self.suggested_word_count
        }


class WritingTaskGenerator:
    """
    Generates writing tasks using Together AI.
    """
    
    MODEL = "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo"
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the generator with API key."""
        self.api_key = api_key or os.getenv("TOGETHER_API_KEY")
        if not self.api_key:
            raise ValueError("TOGETHER_API_KEY is required")
        self.client = Together(api_key=self.api_key)
    
    def _build_task_prompt(
        self,
        topic: str,
        writing_type: Optional[str] = None,
        target_tense: Optional[str] = None,
        target_vocabulary: Optional[List[str]] = None,
        target_grammar: Optional[List[str]] = None,
        additional_details: Optional[str] = None,
        difficulty: str = "B1",
        rag_context: Optional[str] = None
    ) -> str:
        """Build the prompt for task generation."""
        
        # Get CEFR-specific difficulty instructions
        cefr_instructions = get_difficulty_prompt(difficulty)
        spec = get_cefr_spec(difficulty)
        
        prompt = f"""You are an English writing teacher creating a writing task for a student.

{cefr_instructions}

Create a clear, engaging writing task based on the following:

TOPIC: {topic}
"""
        
        if writing_type:
            prompt += f"WRITING TYPE: {writing_type}\n"
        
        if target_tense:
            prompt += f"TARGET TENSE: {target_tense} (the student should practice using this tense)\n"
        
        if target_vocabulary:
            prompt += f"""⚠️ MANDATORY TARGET VOCABULARY: {', '.join(target_vocabulary)}
CRITICAL: The writing task MUST explicitly require the student to use these vocabulary words. Include them in the task description or instructions. The student should use at least 70-80% of these words in their writing. State this requirement clearly in the task.
"""
        
        if target_grammar:
            prompt += f"""⚠️ MANDATORY TARGET GRAMMAR STRUCTURES: {', '.join(target_grammar)}
CRITICAL: The writing task MUST explicitly require the student to use ALL of these grammar structures. State clearly in the task instructions that the student must demonstrate each grammar pattern. This is a strict requirement.
"""
        
        if additional_details:
            prompt += f"ADDITIONAL DETAILS: {additional_details}\n"
        
        prompt += f"CEFR LEVEL: {difficulty}\n"
        
        # Calculate suggested word count from CEFR spec
        base_word_count = int(100 * spec.get("text_length_multiplier", 1.0))
        
        prompt += f"""
Generate a response in the following JSON format:
{{
    "task_instruction": "A clear, detailed writing task instruction in English. Be specific about what the student should write.",
    "tips": ["Tip 1 for completing the task", "Tip 2", "Tip 3"],
    "suggested_word_count": {base_word_count}
}}

The task_instruction should:
1. Be written entirely in English
2. Be clear and specific about what to write
3. Give context (who is writing to whom, purpose, etc.)
4. Be appropriate for CEFR {difficulty} level English language learners
5. Use vocabulary and grammar complexity matching the CEFR level

Return ONLY valid JSON, no additional text.
"""

        if rag_context:
            prompt += rag_context + "\n"

        return prompt
    
    def generate_task(
        self,
        topic: str,
        writing_type: Optional[str] = None,
        target_tense: Optional[str] = None,
        target_vocabulary: Optional[List[str]] = None,
        target_grammar: Optional[List[str]] = None,
        additional_details: Optional[str] = None,
        difficulty: str = "B1",
        rag_context: Optional[str] = None
    ) -> WritingTask:
        """Generate a writing task."""
        
        prompt = self._build_task_prompt(
            topic=topic,
            writing_type=writing_type,
            target_tense=target_tense,
            target_vocabulary=target_vocabulary,
            target_grammar=target_grammar,
            additional_details=additional_details,
            difficulty=difficulty,
            rag_context=rag_context
        )
        
        response = self.client.chat.completions.create(
            model=self.MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert English writing teacher. Generate clear, engaging writing tasks for language learners. Always respond with valid JSON only."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            max_tokens=1000,
            temperature=0.7
        )
        
        response_text = response.choices[0].message.content.strip()
        
        # Parse JSON response
        try:
            # Try to extract JSON from the response
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                result = json.loads(json_match.group())
            else:
                result = json.loads(response_text)
        except json.JSONDecodeError:
            # Fallback if JSON parsing fails
            result = {
                "task_instruction": f"Write a {writing_type or 'text'} about: {topic}",
                "tips": ["Be clear and organized", "Use appropriate vocabulary", "Check your grammar"],
                "suggested_word_count": 150
            }
        
        return WritingTask(
            task_instruction=result.get("task_instruction", f"Write about: {topic}"),
            topic=topic,
            writing_type=writing_type,
            target_tense=target_tense,
            target_vocabulary=target_vocabulary,
            target_grammar=target_grammar,
            additional_details=additional_details,
            tips=result.get("tips", []),
            suggested_word_count=result.get("suggested_word_count", 150)
        )
