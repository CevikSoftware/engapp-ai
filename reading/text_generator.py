"""
Reading Practice - Text Generator Module
Generates educational English reading texts using Together AI's Meta-Llama model.
"""

import json
import os
import re
from typing import Optional, List
from dataclasses import dataclass
from enum import Enum
from together import Together

from cefr_config import CEFRLevel as DifficultyLevel, get_difficulty_prompt, get_cefr_spec


class TextLength(str, Enum):
    SHORT = "short"          # 50-100 words
    MEDIUM = "medium"        # 150-250 words
    LONG = "long"            # 300-500 words
    VERY_LONG = "very_long"  # 500-800 words


class ContentType(str, Enum):
    ARTICLE = "article"
    STORY = "story"
    EMAIL = "email"
    LETTER = "letter"
    ESSAY = "essay"
    DIALOGUE = "dialogue"
    DESCRIPTION = "description"
    INSTRUCTIONS = "instructions"
    REVIEW = "review"
    REPORT = "report"


class WritingStyle(str, Enum):
    FORMAL = "formal"
    INFORMAL = "informal"
    NEUTRAL = "neutral"
    ACADEMIC = "academic"
    CONVERSATIONAL = "conversational"
    PROFESSIONAL = "professional"


class TensePreference(str, Enum):
    PAST = "past"
    PRESENT = "present"
    FUTURE = "future"
    MIXED = "mixed"
    NARRATIVE = "narrative"


@dataclass
class GeneratedText:
    """Represents a generated reading text."""
    concept: str
    content_type: str
    difficulty: str
    length: str
    title: str
    text: str
    word_count: int
    required_words_used: List[str]
    required_words_missing: List[str]
    writing_style: Optional[str] = None
    tense_preference: Optional[str] = None
    
    def to_dict(self) -> dict:
        return {
            "concept": self.concept,
            "content_type": self.content_type,
            "difficulty": self.difficulty,
            "length": self.length,
            "title": self.title,
            "text": self.text,
            "word_count": self.word_count,
            "required_words_used": self.required_words_used,
            "required_words_missing": self.required_words_missing,
            "writing_style": self.writing_style,
            "tense_preference": self.tense_preference
        }


class TextGenerator:
    """
    Generates educational English reading texts using Together AI.
    Designed for English language learning purposes.
    """
    
    MODEL = "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo"
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the text generator.
        
        Args:
            api_key: Together AI API key. If not provided, uses TOGETHER_API_KEY env variable.
        """
        self.api_key = api_key or os.getenv("TOGETHER_API_KEY")
        if not self.api_key:
            raise ValueError("Together API key is required. Set TOGETHER_API_KEY environment variable or pass it directly.")
        
        self.client = Together(api_key=self.api_key)
    
    def _get_length_instruction(self, length: TextLength) -> tuple:
        """Get the word count range for the given length."""
        length_map = {
            TextLength.SHORT: (50, 100),
            TextLength.MEDIUM: (150, 250),
            TextLength.LONG: (300, 500),
            TextLength.VERY_LONG: (500, 800)
        }
        return length_map.get(length, length_map[TextLength.MEDIUM])
    
    def _get_difficulty_instruction(self, difficulty: DifficultyLevel) -> str:
        """Get vocabulary and grammar instructions based on CEFR difficulty level."""
        return get_difficulty_prompt(difficulty.value)
    
    def _get_content_type_instruction(self, content_type: ContentType) -> str:
        """Get format instructions based on content type."""
        content_map = {
            ContentType.ARTICLE: "Write a news article or blog post with a headline, introduction, body paragraphs, and conclusion.",
            ContentType.STORY: "Write a short narrative story with a beginning, middle, and end. Include characters, setting, and a plot.",
            ContentType.EMAIL: "Write an email with appropriate greeting, body, and closing. Include subject line context.",
            ContentType.LETTER: "Write a letter with proper greeting, body paragraphs, and formal/informal closing as appropriate.",
            ContentType.ESSAY: "Write an essay with clear introduction, body paragraphs with topic sentences, and conclusion.",
            ContentType.DIALOGUE: "Write a conversation between two or more people with realistic exchanges and natural flow.",
            ContentType.DESCRIPTION: "Write a descriptive text that paints a vivid picture using sensory details and descriptive language.",
            ContentType.INSTRUCTIONS: "Write step-by-step instructions or a how-to guide with clear, actionable steps.",
            ContentType.REVIEW: "Write a review with opinions, evaluations, and recommendations about a product, service, or experience.",
            ContentType.REPORT: "Write a report with factual information, organized sections, and objective analysis."
        }
        return content_map.get(content_type, content_map[ContentType.ARTICLE])
    
    def _get_style_instruction(self, style: Optional[WritingStyle]) -> str:
        """Get writing style instructions."""
        if style is None:
            return ""
        
        style_map = {
            WritingStyle.FORMAL: "Use formal language, avoid contractions, use passive voice where appropriate, maintain professional tone.",
            WritingStyle.INFORMAL: "Use casual language, include contractions, use active voice, maintain friendly conversational tone.",
            WritingStyle.NEUTRAL: "Use balanced language that is neither too formal nor too casual, appropriate for general audiences.",
            WritingStyle.ACADEMIC: "Use academic language with precise terminology, formal structure, and objective tone.",
            WritingStyle.CONVERSATIONAL: "Write as if speaking to a friend, use rhetorical questions, include personal anecdotes.",
            WritingStyle.PROFESSIONAL: "Use business-appropriate language, be concise and clear, maintain respectful tone."
        }
        return f"\nWRITING STYLE: {style_map.get(style, '')}"
    
    def _get_tense_instruction(self, tense: Optional[TensePreference]) -> str:
        """Get tense preference instructions."""
        if tense is None:
            return ""
        
        tense_map = {
            TensePreference.PAST: "Focus primarily on past tenses (simple past, past continuous, past perfect).",
            TensePreference.PRESENT: "Focus primarily on present tenses (simple present, present continuous, present perfect).",
            TensePreference.FUTURE: "Focus primarily on future forms (will, going to, present continuous for future).",
            TensePreference.MIXED: "Use a natural mix of tenses as appropriate for the content.",
            TensePreference.NARRATIVE: "Use narrative tenses: past simple for main events, past continuous for background, past perfect for earlier events."
        }
        return f"\nTENSE FOCUS: {tense_map.get(tense, '')}"
    
    def _build_system_prompt(self) -> str:
        """Build the system prompt for the text generator."""
        return """You are an expert English language teaching assistant specializing in creating educational reading texts for English learners.

Your role is to generate natural, educational texts that help students improve their English reading comprehension and vocabulary.

CRITICAL RULES:
1. You MUST use ALL required words at least once in the text
2. The required words must be used naturally and in context - don't force them
3. Match the difficulty level exactly - vocabulary, grammar, and sentence complexity must be appropriate
4. Stay within the specified word count range
5. Create engaging, educational content that feels natural
6. Include a relevant title for the text
7. Always respond with ONLY valid JSON, no additional text or explanation

OUTPUT FORMAT:
You must respond with a JSON object in this exact format:
{
    "title": "Title of the text",
    "text": "The full generated text here..."
}"""
    
    def _build_user_prompt(
        self,
        concept: str,
        content_type: ContentType,
        difficulty: DifficultyLevel,
        length: TextLength,
        required_words: List[str],
        writing_style: Optional[WritingStyle] = None,
        tense_preference: Optional[TensePreference] = None,
        additional_details: Optional[str] = None,
        target_grammar: Optional[List[str]] = None,
        rag_context: Optional[str] = None
    ) -> str:
        """Build the user prompt for generating a text."""
        
        min_words, max_words = self._get_length_instruction(length)
        difficulty_instruction = self._get_difficulty_instruction(difficulty)
        content_instruction = self._get_content_type_instruction(content_type)
        style_instruction = self._get_style_instruction(writing_style)
        tense_instruction = self._get_tense_instruction(tense_preference)
        
        prompt = f"""Generate an English reading text for language learners with the following specifications:

CONCEPT/TOPIC: {concept}

CONTENT TYPE: {content_type.value}
{content_instruction}

DIFFICULTY LEVEL: {difficulty.value}
Language requirements for this level:
{difficulty_instruction}

WORD COUNT: {min_words}-{max_words} words

REQUIRED WORDS (MUST USE ALL OF THESE AT LEAST ONCE):
{', '.join(required_words)}

IMPORTANT: Every single word in the required words list MUST appear at least once in your text. This is mandatory.
{style_instruction}
{tense_instruction}
"""
        
        if target_grammar:
            prompt += f"""\n⚠️ MANDATORY TARGET GRAMMAR STRUCTURES — YOU MUST USE ALL OF THESE:
{', '.join(target_grammar)}

CRITICAL RULES:
- You MUST use EVERY listed grammar structure at least once in the text.
- Each grammar pattern must appear naturally and in proper context.
- Spread them across different sentences/paragraphs.
- This is a STRICT REQUIREMENT — do NOT skip any grammar structure.
"""
        
        if additional_details:
            prompt += f"""
ADDITIONAL REQUIREMENTS:
{additional_details}
"""
        
        prompt += """
Remember:
- Use ALL required words naturally in context
- Match the difficulty level exactly
- Stay within the word count range
- Make the text engaging and educational
- Return ONLY the JSON object with title and text
"""

        if rag_context:
            prompt += rag_context + "\n"

        prompt += "Generate the text now:"
        
        return prompt
    
    def _check_required_words(self, text: str, required_words: List[str]) -> tuple:
        """
        Check which required words are present in the text.
        Returns (used_words, missing_words)
        """
        text_lower = text.lower()
        used = []
        missing = []
        
        for word in required_words:
            # Check for the word (case-insensitive, whole word match)
            pattern = r'\b' + re.escape(word.lower()) + r'\b'
            if re.search(pattern, text_lower):
                used.append(word)
            else:
                missing.append(word)
        
        return used, missing
    
    def _count_words(self, text: str) -> int:
        """Count words in the text."""
        return len(text.split())
    
    def generate(
        self,
        concept: str,
        content_type: ContentType,
        difficulty: DifficultyLevel,
        length: TextLength,
        required_words: List[str],
        writing_style: Optional[WritingStyle] = None,
        tense_preference: Optional[TensePreference] = None,
        additional_details: Optional[str] = None,
        target_grammar: Optional[List[str]] = None,
        rag_context: Optional[str] = None,
        max_retries: int = 3
    ) -> GeneratedText:
        """
        Generate an educational reading text.
        
        Args:
            concept: The main topic or concept for the text
            content_type: The type of text to generate
            difficulty: The difficulty level
            length: The desired length
            required_words: List of words that must appear in the text
            writing_style: Optional writing style preference
            tense_preference: Optional tense usage preference
            additional_details: Optional additional requirements
            max_retries: Maximum retries if required words are missing
            
        Returns:
            GeneratedText object with the generated content
        """
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(
            concept=concept,
            content_type=content_type,
            difficulty=difficulty,
            length=length,
            required_words=required_words,
            writing_style=writing_style,
            tense_preference=tense_preference,
            additional_details=additional_details,
            target_grammar=target_grammar,
            rag_context=rag_context
        )
        
        last_error = None
        
        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.MODEL,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.7,
                    max_tokens=2000
                )
                
                content = response.choices[0].message.content.strip()
                
                # Clean up the response - remove markdown code blocks if present
                if content.startswith("```"):
                    content = re.sub(r'^```(?:json)?\s*', '', content)
                    content = re.sub(r'\s*```$', '', content)
                
                # Fix JSON control characters in string values
                # Find the text field and properly escape newlines/tabs within it
                def fix_json_string_values(json_str):
                    """Fix unescaped control characters in JSON string values."""
                    result = []
                    in_string = False
                    escape_next = False
                    
                    for char in json_str:
                        if escape_next:
                            result.append(char)
                            escape_next = False
                            continue
                        
                        if char == '\\':
                            result.append(char)
                            escape_next = True
                            continue
                        
                        if char == '"':
                            in_string = not in_string
                            result.append(char)
                            continue
                        
                        if in_string:
                            # Escape control characters inside strings
                            if char == '\n':
                                result.append('\\n')
                            elif char == '\r':
                                result.append('\\r')
                            elif char == '\t':
                                result.append('\\t')
                            elif ord(char) < 32:
                                result.append(f'\\u{ord(char):04x}')
                            else:
                                result.append(char)
                        else:
                            result.append(char)
                    
                    return ''.join(result)
                
                content = fix_json_string_values(content)
                
                # Parse JSON
                data = json.loads(content)
                
                title = data.get("title", "Untitled")
                text = data.get("text", "")
                
                if not text:
                    raise ValueError("Generated text is empty")
                
                # Check required words
                used_words, missing_words = self._check_required_words(text, required_words)
                word_count = self._count_words(text)
                
                # If words are missing and we have retries left, try again with emphasis
                if missing_words and attempt < max_retries - 1:
                    user_prompt += f"\n\nPREVIOUS ATTEMPT FAILED: The following required words were NOT found in your text: {', '.join(missing_words)}. You MUST include these words in the next attempt!"
                    continue
                
                return GeneratedText(
                    concept=concept,
                    content_type=content_type.value,
                    difficulty=difficulty.value,
                    length=length.value,
                    title=title,
                    text=text,
                    word_count=word_count,
                    required_words_used=used_words,
                    required_words_missing=missing_words,
                    writing_style=writing_style.value if writing_style else None,
                    tense_preference=tense_preference.value if tense_preference else None
                )
                
            except json.JSONDecodeError as e:
                last_error = f"Failed to parse AI response as JSON: {str(e)}"
                continue
            except Exception as e:
                last_error = str(e)
                continue
        
        raise ValueError(f"Failed to generate text after {max_retries} attempts. Last error: {last_error}")
