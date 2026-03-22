"""
Final Voice Test
Tests the 8 verified voices (4 male, 4 female) and saves them organized.
"""

import os
import sys
import wave
import io
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from piper import PiperVoice
    from piper.config import SynthesisConfig
    PIPER_AVAILABLE = True
except ImportError:
    PIPER_AVAILABLE = False
    print("ERROR: piper-tts not installed. Run: pip install piper-tts")
    sys.exit(1)


# Output directory
OUTPUT_DIR = Path(__file__).parent / "final_output"

# Model paths
MODEL_DIR = Path(__file__).parent.parent.parent
MODEL_PATH = MODEL_DIR / "en_US-libritts-high.onnx"
CONFIG_PATH = MODEL_DIR / "en_US-libritts-high.onnx.json"

# Test sentence
TEST_TEXT = "Hello, this is a test of the voice synthesis system. How does this voice sound to you?"

# ============================================
# FINAL VERIFIED VOICES - Only these 8 allowed
# ============================================

MALE_VOICES = [
    {"voice_id": "male_1", "speaker_id": 300, "name": "Alex", "description": "Deep, confident male voice"},
    {"voice_id": "male_2", "speaker_id": 190, "name": "Christopher", "description": "Clear, professional male voice"},
    {"voice_id": "male_3", "speaker_id": 70, "name": "Daniel", "description": "Warm, friendly male voice"},
    {"voice_id": "male_4", "speaker_id": 212, "name": "John", "description": "Authoritative male voice"},
]

FEMALE_VOICES = [
    {"voice_id": "female_1", "speaker_id": 170, "name": "Stephanie", "description": "Warm, friendly female voice"},
    {"voice_id": "female_2", "speaker_id": 10, "name": "Sarah", "description": "Clear, professional female voice"},
    {"voice_id": "female_3", "speaker_id": 118, "name": "Olivia", "description": "Soft, gentle female voice"},
    {"voice_id": "female_4", "speaker_id": 115, "name": "Emma", "description": "Young, cheerful female voice"},
]


def synthesize_audio(voice: PiperVoice, text: str, speaker_id: int) -> bytes:
    """Synthesize text to audio bytes."""
    audio_buffer = io.BytesIO()
    
    syn_config = SynthesisConfig(
        speaker_id=speaker_id,
        length_scale=1.0,
        noise_scale=0.667
    )
    
    audio_chunks = list(voice.synthesize(text, syn_config))
    
    if not audio_chunks:
        raise RuntimeError("No audio generated")
    
    first_chunk = audio_chunks[0]
    sample_rate = first_chunk.sample_rate
    sample_width = first_chunk.sample_width
    channels = first_chunk.sample_channels
    
    all_audio = b""
    for chunk in audio_chunks:
        all_audio += chunk.audio_int16_bytes
    
    with wave.open(audio_buffer, 'wb') as wav_file:
        wav_file.setnchannels(channels)
        wav_file.setsampwidth(sample_width)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(all_audio)
    
    return audio_buffer.getvalue()


def test_final_voices():
    """Test all 8 final verified voices."""
    
    print("=" * 60)
    print("FINAL VOICE TEST - 8 Verified Voices")
    print("=" * 60)
    
    if not MODEL_PATH.exists():
        print(f"ERROR: Model not found at {MODEL_PATH}")
        return
    
    print(f"Model: {MODEL_PATH}")
    print(f"Test text: '{TEST_TEXT}'")
    print()
    
    # Create output directories
    OUTPUT_DIR.mkdir(exist_ok=True)
    male_dir = OUTPUT_DIR / "male"
    female_dir = OUTPUT_DIR / "female"
    male_dir.mkdir(exist_ok=True)
    female_dir.mkdir(exist_ok=True)
    
    print("Loading Piper model...")
    voice = PiperVoice.load(
        str(MODEL_PATH),
        config_path=str(CONFIG_PATH),
        use_cuda=False
    )
    print("Model loaded successfully!")
    print()
    
    results = []
    
    # Test Male Voices
    print("=" * 40)
    print("MALE VOICES (4)")
    print("=" * 40)
    
    for i, v in enumerate(MALE_VOICES, 1):
        try:
            print(f"[{i}/4] {v['voice_id']} - {v['name']} (speaker_id: {v['speaker_id']})...", end=" ")
            
            audio_data = synthesize_audio(voice, TEST_TEXT, v['speaker_id'])
            
            filename = f"{v['voice_id']}_{v['name']}_sid{v['speaker_id']}.wav"
            filepath = male_dir / filename
            
            with open(filepath, 'wb') as f:
                f.write(audio_data)
            
            size_kb = len(audio_data) / 1024
            print(f"OK ({size_kb:.1f} KB)")
            
            results.append({
                'voice_id': v['voice_id'],
                'name': v['name'],
                'speaker_id': v['speaker_id'],
                'gender': 'male',
                'filepath': str(filepath),
                'size_kb': size_kb,
                'status': 'success'
            })
            
        except Exception as e:
            print(f"ERROR: {e}")
            results.append({
                'voice_id': v['voice_id'],
                'name': v['name'],
                'speaker_id': v['speaker_id'],
                'gender': 'male',
                'status': 'error',
                'error': str(e)
            })
    
    print()
    
    # Test Female Voices
    print("=" * 40)
    print("FEMALE VOICES (4)")
    print("=" * 40)
    
    for i, v in enumerate(FEMALE_VOICES, 1):
        try:
            print(f"[{i}/4] {v['voice_id']} - {v['name']} (speaker_id: {v['speaker_id']})...", end=" ")
            
            audio_data = synthesize_audio(voice, TEST_TEXT, v['speaker_id'])
            
            filename = f"{v['voice_id']}_{v['name']}_sid{v['speaker_id']}.wav"
            filepath = female_dir / filename
            
            with open(filepath, 'wb') as f:
                f.write(audio_data)
            
            size_kb = len(audio_data) / 1024
            print(f"OK ({size_kb:.1f} KB)")
            
            results.append({
                'voice_id': v['voice_id'],
                'name': v['name'],
                'speaker_id': v['speaker_id'],
                'gender': 'female',
                'filepath': str(filepath),
                'size_kb': size_kb,
                'status': 'success'
            })
            
        except Exception as e:
            print(f"ERROR: {e}")
            results.append({
                'voice_id': v['voice_id'],
                'name': v['name'],
                'speaker_id': v['speaker_id'],
                'gender': 'female',
                'status': 'error',
                'error': str(e)
            })
    
    # Summary
    print()
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    successful = [r for r in results if r['status'] == 'success']
    errors = [r for r in results if r['status'] == 'error']
    
    print(f"Total: 8 voices")
    print(f"Successful: {len(successful)}")
    print(f"Errors: {len(errors)}")
    print()
    print(f"Output directory: {OUTPUT_DIR}")
    print(f"  - Male voices: {male_dir}")
    print(f"  - Female voices: {female_dir}")
    
    # Write summary file
    summary_file = OUTPUT_DIR / "voice_summary.txt"
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write("FINAL VERIFIED VOICES\n")
        f.write("=" * 60 + "\n")
        f.write(f"Date: {datetime.now().isoformat()}\n")
        f.write(f"Test text: {TEST_TEXT}\n\n")
        
        f.write("MALE VOICES:\n")
        f.write("-" * 40 + "\n")
        for v in MALE_VOICES:
            f.write(f"  {v['voice_id']}: {v['name']} (speaker_id: {v['speaker_id']})\n")
            f.write(f"    Description: {v['description']}\n")
        
        f.write("\nFEMALE VOICES:\n")
        f.write("-" * 40 + "\n")
        for v in FEMALE_VOICES:
            f.write(f"  {v['voice_id']}: {v['name']} (speaker_id: {v['speaker_id']})\n")
            f.write(f"    Description: {v['description']}\n")
        
        f.write("\n" + "=" * 60 + "\n")
        f.write("API USAGE:\n")
        f.write("-" * 40 + "\n")
        f.write("Valid voice_id values:\n")
        f.write("  Male: male_1, male_2, male_3, male_4\n")
        f.write("  Female: female_1, female_2, female_3, female_4\n")
    
    print()
    print(f"Summary saved to: {summary_file}")
    print()
    print("=" * 60)
    print("AVAILABLE VOICES FOR API:")
    print("=" * 60)
    print("Male:   male_1 (Alex), male_2 (Christopher), male_3 (Daniel), male_4 (John)")
    print("Female: female_1 (Stephanie), female_2 (Sarah), female_3 (Olivia), female_4 (Emma)")


if __name__ == "__main__":
    test_final_voices()
