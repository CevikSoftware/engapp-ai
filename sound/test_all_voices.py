"""
TTS Voice Tester
Tests all voice presets and saves audio files with gender labels.
Helps identify which speaker_ids sound male or female.
"""

import os
import sys
import wave
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from piper import PiperVoice
    from piper.config import SynthesisConfig
    PIPER_AVAILABLE = True
except ImportError:
    PIPER_AVAILABLE = False
    print("ERROR: piper-tts not installed. Run: pip install piper-tts")
    sys.exit(1)


# Output directory for test audio files
OUTPUT_DIR = Path(__file__).parent / "output"

# Model paths
MODEL_DIR = Path(__file__).parent.parent.parent
MODEL_PATH = MODEL_DIR / "en_US-libritts-high.onnx"
CONFIG_PATH = MODEL_DIR / "en_US-libritts-high.onnx.json"

# Test sentence
TEST_TEXT = "Hello, this is a test of the voice synthesis system. How does this voice sound to you?"

# Voice configurations to test
# Format: (speaker_id, expected_gender, name)
VOICES_TO_TEST = [
    # === MALE VOICES ===
    (300, "male", "Alex"),
    (190, "male", "Christopher"),
    (70, "male", "Daniel"),
    (212, "male", "John"),
    
    # === FEMALE VOICES ===
    (170, "female", "Stephanie"),
    (10, "female", "Sarah"),
    (118, "female", "Olivia"),
    (115, "female", "Emma"),
]


def synthesize_audio(voice: PiperVoice, text: str, speaker_id: int) -> bytes:
    """Synthesize text to audio bytes."""
    import io
    
    audio_buffer = io.BytesIO()
    
    # Create synthesis config with speaker_id
    syn_config = SynthesisConfig(
        speaker_id=speaker_id,
        length_scale=1.0,
        noise_scale=0.667
    )
    
    # Synthesize and collect audio chunks
    audio_chunks = list(voice.synthesize(text, syn_config))
    
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
    
    # Write WAV to buffer
    with wave.open(audio_buffer, 'wb') as wav_file:
        wav_file.setnchannels(channels)
        wav_file.setsampwidth(sample_width)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(all_audio)
    
    return audio_buffer.getvalue()


def test_all_voices():
    """Test all configured voices and save to output directory."""
    
    print("=" * 60)
    print("TTS Voice Tester")
    print("=" * 60)
    
    # Check model
    if not MODEL_PATH.exists():
        print(f"ERROR: Model not found at {MODEL_PATH}")
        return
    
    print(f"Model: {MODEL_PATH}")
    print(f"Test text: '{TEST_TEXT}'")
    print()
    
    # Create output directory
    OUTPUT_DIR.mkdir(exist_ok=True)
    
    # Create subdirectories for organization
    female_dir = OUTPUT_DIR / "female"
    male_dir = OUTPUT_DIR / "male"
    unknown_dir = OUTPUT_DIR / "unknown"
    
    female_dir.mkdir(exist_ok=True)
    male_dir.mkdir(exist_ok=True)
    unknown_dir.mkdir(exist_ok=True)
    
    print("Loading Piper model...")
    voice = PiperVoice.load(
        str(MODEL_PATH),
        config_path=str(CONFIG_PATH),
        use_cuda=False
    )
    print("Model loaded successfully!")
    print()
    
    # Results tracking
    results = []
    errors = []
    
    print(f"Testing {len(VOICES_TO_TEST)} voices...")
    print("-" * 60)
    
    for i, (speaker_id, expected_gender, name) in enumerate(VOICES_TO_TEST, 1):
        try:
            print(f"[{i}/{len(VOICES_TO_TEST)}] Testing speaker {speaker_id} ({name}, expected: {expected_gender})...", end=" ")
            
            # Generate audio
            audio_data = synthesize_audio(voice, TEST_TEXT, speaker_id)
            
            # Determine output directory
            if expected_gender == "female":
                out_dir = female_dir
            elif expected_gender == "male":
                out_dir = male_dir
            else:
                out_dir = unknown_dir
            
            # Save file with descriptive name
            filename = f"{expected_gender}_{speaker_id:03d}_{name}.wav"
            filepath = out_dir / filename
            
            with open(filepath, 'wb') as f:
                f.write(audio_data)
            
            file_size_kb = len(audio_data) / 1024
            print(f"OK ({file_size_kb:.1f} KB) -> {filepath.name}")
            
            results.append({
                'speaker_id': speaker_id,
                'expected_gender': expected_gender,
                'name': name,
                'filepath': str(filepath),
                'size_kb': file_size_kb,
                'status': 'success'
            })
            
        except Exception as e:
            print(f"ERROR: {e}")
            errors.append({
                'speaker_id': speaker_id,
                'name': name,
                'error': str(e)
            })
    
    print()
    print("=" * 60)
    print("RESULTS SUMMARY")
    print("=" * 60)
    print(f"Total tested: {len(VOICES_TO_TEST)}")
    print(f"Successful: {len(results)}")
    print(f"Errors: {len(errors)}")
    print()
    print(f"Output directory: {OUTPUT_DIR}")
    print(f"  - Female voices: {female_dir}")
    print(f"  - Male voices: {male_dir}")
    print(f"  - Unknown voices: {unknown_dir}")
    
    if errors:
        print()
        print("ERRORS:")
        for err in errors:
            print(f"  - Speaker {err['speaker_id']} ({err['name']}): {err['error']}")
    
    # Write results to a log file
    log_file = OUTPUT_DIR / f"test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(log_file, 'w', encoding='utf-8') as f:
        f.write("TTS Voice Test Results\n")
        f.write("=" * 60 + "\n")
        f.write(f"Date: {datetime.now().isoformat()}\n")
        f.write(f"Test text: {TEST_TEXT}\n")
        f.write(f"Model: {MODEL_PATH}\n")
        f.write("\n")
        
        f.write("SUCCESSFUL:\n")
        f.write("-" * 40 + "\n")
        for r in results:
            f.write(f"Speaker {r['speaker_id']:3d} | {r['expected_gender']:7s} | {r['name']:20s} | {r['size_kb']:.1f} KB\n")
        
        if errors:
            f.write("\nERRORS:\n")
            f.write("-" * 40 + "\n")
            for err in errors:
                f.write(f"Speaker {err['speaker_id']:3d} | {err['name']:20s} | {err['error']}\n")
    
    print()
    print(f"Results log saved to: {log_file}")
    print()
    print("Listen to the audio files and update VOICE_PRESETS accordingly!")


def test_specific_range(start: int, end: int, step: int = 10):
    """Test a specific range of speaker IDs."""
    
    print(f"Testing speaker IDs from {start} to {end} (step: {step})")
    
    if not MODEL_PATH.exists():
        print(f"ERROR: Model not found at {MODEL_PATH}")
        return
    
    OUTPUT_DIR.mkdir(exist_ok=True)
    range_dir = OUTPUT_DIR / f"range_{start}_{end}"
    range_dir.mkdir(exist_ok=True)
    
    print("Loading model...")
    voice = PiperVoice.load(
        str(MODEL_PATH),
        config_path=str(CONFIG_PATH),
        use_cuda=False
    )
    
    for speaker_id in range(start, end + 1, step):
        try:
            print(f"Testing speaker {speaker_id}...", end=" ")
            audio_data = synthesize_audio(voice, TEST_TEXT, speaker_id)
            
            filename = f"speaker_{speaker_id:04d}.wav"
            filepath = range_dir / filename
            
            with open(filepath, 'wb') as f:
                f.write(audio_data)
            
            print(f"OK -> {filename}")
            
        except Exception as e:
            print(f"ERROR: {e}")
    
    print(f"\nOutput saved to: {range_dir}")


def test_single_speaker(speaker_id: int, text: str = None):
    """Test a single speaker ID."""
    
    if text is None:
        text = TEST_TEXT
    
    if not MODEL_PATH.exists():
        print(f"ERROR: Model not found at {MODEL_PATH}")
        return
    
    OUTPUT_DIR.mkdir(exist_ok=True)
    
    print(f"Testing speaker {speaker_id}...")
    print(f"Text: '{text}'")
    
    voice = PiperVoice.load(
        str(MODEL_PATH),
        config_path=str(CONFIG_PATH),
        use_cuda=False
    )
    
    audio_data = synthesize_audio(voice, text, speaker_id)
    
    filename = f"test_speaker_{speaker_id}.wav"
    filepath = OUTPUT_DIR / filename
    
    with open(filepath, 'wb') as f:
        f.write(audio_data)
    
    print(f"Saved to: {filepath}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="TTS Voice Tester")
    parser.add_argument("--range", nargs=3, type=int, metavar=("START", "END", "STEP"),
                        help="Test a range of speaker IDs (start, end, step)")
    parser.add_argument("--speaker", type=int, help="Test a single speaker ID")
    parser.add_argument("--text", type=str, help="Custom text to speak")
    
    args = parser.parse_args()
    
    if args.range:
        test_specific_range(args.range[0], args.range[1], args.range[2])
    elif args.speaker is not None:
        test_single_speaker(args.speaker, args.text)
    else:
        # Run full test
        test_all_voices()
