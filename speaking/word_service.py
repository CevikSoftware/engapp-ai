"""
Word Pronunciation Service for Speaking Practice
Generates audio pronunciation and phonetics for word lists.
"""

import wave
import os
import io
import json
import re
import base64
from pathlib import Path
from typing import Optional, List, Dict
from dataclasses import dataclass

try:
    from together import Together
    TOGETHER_AVAILABLE = True
except ImportError:
    TOGETHER_AVAILABLE = False

try:
    from piper import PiperVoice
    from piper.config import SynthesisConfig
    PIPER_AVAILABLE = True
except ImportError:
    PIPER_AVAILABLE = False
    print("Warning: piper-tts not installed. TTS features will be disabled.")

# Try to import eng_to_ipa for phonetic transcription
try:
    import eng_to_ipa as ipa
    IPA_AVAILABLE = True
except ImportError:
    IPA_AVAILABLE = False
    print("Warning: eng_to_ipa not installed. IPA transcription will use fallback.")

from cefr_config import get_cefr_spec, get_difficulty_prompt

# CEFR-based speech speed recommendations
CEFR_SPEECH_SPEED = {
    "A1": 1.6,   # Very slow
    "A2": 1.4,   # Slow
    "A1-A2": 1.5,
    "B1": 1.2,   # Slightly slow
    "B2": 1.0,   # Normal
    "A2-B1": 1.3,
    "B1-B2": 1.1,
    "C1": 0.9,   # Slightly fast
    "C2": 0.8,   # Fast / natural
    "B2-C1": 0.95,
    "C1-C2": 0.85,
}


# Voice configurations - ONLY these 8 voices are allowed
# Verified and tested voices for consistent quality
VOICE_PRESETS = {
    "male": [
        {"voice_id": "male_1", "speaker_id": 300, "name": "Alex", "description": "Deep, confident male voice"},
        {"voice_id": "male_2", "speaker_id": 190, "name": "Christopher", "description": "Clear, professional male voice"},
        {"voice_id": "male_3", "speaker_id": 70, "name": "Daniel", "description": "Warm, friendly male voice"},
        {"voice_id": "male_4", "speaker_id": 212, "name": "John", "description": "Authoritative male voice"},
    ],
    "female": [
        {"voice_id": "female_1", "speaker_id": 170, "name": "Stephanie", "description": "Warm, friendly female voice"},
        {"voice_id": "female_2", "speaker_id": 10, "name": "Sarah", "description": "Clear, professional female voice"},
        {"voice_id": "female_3", "speaker_id": 118, "name": "Olivia", "description": "Soft, gentle female voice"},
        {"voice_id": "female_4", "speaker_id": 115, "name": "Emma", "description": "Young, cheerful female voice"},
    ]
}

# Flat dictionary for quick voice lookup
ALL_VOICES: Dict[str, dict] = {}
for gender_voices in VOICE_PRESETS.values():
    for voice in gender_voices:
        ALL_VOICES[voice["voice_id"]] = voice


# Simple phonetic mappings for fallback when eng_to_ipa is not available
SIMPLE_PHONETICS = {
    'a': 'æ', 'e': 'ɛ', 'i': 'ɪ', 'o': 'ɒ', 'u': 'ʌ',
    'ai': 'aɪ', 'ay': 'eɪ', 'ea': 'iː', 'ee': 'iː', 'ie': 'aɪ',
    'oa': 'oʊ', 'oo': 'uː', 'ou': 'aʊ', 'ow': 'aʊ', 'oi': 'ɔɪ',
    'oy': 'ɔɪ', 'au': 'ɔː', 'aw': 'ɔː', 'ew': 'juː', 'ue': 'uː',
    'ch': 'tʃ', 'sh': 'ʃ', 'th': 'θ', 'ph': 'f', 'wh': 'w',
    'ng': 'ŋ', 'ck': 'k', 'gh': '', 'kn': 'n', 'wr': 'r',
}


def count_syllables(word: str) -> int:
    """
    Count the number of syllables in a word.
    Uses a simple vowel-counting heuristic.
    """
    word = word.lower().strip()
    if not word:
        return 0
    
    vowels = "aeiouy"
    count = 0
    prev_is_vowel = False
    
    for char in word:
        is_vowel = char in vowels
        if is_vowel and not prev_is_vowel:
            count += 1
        prev_is_vowel = is_vowel
    
    # Adjust for silent 'e' at end
    if word.endswith('e') and count > 1:
        count -= 1
    
    # Adjust for 'le' endings (like "table", "apple")
    if word.endswith('le') and len(word) > 2 and word[-3] not in vowels:
        count += 1
    
    return max(1, count)


def get_stress_pattern(word: str) -> str:
    """
    Generate a simple stress pattern for a word.
    Returns a pattern like "ˈ◌-◌" where ˈ indicates primary stress.
    """
    syllables = count_syllables(word)
    if syllables == 1:
        return "ˈ◌"
    elif syllables == 2:
        # Most 2-syllable words stress first syllable
        return "ˈ◌-◌"
    else:
        # For longer words, assume stress on second syllable as default
        pattern = "◌-" + "ˈ◌" + "-◌" * (syllables - 2)
        return pattern


def get_ipa_transcription(word: str) -> str:
    """
    Get IPA phonetic transcription for a word.
    Uses eng_to_ipa library if available, otherwise returns simplified version.
    """
    word = word.lower().strip()
    
    if IPA_AVAILABLE:
        try:
            result = ipa.convert(word)
            # eng_to_ipa returns the word itself if it can't convert
            if result and result != word and '*' not in result:
                return f"/{result}/"
        except Exception:
            pass
    
    # Fallback: return a simplified phonetic representation
    return f"/[{word}]/"


def get_simple_phonetic(word: str) -> str:
    """
    Generate a simplified phonetic representation for pronunciation guidance.
    This is more user-friendly than IPA for language learners.
    """
    word = word.lower().strip()
    
    # Common pronunciation patterns
    result = word
    
    # Apply common substitutions
    replacements = [
        ('tion', 'shun'),
        ('sion', 'zhun'),
        ('ough', 'uff'),
        ('ight', 'ite'),
        ('ph', 'f'),
        ('gh', ''),
        ('kn', 'n'),
        ('wr', 'r'),
        ('mb', 'm'),
        ('mn', 'm'),
    ]
    
    for old, new in replacements:
        result = result.replace(old, new)
    
    return result


@dataclass
class WordPronunciation:
    """Data class for word pronunciation information."""
    word: str
    phonetic_ipa: str
    phonetic_simple: str
    audio_base64: str
    syllable_count: int
    stress_pattern: str
    example_sentence: str = ""
    usage_note: str = ""
    cefr_level: str = "B1"


class WordPronunciationService:
    """
    Service for generating word pronunciations with audio and phonetics.
    """
    
    def __init__(self, model_dir: Optional[str] = None):
        """
        Initialize the pronunciation service.
        
        Args:
            model_dir: Directory containing the ONNX model files.
        """
        if not PIPER_AVAILABLE:
            raise RuntimeError("piper-tts is not installed. Please install it with: pip install piper-tts")
        
        # Find model directory
        if model_dir is None:
            current_dir = Path(__file__).parent.parent.parent
            model_dir = str(current_dir)
        
        self.model_dir = model_dir
        self.model_name = "en_US-libritts-high"
        self.model_path = os.path.join(model_dir, f"{self.model_name}.onnx")
        self.config_path = os.path.join(model_dir, f"{self.model_name}.onnx.json")
        
        self.voice = None
        self._load_model()
    
    def _load_model(self):
        """Load the Piper TTS model."""
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"Model file not found: {self.model_path}")
        
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Config file not found: {self.config_path}")
        
        print(f"Loading TTS model for speaking practice from: {self.model_path}")
        self.voice = PiperVoice.load(
            self.model_path,
            config_path=self.config_path,
            use_cuda=False
        )
        print("TTS model loaded successfully for speaking practice.")
    
    def get_voice_by_id(self, voice_id: str) -> Optional[dict]:
        """Get voice configuration by ID."""
        return ALL_VOICES.get(voice_id)
    
    @staticmethod
    def get_available_voices() -> Dict[str, List[dict]]:
        """Get all available voices."""
        return VOICE_PRESETS
    
    def synthesize_word_to_base64(
        self,
        word: str,
        speaker_id: int,
        length_scale: float = 1.0,
        noise_scale: float = 0.667
    ) -> str:
        """
        Synthesize a word to base64 encoded WAV audio.
        
        Args:
            word: The word to synthesize.
            speaker_id: The speaker ID to use.
            length_scale: Speech speed (1.0=normal, >1=slower, <1=faster).
            noise_scale: Voice variation.
            
        Returns:
            Base64 encoded WAV audio data.
        """
        if self.voice is None:
            raise RuntimeError("TTS model not loaded")
        
        # Create synthesis config
        syn_config = SynthesisConfig(
            speaker_id=speaker_id,
            length_scale=length_scale,
            noise_scale=noise_scale
        )
        
        # Synthesize and collect audio chunks
        audio_chunks = list(self.voice.synthesize(word, syn_config))
        
        if not audio_chunks:
            raise RuntimeError(f"No audio generated for word: {word}")
        
        # Get audio parameters from first chunk
        first_chunk = audio_chunks[0]
        sample_rate = first_chunk.sample_rate
        sample_width = first_chunk.sample_width
        channels = first_chunk.sample_channels
        
        # Combine all audio data
        all_audio = b""
        for chunk in audio_chunks:
            all_audio += chunk.audio_int16_bytes
        
        # Write WAV to bytes buffer
        buffer = io.BytesIO()
        with wave.open(buffer, "wb") as wav_file:
            wav_file.setnchannels(channels)
            wav_file.setsampwidth(sample_width)
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(all_audio)
        
        # Encode to base64
        audio_bytes = buffer.getvalue()
        return base64.b64encode(audio_bytes).decode('utf-8')
    
    def process_word_list(
        self,
        words: List[str],
        voice_id: str = "female_1",
        speech_speed: float = 1.0,
        difficulty: str = "B1"
    ) -> List[WordPronunciation]:
        """
        Process a list of words and generate pronunciation data for each.
        
        Args:
            words: List of words to process.
            voice_id: Voice ID to use for audio generation.
            speech_speed: Speech speed multiplier.
            
        Returns:
            List of WordPronunciation objects.
        """
        # Get voice configuration
        voice_config = self.get_voice_by_id(voice_id)
        if voice_config is None:
            # Default to female_1 if voice not found
            voice_config = ALL_VOICES.get("female_1", {"speaker_id": 0})
        
        speaker_id = voice_config["speaker_id"]
        
        # Generate CEFR-aware example sentences via LLM
        examples = self._generate_examples(words, difficulty)
        
        results = []
        
        for word in words:
            word = word.strip()
            if not word:
                continue
            
            try:
                # Generate audio
                audio_base64 = self.synthesize_word_to_base64(
                    word=word,
                    speaker_id=speaker_id,
                    length_scale=speech_speed
                )
                
                # Get phonetic information
                phonetic_ipa = get_ipa_transcription(word)
                phonetic_simple = get_simple_phonetic(word)
                syllable_count = count_syllables(word)
                stress_pattern = get_stress_pattern(word)
                
                results.append(WordPronunciation(
                    word=word,
                    phonetic_ipa=phonetic_ipa,
                    phonetic_simple=phonetic_simple,
                    audio_base64=audio_base64,
                    syllable_count=syllable_count,
                    stress_pattern=stress_pattern,
                    example_sentence=examples.get(word.lower(), {}).get("sentence", ""),
                    usage_note=examples.get(word.lower(), {}).get("note", ""),
                    cefr_level=difficulty
                ))
            except Exception as e:
                print(f"Error processing word '{word}': {e}")
                # Add entry with error indication
                results.append(WordPronunciation(
                    word=word,
                    phonetic_ipa="/error/",
                    phonetic_simple="error",
                    audio_base64="",
                    syllable_count=0,
                    stress_pattern="",
                    example_sentence="",
                    usage_note="",
                    cefr_level=difficulty
                ))
        
        return results

    def _generate_examples(self, words: List[str], difficulty: str = "B1") -> Dict[str, Dict[str, str]]:
        """
        Generate CEFR-appropriate example sentences and usage notes for words using Together AI.
        
        Returns dict like: {"word": {"sentence": "...", "note": "..."}}
        """
        if not TOGETHER_AVAILABLE:
            return {}
        
        api_key = os.getenv("TOGETHER_API_KEY")
        if not api_key:
            return {}
        
        try:
            spec = get_cefr_spec(difficulty)
            vocab_desc = spec["vocabulary"]["description"]
            grammar_tenses = spec["grammar"]["tenses"]
            sent_length = spec["sentence_length"]["words_per_sentence"]
            
            client = Together(api_key=api_key)
            
            word_list_str = ", ".join([w.strip() for w in words[:50] if w.strip()])
            
            prompt = f"""For each word below, generate:
1. One example sentence appropriate for CEFR {difficulty} level
2. A brief usage note (1 sentence)

CEFR {difficulty} requirements:
- Vocabulary: {vocab_desc}
- Grammar: use only {grammar_tenses}
- Sentence length: {sent_length}

Words: {word_list_str}

Return ONLY valid JSON in this format:
{{
    "word1": {{"sentence": "Example sentence using word1.", "note": "Brief usage note."}},
    "word2": {{"sentence": "Example sentence using word2.", "note": "Brief usage note."}}
}}

Rules:
- Example sentences must use ONLY grammar and vocabulary appropriate for CEFR {difficulty}
- Sentences must be natural and useful for pronunciation practice
- Usage notes should be simple and helpful for the CEFR level
- Return ONLY JSON, no extra text"""

            response = client.chat.completions.create(
                model="meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",
                messages=[
                    {"role": "system", "content": "You are an English pronunciation teacher. Generate example sentences and usage notes. Always respond with valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=2000,
                temperature=0.5
            )
            
            response_text = response.choices[0].message.content.strip()
            
            # Parse JSON
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                result = json.loads(json_match.group())
            else:
                result = json.loads(response_text)
            
            # Normalize keys to lowercase
            return {k.lower(): v for k, v in result.items()}
            
        except Exception as e:
            print(f"Warning: Could not generate CEFR examples: {e}")
            return {}
