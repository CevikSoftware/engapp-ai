"""
Listening Practice - Conversation Generator Module
Generates educational English conversations using Together AI's Meta-Llama model.
"""

import json
import os
from typing import Optional, List
from dataclasses import dataclass
from enum import Enum
from together import Together

from cefr_config import CEFRLevel as DifficultyLevel, get_difficulty_prompt, get_cefr_spec


class ConversationLength(str, Enum):
    SHORT = "short"      # 4-6 exchanges
    MEDIUM = "medium"    # 8-12 exchanges
    LONG = "long"        # 14-20 exchanges


@dataclass
class DialogueLine:
    """Represents a single line of dialogue."""
    speaker: str
    text: str


@dataclass
class Conversation:
    """Represents a complete conversation."""
    topic: str
    difficulty: str
    character1: str
    character2: str
    dialogue: List[DialogueLine]
    
    def to_dict(self) -> dict:
        return {
            "topic": self.topic,
            "difficulty": self.difficulty,
            "character1": self.character1,
            "character2": self.character2,
            "dialogue": [
                {"speaker": line.speaker, "text": line.text}
                for line in self.dialogue
            ]
        }


class ConversationGenerator:
    """
    Generates educational English conversations using Together AI.
    Designed for English language learning purposes.
    """
    
    MODEL = "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo"
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the conversation generator.
        
        Args:
            api_key: Together AI API key. If not provided, uses TOGETHER_API_KEY env variable.
        """
        self.api_key = api_key or os.getenv("TOGETHER_API_KEY")
        if not self.api_key:
            raise ValueError("Together API key is required. Set TOGETHER_API_KEY environment variable or pass it directly.")
        
        self.client = Together(api_key=self.api_key)
    
    def _get_length_instruction(self, length: ConversationLength, difficulty: DifficultyLevel = None) -> str:
        """Get the instruction for conversation length, adjusted by CEFR level."""
        # Base ranges
        length_map = {
            ConversationLength.SHORT: "4-6 exchanges (8-12 total lines)",
            ConversationLength.MEDIUM: "8-12 exchanges (16-24 total lines)",
            ConversationLength.LONG: "14-20 exchanges (28-40 total lines)"
        }
        base = length_map.get(length, length_map[ConversationLength.MEDIUM])
        
        # If CEFR level provided, use spec-specific exchange counts
        if difficulty:
            try:
                spec = get_cefr_spec(difficulty.value)
                conv = spec["conversation"]
                if length == ConversationLength.SHORT:
                    exchanges = conv["exchanges_short"]
                elif length == ConversationLength.LONG:
                    exchanges = conv["exchanges_long"]
                else:
                    exchanges = conv["exchanges_medium"]
                return f"{exchanges} exchanges"
            except (KeyError, ValueError):
                pass
        
        return base
    
    def _get_difficulty_instruction(self, difficulty: DifficultyLevel) -> str:
        """Get vocabulary and grammar instructions based on CEFR difficulty level."""
        return get_difficulty_prompt(difficulty.value)
    
    def _build_system_prompt(self) -> str:
        """Build the system prompt for the conversation generator."""
        return """You are an expert English language teaching assistant specializing in creating realistic conversation dialogues for listening practice exercises.

Your role is to generate natural, educational conversations that help students improve their English listening comprehension skills.

IMPORTANT RULES:
1. Create natural, realistic dialogues that could happen in real life
2. Ensure the conversation flows logically with proper turn-taking
3. Include natural speech patterns (hesitations, confirmations, reactions)
4. Make sure both characters contribute meaningfully to the conversation
5. The conversation should be educational but not feel like a textbook
6. Always respond with ONLY valid JSON, no additional text or explanation

OUTPUT FORMAT:
You must respond with a JSON object in this exact format:
{
    "dialogue": [
        {"speaker": "CHARACTER1_NAME", "text": "First line of dialogue"},
        {"speaker": "CHARACTER2_NAME", "text": "Response"},
        ...
    ]
}"""
    
    def _build_user_prompt(
        self,
        topic: str,
        difficulty: DifficultyLevel,
        length: ConversationLength,
        character1: str,
        character2: str,
        special_details: Optional[str] = None,
        target_vocabulary: Optional[List[str]] = None,
        target_grammar: Optional[List[str]] = None,
        rag_context: Optional[str] = None
    ) -> str:
        """Build the user prompt for generating a conversation."""
        
        length_instruction = self._get_length_instruction(length, difficulty)
        difficulty_instruction = self._get_difficulty_instruction(difficulty)
        
        prompt = f"""Generate an English conversation for listening practice with the following specifications:

TOPIC: {topic}

CHARACTERS:
- First speaker: {character1}
- Second speaker: {character2}

DIFFICULTY LEVEL: {difficulty.value}
Language requirements for this level:
{difficulty_instruction}

CONVERSATION LENGTH: {length_instruction}

"""
        
        if special_details:
            prompt += f"""SPECIAL DETAILS TO INCLUDE:
{special_details}

"""
        
        if target_vocabulary:
            prompt += f"""⚠️ MANDATORY TARGET VOCABULARY — YOU MUST USE THESE WORDS:
{', '.join(target_vocabulary)}

CRITICAL RULES:
- You MUST use at least 70-80% of the listed vocabulary words in the conversation.
- Ideally use ALL of them. Missing more than 2-3 words is NOT acceptable.
- Each word must be used naturally and in proper context — do NOT just list them.
- If a word cannot fit the conversation topic, adjust the conversation flow to include it.
- This is a STRICT REQUIREMENT, not a suggestion.

"""
        
        if target_grammar:
            prompt += f"""⚠️ MANDATORY TARGET GRAMMAR STRUCTURES — YOU MUST USE ALL OF THESE:
{', '.join(target_grammar)}

CRITICAL RULES:
- You MUST use EVERY listed grammar structure at least once in the conversation.
- Each grammar pattern must appear naturally in dialogue sentences.
- If there are multiple structures, spread them across different parts of the conversation.
- This is a STRICT REQUIREMENT — do NOT skip any grammar structure.

"""
        
        prompt += f"""Remember:
- Start the conversation with {character1}
- Alternate between {character1} and {character2}
- Make the conversation natural and educational
- Return ONLY the JSON object with the dialogue array
"""

        if rag_context:
            prompt += rag_context + "\n"

        prompt += "Generate the conversation now:"
        
        return prompt
    
    def generate(
        self,
        topic: str,
        difficulty: DifficultyLevel,
        length: ConversationLength,
        character1: str,
        character2: str,
        special_details: Optional[str] = None,
        target_vocabulary: Optional[List[str]] = None,
        target_grammar: Optional[List[str]] = None,
        rag_context: Optional[str] = None
    ) -> Conversation:
        """
        Generate an educational English conversation.
        
        Args:
            topic: The topic of the conversation
            difficulty: The difficulty level (CEFR)
            length: The conversation length (short, medium, long)
            character1: Name of the first character (starts the conversation)
            character2: Name of the second character
            special_details: Optional specific details to include in the conversation
            target_vocabulary: Optional list of vocabulary words to use in the conversation
            target_grammar: Optional list of grammar structures to practice
            rag_context: Optional textbook RAG context to inject
            
        Returns:
            Conversation object containing the generated dialogue
        """
        
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(
            topic=topic,
            difficulty=difficulty,
            length=length,
            character1=character1,
            character2=character2,
            special_details=special_details,
            target_vocabulary=target_vocabulary,
            target_grammar=target_grammar,
            rag_context=rag_context
        )
        
        response = self.client.chat.completions.create(
            model=self.MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=2000,
            response_format={"type": "json_object"}
        )
        
        # Parse the response
        response_text = response.choices[0].message.content
        
        try:
            result = json.loads(response_text)
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse LLM response as JSON: {e}")
        
        # Extract dialogue
        dialogue_data = result.get("dialogue", [])
        
        dialogue_lines = [
            DialogueLine(speaker=line["speaker"], text=line["text"])
            for line in dialogue_data
        ]
        
        return Conversation(
            topic=topic,
            difficulty=difficulty.value,
            character1=character1,
            character2=character2,
            dialogue=dialogue_lines
        )


def generate_conversation(
    topic: str,
    difficulty: str,
    length: str,
    character1: str,
    character2: str,
    special_details: Optional[str] = None,
    api_key: Optional[str] = None
) -> dict:
    """
    Convenience function to generate a conversation and return as dictionary.
    
    Args:
        topic: The topic of the conversation
        difficulty: The difficulty level (beginner, elementary, intermediate, upper_intermediate, advanced)
        length: The conversation length (short, medium, long)
        character1: Name of the first character
        character2: Name of the second character
        special_details: Optional specific details to include
        api_key: Optional Together AI API key
        
    Returns:
        Dictionary containing the conversation data
    """
    
    generator = ConversationGenerator(api_key=api_key)
    
    # Convert string to enum
    difficulty_enum = DifficultyLevel(difficulty.lower())
    length_enum = ConversationLength(length.lower())
    
    conversation = generator.generate(
        topic=topic,
        difficulty=difficulty_enum,
        length=length_enum,
        character1=character1,
        character2=character2,
        special_details=special_details
    )
    
    return conversation.to_dict()
