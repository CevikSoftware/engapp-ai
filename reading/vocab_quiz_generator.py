"""
Reading Practice - Vocabulary Audio Quiz Generator
Generates vocabulary questions with audio pronunciation, phonetic transcription,
and Turkish meaning options using Together AI and TTS.
"""

import json
import os
import re
import io
import base64
from typing import Optional, List
from dataclasses import dataclass
from enum import Enum
from together import Together

from cefr_config import CEFRLevel as VocabQuizDifficulty, get_cefr_spec

# Try to import TTS libraries
try:
    import piper
    PIPER_AVAILABLE = True
except ImportError:
    PIPER_AVAILABLE = False

try:
    from gtts import gTTS
    GTTS_AVAILABLE = True
except ImportError:
    GTTS_AVAILABLE = False

try:
    import eng_to_ipa as ipa
    IPA_AVAILABLE = True
except ImportError:
    IPA_AVAILABLE = False


@dataclass
class VocabOption:
    """Represents a single option for vocabulary quiz."""
    label: str  # A, B, C, D
    text: str   # Turkish meaning
    is_correct: bool


@dataclass
class VocabQuizQuestion:
    """Represents a single vocabulary audio quiz question."""
    question_number: int
    english_word: str           # The English word
    phonetic: str               # IPA phonetic transcription
    audio_base64: Optional[str] # Base64 encoded audio (if TTS available)
    audio_format: str           # Audio format (mp3, wav, etc.)
    options: List[VocabOption]  # 4 options with Turkish meanings
    correct_answer: str         # A, B, C, or D
    correct_meaning: str        # The correct Turkish meaning
    example_sentence: str       # Example sentence using the word
    word_type: str              # noun, verb, adjective, etc.


@dataclass
class GeneratedVocabQuizQuestions:
    """Represents the complete generated vocabulary quiz response."""
    difficulty: str
    question_count: int
    questions: List[VocabQuizQuestion]
    
    def to_dict(self) -> dict:
        return {
            "difficulty": self.difficulty,
            "question_count": self.question_count,
            "questions": [
                {
                    "question_number": q.question_number,
                    "english_word": q.english_word,
                    "phonetic": q.phonetic,
                    "audio_base64": q.audio_base64,
                    "audio_format": q.audio_format,
                    "options": [
                        {
                            "label": opt.label,
                            "text": opt.text,
                            "is_correct": opt.is_correct
                        }
                        for opt in q.options
                    ],
                    "correct_answer": q.correct_answer,
                    "correct_meaning": q.correct_meaning,
                    "example_sentence": q.example_sentence,
                    "word_type": q.word_type
                }
                for q in self.questions
            ]
        }


class VocabQuizGenerator:
    """
    Generates vocabulary audio quiz questions using Together AI and TTS.
    Creates questions where users hear a word and select its Turkish meaning.
    """
    
    MODEL = "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo"
    
    def __init__(self, api_key: Optional[str] = None, tts_model_path: Optional[str] = None):
        """
        Initialize the vocabulary quiz generator.
        
        Args:
            api_key: Together AI API key
            tts_model_path: Path to Piper TTS model (optional)
        """
        self.api_key = api_key or os.getenv("TOGETHER_API_KEY")
        if not self.api_key:
            raise ValueError("Together API key is required.")
        
        self.client = Together(api_key=self.api_key)
        self.tts_model_path = tts_model_path
    
    def _get_phonetic(self, word: str) -> str:
        """Get IPA phonetic transcription for a word."""
        if IPA_AVAILABLE:
            try:
                phonetic = ipa.convert(word)
                return f"/{phonetic}/"
            except:
                pass
        
        # Fallback: Return a placeholder
        return f"[{word}]"
    
    def _generate_audio(self, word: str) -> tuple:
        """
        Generate audio pronunciation for a word.
        
        Returns:
            Tuple of (base64_audio, format) or (None, None) if TTS unavailable
        """
        # Try gTTS first (more reliable, requires internet)
        if GTTS_AVAILABLE:
            try:
                tts = gTTS(text=word, lang='en', slow=False)
                audio_buffer = io.BytesIO()
                tts.write_to_fp(audio_buffer)
                audio_buffer.seek(0)
                audio_base64 = base64.b64encode(audio_buffer.read()).decode('utf-8')
                return audio_base64, "mp3"
            except Exception as e:
                print(f"gTTS failed: {e}")
        
        # Try Piper TTS (offline)
        if PIPER_AVAILABLE and self.tts_model_path:
            try:
                # Piper TTS implementation would go here
                pass
            except Exception as e:
                print(f"Piper TTS failed: {e}")
        
        return None, "none"
    
    def _get_difficulty_instruction(self, difficulty: VocabQuizDifficulty) -> str:
        """Get vocabulary selection instructions based on CEFR difficulty level."""
        spec = get_cefr_spec(difficulty.value)
        vocab = spec["vocabulary"]
        assess = spec["assessment"]
        return f"""CEFR Level: {difficulty.value} - {spec['label']}
- Vocabulary level: {assess['vocab_level']}
- Description: {vocab['description']}
- Word count range: {vocab['word_count_range']}
- Example words: {vocab['examples']}
- Restrictions: {vocab['restrictions']}"""
    
    def _build_prompt(
        self,
        difficulty: VocabQuizDifficulty,
        question_count: int,
        word_list: Optional[List[str]] = None,
        topic: Optional[str] = None,
        additional_instructions: Optional[str] = None
    ) -> str:
        """Build the prompt for vocabulary quiz generation."""
        
        difficulty_instructions = self._get_difficulty_instruction(difficulty)
        
        word_list_section = ""
        if word_list:
            word_list_section = f"""
**Use these specific words:**
{', '.join(word_list)}
"""
        
        topic_section = ""
        if topic:
            topic_section = f"""
**Topic/Theme:** {topic}
Generate vocabulary related to this topic.
"""
        
        additional_section = ""
        if additional_instructions:
            additional_section = f"""
**Additional Requirements:**
{additional_instructions}
"""
        
        prompt = f"""You are an expert English-Turkish language teacher. Create vocabulary quiz questions where students hear an English word and must select its Turkish meaning.

**Difficulty Level:** {difficulty.value}
{difficulty_instructions}

**Number of Questions:** {question_count}
{word_list_section}
{topic_section}
{additional_section}

**IMPORTANT RULES:**
1. Each question should have exactly ONE English word
2. Provide exactly 4 Turkish meaning options (A, B, C, D)
3. Only ONE option should be the correct Turkish meaning
4. Wrong options should be plausible (same category) but clearly incorrect
5. Include an example sentence for each word
6. Specify the word type (noun, verb, adjective, adverb, etc.)
7. Wrong options should be Turkish words, not random text
8. Make sure Turkish translations are accurate

**OUTPUT FORMAT:**
Return a valid JSON object with the following structure:
{{
    "questions": [
        {{
            "question_number": 1,
            "english_word": "apple",
            "word_type": "noun",
            "correct_meaning": "elma",
            "wrong_meanings": ["muz", "portakal", "armut"],
            "example_sentence": "I eat an apple every day for breakfast."
        }},
        {{
            "question_number": 2,
            "english_word": "beautiful",
            "word_type": "adjective",
            "correct_meaning": "güzel",
            "wrong_meanings": ["çirkin", "büyük", "küçük"],
            "example_sentence": "The sunset was beautiful last evening."
        }}
    ]
}}

Generate exactly {question_count} vocabulary questions. Return ONLY the JSON object, no additional text."""
        
        return prompt
    
    def _parse_response(
        self,
        response_text: str,
        difficulty: str,
        question_count: int,
        generate_audio: bool = True
    ) -> GeneratedVocabQuizQuestions:
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
        import random
        
        for q_data in data["questions"]:
            english_word = q_data.get("english_word", "")
            correct_meaning = q_data.get("correct_meaning", "")
            wrong_meanings = q_data.get("wrong_meanings", [])[:3]  # Take only 3 wrong options
            
            # Get phonetic transcription
            phonetic = self._get_phonetic(english_word)
            
            # Generate audio if requested
            audio_base64, audio_format = (None, "none")
            if generate_audio:
                audio_base64, audio_format = self._generate_audio(english_word)
            
            # Create options with randomized correct answer position
            all_meanings = [correct_meaning] + wrong_meanings
            random.shuffle(all_meanings)
            
            labels = ["A", "B", "C", "D"]
            options = []
            correct_answer = ""
            
            for i, meaning in enumerate(all_meanings):
                is_correct = meaning == correct_meaning
                if is_correct:
                    correct_answer = labels[i]
                options.append(VocabOption(
                    label=labels[i],
                    text=meaning,
                    is_correct=is_correct
                ))
            
            questions.append(VocabQuizQuestion(
                question_number=q_data.get("question_number", len(questions) + 1),
                english_word=english_word,
                phonetic=phonetic,
                audio_base64=audio_base64,
                audio_format=audio_format,
                options=options,
                correct_answer=correct_answer,
                correct_meaning=correct_meaning,
                example_sentence=q_data.get("example_sentence", ""),
                word_type=q_data.get("word_type", "unknown")
            ))
        
        return GeneratedVocabQuizQuestions(
            difficulty=difficulty,
            question_count=len(questions),
            questions=questions
        )
    
    def generate_questions(
        self,
        difficulty: VocabQuizDifficulty = VocabQuizDifficulty.B1,
        question_count: int = 5,
        word_list: Optional[List[str]] = None,
        topic: Optional[str] = None,
        additional_instructions: Optional[str] = None,
        generate_audio: bool = True
    ) -> GeneratedVocabQuizQuestions:
        """
        Generate vocabulary audio quiz questions.
        
        Args:
            difficulty: The difficulty level for vocabulary selection
            question_count: Number of questions to generate (1-10)
            word_list: Optional specific words to create questions for
            topic: Optional topic to generate vocabulary from
            additional_instructions: Optional additional requirements
            generate_audio: Whether to generate audio pronunciation
            
        Returns:
            GeneratedVocabQuizQuestions object containing all generated questions
        """
        
        if question_count < 1 or question_count > 10:
            raise ValueError("Question count must be between 1 and 10")
        
        prompt = self._build_prompt(
            difficulty=difficulty,
            question_count=question_count,
            word_list=word_list,
            topic=topic,
            additional_instructions=additional_instructions
        )
        
        try:
            response = self.client.chat.completions.create(
                model=self.MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert English-Turkish language teacher. You always respond with valid JSON."
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
            difficulty=difficulty.value,
            question_count=question_count,
            generate_audio=generate_audio
        )
    
    def generate_single_word_quiz(
        self,
        word: str,
        generate_audio: bool = True
    ) -> VocabQuizQuestion:
        """
        Generate a quiz question for a single specific word.
        
        Args:
            word: The English word to create a quiz for
            generate_audio: Whether to generate audio pronunciation
            
        Returns:
            VocabQuizQuestion object for the specified word
        """
        result = self.generate_questions(
            difficulty=VocabQuizDifficulty.B1,
            question_count=1,
            word_list=[word],
            generate_audio=generate_audio
        )
        
        if result.questions:
            return result.questions[0]
        else:
            raise ValueError(f"Failed to generate quiz for word: {word}")
