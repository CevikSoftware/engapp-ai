"""
Ultra-fast Async TTS Service for Practice Conversations
Optimized for CPU with minimal latency using Piper TTS.
"""

import io
import wave
import base64
import asyncio
from pathlib import Path
from typing import Optional, Dict, List
from dataclasses import dataclass
from enum import Enum
from concurrent.futures import ThreadPoolExecutor

try:
    from piper import PiperVoice
    from piper.config import SynthesisConfig
    PIPER_AVAILABLE = True
except ImportError:
    PIPER_AVAILABLE = False


class Gender(str, Enum):
    MALE = "male"
    FEMALE = "female"


@dataclass
class VoiceConfig:
    """Voice configuration."""
    voice_id: str
    speaker_id: int
    gender: Gender
    name: str
    description: str = ""


# Pre-configured voices for LibriTTS model
# Verified and tested voices - ONLY these 8 voices are allowed
VOICE_PRESETS: Dict[Gender, List[VoiceConfig]] = {
    Gender.MALE: [
        VoiceConfig("male_1", 300, Gender.MALE, "Alex", "Deep, confident male voice"),
        VoiceConfig("male_2", 190, Gender.MALE, "Christopher", "Clear, professional male"),
        VoiceConfig("male_3", 70, Gender.MALE, "Daniel", "Warm, friendly male"),
        VoiceConfig("male_4", 212, Gender.MALE, "John", "Authoritative male voice"),
    ],
    Gender.FEMALE: [
        VoiceConfig("female_1", 170, Gender.FEMALE, "Stephanie", "Warm, friendly female voice"),
        VoiceConfig("female_2", 10, Gender.FEMALE, "Sarah", "Clear, professional female"),
        VoiceConfig("female_3", 118, Gender.FEMALE, "Olivia", "Soft, gentle female"),
        VoiceConfig("female_4", 115, Gender.FEMALE, "Emma", "Young, cheerful female"),
    ]
}

# Flat lookup
ALL_VOICES: Dict[str, VoiceConfig] = {
    v.voice_id: v 
    for voices in VOICE_PRESETS.values() 
    for v in voices
}


class FastTTSService:
    """
    High-performance async TTS service.
    Uses thread pool for non-blocking synthesis.
    """
    
    _instance: Optional['FastTTSService'] = None
    _lock = asyncio.Lock()
    
    def __init__(self):
        if not PIPER_AVAILABLE:
            raise RuntimeError("piper-tts not installed")
        
        # Find model in project root
        model_dir = Path(__file__).parent.parent.parent
        self.model_path = model_dir / "en_US-libritts-high.onnx"
        self.config_path = model_dir / "en_US-libritts-high.onnx.json"
        
        if not self.model_path.exists():
            raise FileNotFoundError(f"Model not found: {self.model_path}")
        
        # Load model once
        self.voice = PiperVoice.load(
            str(self.model_path),
            config_path=str(self.config_path),
            use_cuda=False
        )
        
        # Thread pool for CPU-bound synthesis
        self._executor = ThreadPoolExecutor(max_workers=2)
    
    @classmethod
    async def get_instance(cls) -> 'FastTTSService':
        """Get or create singleton instance."""
        if cls._instance is None:
            async with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance
    
    def _synthesize_sync(self, text: str, speaker_id: int, length_scale: float = 1.0) -> bytes:
        """Synchronous synthesis - runs in thread pool."""
        # length_scale: lower = faster speech, higher = slower speech
        # We invert it so that speech_rate 1.25 = faster (length_scale 0.8)
        actual_length_scale = 1.0 / length_scale if length_scale > 0 else 1.0
        
        syn_config = SynthesisConfig(
            speaker_id=speaker_id,
            length_scale=actual_length_scale,
            noise_scale=0.667
        )
        
        # Synthesize
        audio_chunks = list(self.voice.synthesize(text, syn_config))
        
        if not audio_chunks:
            return b""
        
        # Get params
        first = audio_chunks[0]
        sample_rate = first.sample_rate
        sample_width = first.sample_width
        channels = first.sample_channels
        
        # Combine audio
        all_audio = b"".join(c.audio_int16_bytes for c in audio_chunks)
        
        # Write WAV to buffer
        buffer = io.BytesIO()
        with wave.open(buffer, "wb") as wav:
            wav.setnchannels(channels)
            wav.setsampwidth(sample_width)
            wav.setframerate(sample_rate)
            wav.writeframes(all_audio)
        
        return buffer.getvalue()
    
    async def synthesize(self, text: str, speaker_id: int, speech_rate: float = 1.0) -> bytes:
        """Async synthesis - non-blocking."""
        loop = asyncio.get_event_loop()        
        return await loop.run_in_executor(
            self._executor,
            self._synthesize_sync,
            text,
            speaker_id,
            speech_rate
        )
    
    async def synthesize_to_base64(self, text: str, speaker_id: int, speech_rate: float = 1.0) -> str:
        """Synthesize and return base64-encoded audio."""
        audio_bytes = await self.synthesize(text, speaker_id, speech_rate)
        return base64.b64encode(audio_bytes).decode('utf-8')
    
    @staticmethod
    def get_voice_by_id(voice_id: str) -> Optional[VoiceConfig]:
        """Get voice config by ID."""
        return ALL_VOICES.get(voice_id)
    
    @staticmethod
    def get_voice_by_gender(gender: Gender, index: int = 0) -> VoiceConfig:
        """Get voice by gender and index."""
        voices = VOICE_PRESETS.get(gender, VOICE_PRESETS[Gender.FEMALE])
        return voices[index % len(voices)]
    
    @staticmethod
    def get_available_voices() -> Dict[str, List[Dict]]:
        """Get all available voices."""
        return {
            "male": [
                {"voice_id": v.voice_id, "name": v.name, "description": v.description}
                for v in VOICE_PRESETS[Gender.MALE]
            ],
            "female": [
                {"voice_id": v.voice_id, "name": v.name, "description": v.description}
                for v in VOICE_PRESETS[Gender.FEMALE]
            ]
        }


# Helper function
async def get_tts_service() -> FastTTSService:
    """Get TTS service instance."""
    return await FastTTSService.get_instance()
