"""
Text-to-Speech Service for Listening Practice
Converts conversation dialogues to audio files using Piper TTS.
"""

import wave
import os
from pathlib import Path
from typing import Optional, List, Dict
from dataclasses import dataclass
from enum import Enum

try:
    from piper import PiperVoice
    from piper.config import SynthesisConfig
    PIPER_AVAILABLE = True
except ImportError:
    PIPER_AVAILABLE = False
    print("Warning: piper-tts not installed. TTS features will be disabled.")


class Gender(str, Enum):
    MALE = "male"
    FEMALE = "female"


@dataclass
class VoiceConfig:
    """Configuration for a voice."""
    voice_id: str  # Unique identifier for API selection
    speaker_id: int
    gender: Gender
    name: str
    description: str = ""


# Voice mappings for libritts-high model
# Verified and tested voices - ONLY these 8 voices are allowed
VOICE_PRESETS = {
    Gender.MALE: [
        VoiceConfig(voice_id="male_1", speaker_id=300, gender=Gender.MALE, name="Alex", description="Deep, confident male voice"),
        VoiceConfig(voice_id="male_2", speaker_id=190, gender=Gender.MALE, name="Christopher", description="Clear, professional male voice"),
        VoiceConfig(voice_id="male_3", speaker_id=70, gender=Gender.MALE, name="Daniel", description="Warm, friendly male voice"),
        VoiceConfig(voice_id="male_4", speaker_id=212, gender=Gender.MALE, name="John", description="Authoritative male voice"),
    ],
    Gender.FEMALE: [
        VoiceConfig(voice_id="female_1", speaker_id=170, gender=Gender.FEMALE, name="Stephanie", description="Warm, friendly female voice"),
        VoiceConfig(voice_id="female_2", speaker_id=10, gender=Gender.FEMALE, name="Sarah", description="Clear, professional female voice"),
        VoiceConfig(voice_id="female_3", speaker_id=118, gender=Gender.FEMALE, name="Olivia", description="Soft, gentle female voice"),
        VoiceConfig(voice_id="female_4", speaker_id=115, gender=Gender.FEMALE, name="Emma", description="Young, cheerful female voice"),
    ]
}

# Create a flat dictionary for quick voice lookup by ID
ALL_VOICES: Dict[str, VoiceConfig] = {}
for gender_voices in VOICE_PRESETS.values():
    for voice in gender_voices:
        ALL_VOICES[voice.voice_id] = voice


@dataclass
class AudioFile:
    """Represents a generated audio file."""
    filename: str
    filepath: str
    speaker: str
    dialogue_index: int
    turn_index: int
    text: str
    audio_data: bytes = None  # Raw audio bytes (WAV format)


class TTSService:
    """
    Text-to-Speech service for generating conversation audio files.
    Uses Piper TTS with multi-speaker support.
    """
    
    def __init__(self, model_dir: Optional[str] = None):
        """
        Initialize the TTS service.
        
        Args:
            model_dir: Directory containing the ONNX model files.
                      Defaults to the project root.
        """
        if not PIPER_AVAILABLE:
            raise RuntimeError("piper-tts is not installed. Please install it with: pip install piper-tts")
        
        # Find model directory (go up from listening folder to find models)
        if model_dir is None:
            # Navigate up from real_project_api to find the models
            current_dir = Path(__file__).parent.parent.parent
            model_dir = str(current_dir)
        
        self.model_dir = model_dir
        self.model_name = "en_US-libritts-high"
        self.model_path = os.path.join(model_dir, f"{self.model_name}.onnx")
        self.config_path = os.path.join(model_dir, f"{self.model_name}.onnx.json")
        
        self.voice: Optional[PiperVoice] = None
        self._load_model()
    
    def _download_model_if_missing(self):
        """Download the Piper TTS model if it doesn't exist."""
        if os.path.exists(self.model_path) and os.path.exists(self.config_path):
            return

        print(f"Model not found at {self.model_path}. Downloading...")
        
        # URLs for the model files
        model_url = "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/libritts/high/en_US-libritts-high.onnx?download=true"
        config_url = "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/libritts/high/en_US-libritts-high.onnx.json?download=true"
        
        try:
            import requests
            
            # Download model file
            print(f"Downloading model file from {model_url}...")
            response = requests.get(model_url, stream=True)
            response.raise_for_status()
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.model_path), exist_ok=True)

            with open(self.model_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            # Download config file
            print(f"Downloading config file from {config_url}...")
            response = requests.get(config_url, stream=True)
            response.raise_for_status()
            with open(self.config_path, "wb") as f:
                f.write(response.content)
                
            print("Model downloaded successfully.")
            
        except ImportError:
            raise RuntimeError("The 'requests' library is required to download models. Please install it: pip install requests")
        except Exception as e:
            # Clean up partial downloads
            if os.path.exists(self.model_path):
                os.remove(self.model_path)
            if os.path.exists(self.config_path):
                os.remove(self.config_path)
            raise RuntimeError(f"Failed to download model: {str(e)}")

    def _load_model(self):
        """Load the Piper TTS model."""
        self._download_model_if_missing()

        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"Model file not found: {self.model_path}")
        
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Config file not found: {self.config_path}")
        
        print(f"Loading TTS model from: {self.model_path}")
        self.voice = PiperVoice.load(
            self.model_path,
            config_path=self.config_path,
            use_cuda=False
        )
        print("TTS model loaded successfully.")
    
    def get_voice_for_gender(self, gender: Gender, index: int = 0) -> VoiceConfig:
        """
        Get a voice configuration for the specified gender.
        
        Args:
            gender: The gender of the voice.
            index: Index of the voice variant (for variety).
            
        Returns:
            VoiceConfig for the requested gender.
        """
        voices = VOICE_PRESETS.get(gender, VOICE_PRESETS[Gender.MALE])
        return voices[index % len(voices)]
    
    def get_voice_by_id(self, voice_id: str) -> Optional[VoiceConfig]:
        """
        Get a voice configuration by its unique ID.
        
        Args:
            voice_id: The unique voice identifier (e.g., 'male_1', 'female_3')
            
        Returns:
            VoiceConfig if found, None otherwise.
        """
        return ALL_VOICES.get(voice_id)
    
    @staticmethod
    def get_available_voices() -> Dict[str, List[Dict]]:
        """
        Get all available voices organized by gender.
        
        Returns:
            Dictionary with 'male' and 'female' keys containing voice lists.
        """
        return {
            "male": [
                {
                    "voice_id": v.voice_id,
                    "name": v.name,
                    "description": v.description,
                    "speaker_id": v.speaker_id
                }
                for v in VOICE_PRESETS[Gender.MALE]
            ],
            "female": [
                {
                    "voice_id": v.voice_id,
                    "name": v.name,
                    "description": v.description,
                    "speaker_id": v.speaker_id
                }
                for v in VOICE_PRESETS[Gender.FEMALE]
            ]
        }
    
    def synthesize_text(
        self,
        text: str,
        output_path: str,
        speaker_id: int,
        length_scale: float = 1.0,
        noise_scale: float = 0.667
    ) -> str:
        """
        Synthesize text to audio file.
        
        Args:
            text: The text to synthesize.
            output_path: Path for the output WAV file.
            speaker_id: The speaker ID to use.
            length_scale: Speech speed (1.0 = normal, >1 = slower, <1 = faster).
            noise_scale: Voice variation (higher = more variation).
            
        Returns:
            Path to the generated audio file.
        """
        if self.voice is None:
            raise RuntimeError("TTS model not loaded")
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Create synthesis config
        syn_config = SynthesisConfig(
            speaker_id=speaker_id,
            length_scale=length_scale,
            noise_scale=noise_scale
        )
        
        # Synthesize and collect audio chunks
        audio_chunks = list(self.voice.synthesize(text, syn_config))
        
        if not audio_chunks:
            raise RuntimeError("No audio generated")
        
        # Get audio parameters from first chunk
        first_chunk = audio_chunks[0]
        sample_rate = first_chunk.sample_rate
        sample_width = first_chunk.sample_width
        channels = first_chunk.sample_channels
        
        # Combine all audio data
        all_audio = b""
        for chunk in audio_chunks:
            # Get int16 bytes from chunk
            all_audio += chunk.audio_int16_bytes
        
        # Write WAV file
        with wave.open(output_path, "wb") as wav_file:
            wav_file.setnchannels(channels)
            wav_file.setsampwidth(sample_width)
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(all_audio)
        
        return output_path
    
    def synthesize_to_bytes(
        self,
        text: str,
        speaker_id: int,
        length_scale: float = 1.0,
        noise_scale: float = 0.667
    ) -> bytes:
        """
        Synthesize text to audio bytes (WAV format) without saving to disk.
        
        Args:
            text: The text to synthesize.
            speaker_id: The speaker ID to use.
            length_scale: Speech speed (1.0 = normal, >1 = slower, <1 = faster).
            noise_scale: Voice variation (higher = more variation).
            
        Returns:
            WAV audio data as bytes.
        """
        import io
        
        if self.voice is None:
            raise RuntimeError("TTS model not loaded")
        
        # Create synthesis config
        syn_config = SynthesisConfig(
            speaker_id=speaker_id,
            length_scale=length_scale,
            noise_scale=noise_scale
        )
        
        # Synthesize and collect audio chunks
        audio_chunks = list(self.voice.synthesize(text, syn_config))
        
        if not audio_chunks:
            raise RuntimeError("No audio generated")
        
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
        
        return buffer.getvalue()
    
    def generate_conversation_audio(
        self,
        dialogue: List[Dict[str, str]],
        character1: str,
        character2: str,
        gender1: Gender,
        gender2: Gender,
        output_dir: str,
        conversation_id: str = "conv",
        voice_id1: Optional[str] = None,
        voice_id2: Optional[str] = None,
        speech_speed: float = 1.0
    ) -> List[AudioFile]:
        """
        Generate audio files for a conversation.
        
        Args:
            dialogue: List of dialogue lines with 'speaker' and 'text' keys.
            character1: Name of the first character.
            character2: Name of the second character.
            gender1: Gender of the first character.
            gender2: Gender of the second character.
            output_dir: Directory to save audio files.
            conversation_id: Identifier for the conversation.
            voice_id1: Optional specific voice ID for character1.
            voice_id2: Optional specific voice ID for character2.
            speech_speed: Speech speed multiplier (0.5=fast, 1.0=normal, 2.0=slow).
            
        Returns:
            List of AudioFile objects describing the generated files.
            
        File naming convention:
            {SPEAKER}_{dialogue_number}.{turn_number}.wav
            Example: JOHN_1.1.wav, ALEX_1.2.wav, JOHN_2.1.wav, etc.
        """
        # Get voice configs for each character
        # Use specific voice_id if provided, otherwise fall back to gender-based selection
        if voice_id1 and voice_id1 in ALL_VOICES:
            voice1 = ALL_VOICES[voice_id1]
        else:
            voice1 = self.get_voice_for_gender(gender1, 0)
            
        if voice_id2 and voice_id2 in ALL_VOICES:
            voice2 = ALL_VOICES[voice_id2]
        else:
            voice2 = self.get_voice_for_gender(gender2, 1)
        
        # Map character names to voice configs
        voice_map = {
            character1.upper(): voice1,
            character2.upper(): voice2
        }
        
        # Track dialogue numbering
        dialogue_count = 0
        audio_files: List[AudioFile] = []
        
        # Process each line of dialogue
        for i, line in enumerate(dialogue):
            speaker = line["speaker"].upper()
            text = line["text"]
            
            # Calculate dialogue number and turn
            # Dialogue number increments every 2 turns (one exchange)
            dialogue_num = (i // 2) + 1
            turn_num = (i % 2) + 1
            
            # Get voice config for this speaker
            speaker_upper = speaker.upper()
            if speaker_upper in voice_map:
                voice_config = voice_map[speaker_upper]
            elif character1.upper() in speaker_upper:
                voice_config = voice1
            elif character2.upper() in speaker_upper:
                voice_config = voice2
            else:
                # Default to alternating voices
                voice_config = voice1 if i % 2 == 0 else voice2
            
            # Generate filename: SPEAKER_dialogue.turn.wav
            filename = f"{speaker}_{dialogue_num}.{turn_num}.wav"
            filepath = os.path.join(output_dir, filename) if output_dir else ""
            
            # Synthesize audio to bytes with speech speed
            audio_bytes = self.synthesize_to_bytes(
                text=text,
                speaker_id=voice_config.speaker_id,
                length_scale=speech_speed
            )
            
            # Optionally save to file if output_dir is provided
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
                with open(filepath, 'wb') as f:
                    f.write(audio_bytes)
            
            audio_files.append(AudioFile(
                filename=filename,
                filepath=filepath,
                speaker=speaker,
                dialogue_index=dialogue_num,
                turn_index=turn_num,
                text=text,
                audio_data=audio_bytes
            ))
            
            print(f"Generated: {filename}")
        
        return audio_files


def generate_conversation_audio(
    dialogue: List[Dict[str, str]],
    character1: str,
    character2: str,
    gender1: str,
    gender2: str,
    output_dir: str,
    conversation_id: str = "conv",
    model_dir: Optional[str] = None
) -> List[Dict]:
    """
    Convenience function to generate audio for a conversation.
    
    Args:
        dialogue: List of dialogue dictionaries with 'speaker' and 'text'.
        character1: Name of character 1.
        character2: Name of character 2.
        gender1: Gender of character 1 ('male' or 'female').
        gender2: Gender of character 2 ('male' or 'female').
        output_dir: Output directory for audio files.
        conversation_id: ID for the conversation.
        model_dir: Directory containing TTS models.
        
    Returns:
        List of dictionaries describing generated audio files.
    """
    tts = TTSService(model_dir=model_dir)
    
    gender1_enum = Gender(gender1.lower())
    gender2_enum = Gender(gender2.lower())
    
    audio_files = tts.generate_conversation_audio(
        dialogue=dialogue,
        character1=character1,
        character2=character2,
        gender1=gender1_enum,
        gender2=gender2_enum,
        output_dir=output_dir,
        conversation_id=conversation_id
    )
    
    return [
        {
            "filename": af.filename,
            "filepath": af.filepath,
            "speaker": af.speaker,
            "dialogue_index": af.dialogue_index,
            "turn_index": af.turn_index,
            "text": af.text
        }
        for af in audio_files
    ]
