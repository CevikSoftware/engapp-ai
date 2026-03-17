"""
Listening Practice - Question Generator Module
Generates various types of questions based on dialogue content using Together AI.
Question types: Multiple Choice, Fill in the Blank, Sentence Builder, Vocabulary Quiz
"""

import json
import os
import re
import random
import io
import base64
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from enum import Enum
from together import Together

from cefr_config import CEFRLevel as QuestionDifficulty, get_assessment_prompt, get_cefr_spec

# TTS imports
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


class QuestionType(str, Enum):
    MULTIPLE_CHOICE = "multiple_choice"
    FILL_BLANK = "fill_blank"
    SENTENCE_BUILDER = "sentence_builder"
    VOCABULARY_QUIZ = "vocabulary_quiz"


# ==================== Multiple Choice ====================

@dataclass
class MCOption:
    """Multiple choice option."""
    label: str  # A, B, C, D
    text: str
    is_correct: bool


@dataclass 
class MultipleChoiceQuestion:
    """Multiple choice question based on dialogue."""
    question_number: int
    question_text: str
    options: List[MCOption]
    correct_answer: str
    explanation: str
    related_dialogue: str  # The dialogue line this question is about


# ==================== Fill in the Blank ====================

@dataclass
class BlankInfo:
    """Information about a blank in fill-the-blank question."""
    blank_number: int
    correct_word: str
    position_in_sentence: int


@dataclass
class FillBlankQuestion:
    """Fill in the blank question."""
    question_number: int
    original_sentence: str      # Complete sentence
    sentence_with_blanks: str   # Sentence with ___1___, ___2___ etc.
    blanks: List[BlankInfo]     # Info about each blank
    word_options: List[str]     # All options (correct + distractors)
    correct_words: List[str]    # Just the correct words in order
    speaker: str                # Who said this line


# ==================== Sentence Builder ====================

@dataclass
class SentenceBuilderQuestion:
    """Sentence building/ordering question."""
    question_number: int
    original_sentence: str
    scrambled_words: List[str]
    word_order: List[int]       # Correct order indices
    word_count: int
    speaker: str
    hint: Optional[str] = None


# ==================== Vocabulary Quiz ====================

@dataclass
class VocabOption:
    """Vocabulary quiz option (Turkish meaning)."""
    label: str
    text: str
    is_correct: bool


@dataclass
class VocabularyQuestion:
    """Vocabulary audio quiz question."""
    question_number: int
    english_word: str
    phonetic: str
    audio_base64: Optional[str]
    audio_format: str
    options: List[VocabOption]
    correct_answer: str
    correct_meaning: str
    example_sentence: str
    word_type: str


# ==================== Response Dataclasses ====================

@dataclass
class GeneratedMCQuestions:
    """Generated multiple choice questions response."""
    dialogue_excerpt: str
    speaker: str
    difficulty: str
    question_count: int
    questions: List[MultipleChoiceQuestion]
    
    def to_dict(self) -> dict:
        return {
            "dialogue_excerpt": self.dialogue_excerpt,
            "speaker": self.speaker,
            "difficulty": self.difficulty,
            "question_count": self.question_count,
            "questions": [
                {
                    "question_number": q.question_number,
                    "question_text": q.question_text,
                    "options": [{"label": o.label, "text": o.text, "is_correct": o.is_correct} for o in q.options],
                    "correct_answer": q.correct_answer,
                    "explanation": q.explanation,
                    "related_dialogue": q.related_dialogue
                }
                for q in self.questions
            ]
        }


@dataclass
class GeneratedFillBlankQuestions:
    """Generated fill in the blank questions response."""
    dialogue_excerpt: str
    speaker: str
    difficulty: str
    question_count: int
    questions: List[FillBlankQuestion]
    
    def to_dict(self) -> dict:
        return {
            "dialogue_excerpt": self.dialogue_excerpt,
            "speaker": self.speaker,
            "difficulty": self.difficulty,
            "question_count": self.question_count,
            "questions": [
                {
                    "question_number": q.question_number,
                    "original_sentence": q.original_sentence,
                    "sentence_with_blanks": q.sentence_with_blanks,
                    "blanks": [
                        {"blank_number": b.blank_number, "correct_word": b.correct_word, "position_in_sentence": b.position_in_sentence}
                        for b in q.blanks
                    ],
                    "word_options": q.word_options,
                    "correct_words": q.correct_words,
                    "speaker": q.speaker
                }
                for q in self.questions
            ]
        }


@dataclass
class GeneratedSentenceBuilderQuestions:
    """Generated sentence builder questions response."""
    dialogue_excerpt: str
    speaker: str
    difficulty: str
    question_count: int
    questions: List[SentenceBuilderQuestion]
    
    def to_dict(self) -> dict:
        return {
            "dialogue_excerpt": self.dialogue_excerpt,
            "speaker": self.speaker,
            "difficulty": self.difficulty,
            "question_count": self.question_count,
            "questions": [
                {
                    "question_number": q.question_number,
                    "original_sentence": q.original_sentence,
                    "scrambled_words": q.scrambled_words,
                    "word_order": q.word_order,
                    "word_count": q.word_count,
                    "speaker": q.speaker,
                    "hint": q.hint
                }
                for q in self.questions
            ]
        }


@dataclass
class GeneratedVocabQuestions:
    """Generated vocabulary quiz questions response."""
    dialogue_excerpt: str
    speaker: str
    difficulty: str
    question_count: int
    questions: List[VocabularyQuestion]
    
    def to_dict(self) -> dict:
        return {
            "dialogue_excerpt": self.dialogue_excerpt,
            "speaker": self.speaker,
            "difficulty": self.difficulty,
            "question_count": self.question_count,
            "questions": [
                {
                    "question_number": q.question_number,
                    "english_word": q.english_word,
                    "phonetic": q.phonetic,
                    "audio_base64": q.audio_base64,
                    "audio_format": q.audio_format,
                    "options": [{"label": o.label, "text": o.text, "is_correct": o.is_correct} for o in q.options],
                    "correct_answer": q.correct_answer,
                    "correct_meaning": q.correct_meaning,
                    "example_sentence": q.example_sentence,
                    "word_type": q.word_type
                }
                for q in self.questions
            ]
        }


class ListeningQuestionGenerator:
    """
    Generates various types of questions based on dialogue content.
    """
    
    MODEL = "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo"
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the question generator."""
        self.api_key = api_key or os.getenv("TOGETHER_API_KEY")
        if not self.api_key:
            raise ValueError("Together API key is required.")
        self.client = Together(api_key=self.api_key)
    
    def _get_phonetic(self, word: str) -> str:
        """Get IPA phonetic transcription."""
        if IPA_AVAILABLE:
            try:
                phonetic = ipa.convert(word.lower())
                return f"/{phonetic}/"
            except:
                pass
        return f"[{word}]"
    
    def _generate_audio(self, text: str) -> tuple:
        """Generate audio for text using gTTS."""
        if GTTS_AVAILABLE:
            try:
                tts = gTTS(text=text, lang='en', slow=False)
                audio_buffer = io.BytesIO()
                tts.write_to_fp(audio_buffer)
                audio_buffer.seek(0)
                audio_base64 = base64.b64encode(audio_buffer.read()).decode('utf-8')
                return audio_base64, "mp3"
            except Exception as e:
                print(f"TTS failed: {e}")
        return None, "none"
    
    def _get_difficulty_instruction(self, difficulty: QuestionDifficulty, question_type: QuestionType) -> str:
        """Get difficulty-specific instructions based on CEFR level."""
        spec = get_cefr_spec(difficulty.value)
        assess = spec["assessment"]
        vocab = spec["vocabulary"]
        sent = spec["sentence_length"]
        
        if question_type == QuestionType.MULTIPLE_CHOICE:
            return f"Question style: {assess['question_style']}. Distractors: {assess['distractors']}. Vocabulary level: {vocab['description']}."
        elif question_type == QuestionType.FILL_BLANK:
            return f"Use {assess['blanks_per_question']} blank(s) per sentence. Vocabulary level: {vocab['description']}. {vocab['restrictions']}."
        elif question_type == QuestionType.VOCABULARY_QUIZ:
            return f"Vocabulary level: {assess['vocab_level']}. {vocab['description']}. Example words: {vocab['examples']}."
        else:  # SENTENCE_BUILDER
            return f"Use sentences with {assess['builder_words']}. Target sentence length: {sent['words_per_sentence']}. Grammar: {spec['grammar']['tenses']}."
    
    # ==================== Multiple Choice Generation ====================
    
    def generate_multiple_choice(
        self,
        dialogue_excerpt: str,
        speaker: str,
        difficulty: QuestionDifficulty = QuestionDifficulty.B1,
        question_count: int = 3,
        additional_details: Optional[str] = None
    ) -> GeneratedMCQuestions:
        """Generate multiple choice questions based on dialogue."""
        
        difficulty_instruction = self._get_difficulty_instruction(difficulty, QuestionType.MULTIPLE_CHOICE)
        
        additional_section = f"\nAdditional requirements: {additional_details}" if additional_details else ""
        
        prompt = f"""You are an English language assessment expert. Create multiple choice questions based on this dialogue excerpt.

**Dialogue (spoken by {speaker}):**
"{dialogue_excerpt}"

**Difficulty:** {difficulty.value}
{difficulty_instruction}

**Number of Questions:** {question_count}
{additional_section}

**RULES:**
1. Each question must have exactly 4 options (A, B, C, D)
2. Only ONE option is correct
3. Questions should test comprehension of the dialogue
4. Vary correct answer positions
5. Include brief explanations

**OUTPUT FORMAT (JSON only):**
{{
    "questions": [
        {{
            "question_number": 1,
            "question_text": "What does the speaker mean when they say...?",
            "options": [
                {{"label": "A", "text": "Option A", "is_correct": false}},
                {{"label": "B", "text": "Option B", "is_correct": true}},
                {{"label": "C", "text": "Option C", "is_correct": false}},
                {{"label": "D", "text": "Option D", "is_correct": false}}
            ],
            "correct_answer": "B",
            "explanation": "The speaker indicates...",
            "related_dialogue": "The specific part of dialogue this relates to"
        }}
    ]
}}

Return ONLY valid JSON."""

        try:
            response = self.client.chat.completions.create(
                model=self.MODEL,
                messages=[
                    {"role": "system", "content": "You are an expert English assessment designer. Respond with valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=3000
            )
            response_text = response.choices[0].message.content
        except Exception as e:
            raise RuntimeError(f"LLM call failed: {e}")
        
        # Parse response
        json_match = re.search(r'\{[\s\S]*\}', response_text)
        if not json_match:
            raise ValueError("No valid JSON in response")
        
        data = json.loads(json_match.group())
        
        questions = []
        for q in data.get("questions", []):
            options = [MCOption(o["label"], o["text"], o["is_correct"]) for o in q.get("options", [])]
            questions.append(MultipleChoiceQuestion(
                question_number=q.get("question_number", len(questions) + 1),
                question_text=q.get("question_text", ""),
                options=options,
                correct_answer=q.get("correct_answer", ""),
                explanation=q.get("explanation", ""),
                related_dialogue=q.get("related_dialogue", dialogue_excerpt)
            ))
        
        return GeneratedMCQuestions(
            dialogue_excerpt=dialogue_excerpt,
            speaker=speaker,
            difficulty=difficulty.value,
            question_count=len(questions),
            questions=questions
        )
    
    # ==================== Fill in the Blank Generation ====================
    
    def generate_fill_blank(
        self,
        dialogue_excerpt: str,
        speaker: str,
        difficulty: QuestionDifficulty = QuestionDifficulty.B1,
        question_count: int = 3,
        additional_details: Optional[str] = None
    ) -> GeneratedFillBlankQuestions:
        """Generate fill in the blank questions from dialogue."""
        
        difficulty_instruction = self._get_difficulty_instruction(difficulty, QuestionType.FILL_BLANK)
        
        # Determine blanks per question based on CEFR level
        spec = get_cefr_spec(difficulty.value)
        blanks_per_question = spec["assessment"]["blanks_per_question"]
        
        additional_section = f"\nAdditional requirements: {additional_details}" if additional_details else ""
        
        prompt = f"""You are an English language assessment expert. Create fill-in-the-blank questions based on this dialogue.

**Dialogue (spoken by {speaker}):**
"{dialogue_excerpt}"

**Difficulty:** {difficulty.value}
{difficulty_instruction}

**Number of Questions:** {question_count}
**Blanks per Question:** {blanks_per_question}
{additional_section}

**RULES:**
1. Create sentences from the dialogue with {blanks_per_question} word(s) removed
2. Mark blanks as ___1___, ___2___, etc.
3. Provide {blanks_per_question + 3} word options (correct words + 3 distractors)
4. Distractors should be plausible but wrong
5. Specify which word goes in which blank

**OUTPUT FORMAT (JSON only):**
{{
    "questions": [
        {{
            "question_number": 1,
            "original_sentence": "I really enjoyed the movie last night.",
            "sentence_with_blanks": "I really ___1___ the ___2___ last night.",
            "blanks": [
                {{"blank_number": 1, "correct_word": "enjoyed", "position_in_sentence": 3}},
                {{"blank_number": 2, "correct_word": "movie", "position_in_sentence": 5}}
            ],
            "word_options": ["enjoyed", "movie", "hated", "dinner", "book"],
            "correct_words": ["enjoyed", "movie"]
        }}
    ]
}}

Return ONLY valid JSON."""

        try:
            response = self.client.chat.completions.create(
                model=self.MODEL,
                messages=[
                    {"role": "system", "content": "You are an expert English assessment designer. Respond with valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=3000
            )
            response_text = response.choices[0].message.content
        except Exception as e:
            raise RuntimeError(f"LLM call failed: {e}")
        
        json_match = re.search(r'\{[\s\S]*\}', response_text)
        if not json_match:
            raise ValueError("No valid JSON in response")
        
        data = json.loads(json_match.group())
        
        questions = []
        for q in data.get("questions", []):
            blanks = [
                BlankInfo(b["blank_number"], b["correct_word"], b.get("position_in_sentence", 0))
                for b in q.get("blanks", [])
            ]
            questions.append(FillBlankQuestion(
                question_number=q.get("question_number", len(questions) + 1),
                original_sentence=q.get("original_sentence", ""),
                sentence_with_blanks=q.get("sentence_with_blanks", ""),
                blanks=blanks,
                word_options=q.get("word_options", []),
                correct_words=q.get("correct_words", []),
                speaker=speaker
            ))
        
        return GeneratedFillBlankQuestions(
            dialogue_excerpt=dialogue_excerpt,
            speaker=speaker,
            difficulty=difficulty.value,
            question_count=len(questions),
            questions=questions
        )
    
    # ==================== Sentence Builder Generation ====================
    
    def generate_sentence_builder(
        self,
        dialogue_excerpt: str,
        speaker: str,
        difficulty: QuestionDifficulty = QuestionDifficulty.B1,
        question_count: int = 3,
        additional_details: Optional[str] = None
    ) -> GeneratedSentenceBuilderQuestions:
        """Generate sentence building questions from dialogue."""
        
        difficulty_instruction = self._get_difficulty_instruction(difficulty, QuestionType.SENTENCE_BUILDER)
        additional_section = f"\nAdditional requirements: {additional_details}" if additional_details else ""
        
        prompt = f"""You are an English language assessment expert. Create sentence ordering exercises from this dialogue.

**Dialogue (spoken by {speaker}):**
"{dialogue_excerpt}"

**Difficulty:** {difficulty.value}
{difficulty_instruction}

**Number of Questions:** {question_count}
{additional_section}

**RULES:**
1. Select sentences from the dialogue
2. Split into individual words (keep punctuation with last word)
3. Provide a hint about the sentence meaning
4. Sentences should match the difficulty level

**OUTPUT FORMAT (JSON only):**
{{
    "questions": [
        {{
            "question_number": 1,
            "original_sentence": "How are you today?",
            "hint": "A common greeting question"
        }}
    ]
}}

Return ONLY valid JSON."""

        try:
            response = self.client.chat.completions.create(
                model=self.MODEL,
                messages=[
                    {"role": "system", "content": "You are an expert English assessment designer. Respond with valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2000
            )
            response_text = response.choices[0].message.content
        except Exception as e:
            raise RuntimeError(f"LLM call failed: {e}")
        
        json_match = re.search(r'\{[\s\S]*\}', response_text)
        if not json_match:
            raise ValueError("No valid JSON in response")
        
        data = json.loads(json_match.group())
        
        questions = []
        for q in data.get("questions", []):
            original = q.get("original_sentence", "")
            words = original.split()
            
            # Create scrambled version with order tracking
            indexed_words = list(enumerate(words))
            random.shuffle(indexed_words)
            scrambled = [w for _, w in indexed_words]
            word_order = [i for i, _ in indexed_words]
            # Convert to correct order (what position should word at index i go to)
            correct_order = [0] * len(words)
            for new_pos, (orig_pos, _) in enumerate(indexed_words):
                correct_order[new_pos] = orig_pos
            
            questions.append(SentenceBuilderQuestion(
                question_number=q.get("question_number", len(questions) + 1),
                original_sentence=original,
                scrambled_words=scrambled,
                word_order=correct_order,
                word_count=len(words),
                speaker=speaker,
                hint=q.get("hint")
            ))
        
        return GeneratedSentenceBuilderQuestions(
            dialogue_excerpt=dialogue_excerpt,
            speaker=speaker,
            difficulty=difficulty.value,
            question_count=len(questions),
            questions=questions
        )
    
    # ==================== Vocabulary Quiz Generation ====================
    
    def generate_vocabulary_quiz(
        self,
        dialogue_excerpt: str,
        speaker: str,
        difficulty: QuestionDifficulty = QuestionDifficulty.B1,
        question_count: int = 3,
        additional_details: Optional[str] = None,
        generate_audio: bool = True
    ) -> GeneratedVocabQuestions:
        """Generate vocabulary quiz with audio from dialogue words."""
        
        difficulty_instruction = self._get_difficulty_instruction(difficulty, QuestionType.VOCABULARY_QUIZ)
        additional_section = f"\nAdditional requirements: {additional_details}" if additional_details else ""
        
        prompt = f"""You are an English-Turkish language expert. Create vocabulary quiz questions from words in this dialogue.

**Dialogue (spoken by {speaker}):**
"{dialogue_excerpt}"

**Difficulty:** {difficulty.value}
{difficulty_instruction}

**Number of Questions:** {question_count}
{additional_section}

**RULES:**
1. Select important vocabulary words from the dialogue
2. Provide the correct Turkish translation
3. Provide 3 wrong Turkish translations (plausible distractors from same category)
4. Include word type (noun, verb, adjective, etc.)
5. Create an example sentence using the word

**OUTPUT FORMAT (JSON only):**
{{
    "questions": [
        {{
            "question_number": 1,
            "english_word": "restaurant",
            "word_type": "noun",
            "correct_meaning": "restoran",
            "wrong_meanings": ["market", "hastane", "okul"],
            "example_sentence": "We had dinner at a nice restaurant."
        }}
    ]
}}

Return ONLY valid JSON."""

        try:
            response = self.client.chat.completions.create(
                model=self.MODEL,
                messages=[
                    {"role": "system", "content": "You are an expert English-Turkish language teacher. Respond with valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=3000
            )
            response_text = response.choices[0].message.content
        except Exception as e:
            raise RuntimeError(f"LLM call failed: {e}")
        
        json_match = re.search(r'\{[\s\S]*\}', response_text)
        if not json_match:
            raise ValueError("No valid JSON in response")
        
        data = json.loads(json_match.group())
        
        questions = []
        for q in data.get("questions", []):
            english_word = q.get("english_word", "")
            correct_meaning = q.get("correct_meaning", "")
            wrong_meanings = q.get("wrong_meanings", [])[:3]
            
            # Get phonetic
            phonetic = self._get_phonetic(english_word)
            
            # Generate audio if requested
            audio_base64, audio_format = (None, "none")
            if generate_audio:
                audio_base64, audio_format = self._generate_audio(english_word)
            
            # Create randomized options
            all_meanings = [correct_meaning] + wrong_meanings
            random.shuffle(all_meanings)
            
            labels = ["A", "B", "C", "D"]
            options = []
            correct_answer = ""
            
            for i, meaning in enumerate(all_meanings[:4]):
                is_correct = meaning == correct_meaning
                if is_correct:
                    correct_answer = labels[i]
                options.append(VocabOption(labels[i], meaning, is_correct))
            
            questions.append(VocabularyQuestion(
                question_number=q.get("question_number", len(questions) + 1),
                english_word=english_word,
                phonetic=phonetic,
                audio_base64=audio_base64,
                audio_format=audio_format,
                options=options,
                correct_answer=correct_answer,
                correct_meaning=correct_meaning,
                example_sentence=q.get("example_sentence", ""),
                word_type=q.get("word_type", "unknown")
            ))
        
        return GeneratedVocabQuestions(
            dialogue_excerpt=dialogue_excerpt,
            speaker=speaker,
            difficulty=difficulty.value,
            question_count=len(questions),
            questions=questions
        )
