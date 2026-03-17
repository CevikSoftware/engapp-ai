"""
Test script for Listening API - Downloads and saves audio from Base64 response

Usage:
    python test.py                    # Interactive mode
    python test.py --quick            # Quick test with defaults
    python test.py --voice female_3 male_2 --speed 1.25
"""

import requests
import base64
import argparse
from pathlib import Path

# API Configuration
API_BASE_URL = "http://localhost:8000/api/v1"  # Adjust port if needed

# Output directory for audio files
OUTPUT_DIR = Path(__file__).parent / "test_audio_output"
OUTPUT_DIR.mkdir(exist_ok=True)


def get_available_voices():
    """
    Get all available voices from the API.
    Returns dict with 'male' and 'female' voice lists.
    """
    url = f"{API_BASE_URL}/listening/voices"
    
    print("\n" + "=" * 60)
    print("📋 Available Voices")
    print("=" * 60)
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        print("\n🎤 MALE VOICES:")
        print("-" * 50)
        for voice in data['male']:
            print(f"  {voice['voice_id']:<10} | {voice['name']:<12} | {voice['description']}")
        
        print("\n🎤 FEMALE VOICES:")
        print("-" * 50)
        for voice in data['female']:
            print(f"  {voice['voice_id']:<10} | {voice['name']:<12} | {voice['description']}")
        
        return data
        
    except requests.exceptions.ConnectionError:
        print("\n❌ Connection Error: Could not connect to API")
        print("   Make sure the server is running: python main.py")
        return None
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return None


def generate_conversation_with_audio(
    topic: str = "Ordering coffee at a cafe",
    difficulty: str = "intermediate",
    length: str = "short",
    character1: str = "Sarah",
    character2: str = "Barista",
    gender1: str = "female",
    gender2: str = "male",
    voice_id1: str = None,
    voice_id2: str = None,
    speech_speed: float = 1.0,
    special_details: str = None
):
    """
    Generate a conversation with audio using the API.
    
    Args:
        topic: Conversation topic
        difficulty: beginner, elementary, intermediate, upper_intermediate, advanced
        length: short, medium, long
        character1: Name of first character
        character2: Name of second character
        gender1: male or female
        gender2: male or female
        voice_id1: Specific voice ID for character1 (e.g., 'female_1')
        voice_id2: Specific voice ID for character2 (e.g., 'male_3')
        speech_speed: 0.5 (fast) to 2.0 (slow), default 1.0
        special_details: Additional instructions for conversation
    
    Returns:
        API response data or None on error
    """
    
    # Build request payload
    payload = {
        "topic": topic,
        "difficulty": difficulty,
        "length": length,
        "character1": character1,
        "character2": character2,
        "gender1": gender1,
        "gender2": gender2,
        "speech_speed": speech_speed
    }
    
    # Add optional parameters
    if voice_id1:
        payload["voice_id1"] = voice_id1
    if voice_id2:
        payload["voice_id2"] = voice_id2
    if special_details:
        payload["special_details"] = special_details
    
    print("\n" + "=" * 60)
    print("🎧 Generating Conversation with Audio")
    print("=" * 60)
    print("\n📝 Request Parameters:")
    for key, value in payload.items():
        print(f"   {key}: {value}")
    
    url = f"{API_BASE_URL}/listening/generate-conversation-with-audio"
    print(f"\n🌐 POST {url}")
    print("   ⏳ Generating... (this may take a moment)")
    
    try:
        response = requests.post(url, json=payload, timeout=180)
        response.raise_for_status()
        
        data = response.json()
        
        if data.get("success"):
            print("\n✅ Success!")
            print(f"\n📌 Topic: {data['topic']}")
            print(f"📊 Difficulty: {data['difficulty']}")
            print(f"👤 {data['character1']} ({data['gender1']}) & {data['character2']} ({data['gender2']})")
            
            # Print dialogue
            print("\n" + "-" * 50)
            print("💬 DIALOGUE:")
            print("-" * 50)
            for line in data['dialogue']:
                print(f"   {line['speaker']}: {line['text']}")
            
            # Save audio files
            print("\n" + "-" * 50)
            print("💾 SAVING AUDIO FILES:")
            print("-" * 50)
            
            total_size = 0
            for audio_info in data['audio_files']:
                filename = audio_info['filename']
                audio_base64 = audio_info['audio_data']
                
                # Decode Base64 to bytes
                audio_bytes = base64.b64decode(audio_base64)
                total_size += len(audio_bytes)
                
                # Save to file
                output_path = OUTPUT_DIR / filename
                with open(output_path, 'wb') as f:
                    f.write(audio_bytes)
                
                file_size_kb = len(audio_bytes) / 1024
                text_preview = audio_info['text'][:40] + "..." if len(audio_info['text']) > 40 else audio_info['text']
                print(f"   ✅ {filename:<20} ({file_size_kb:>6.1f} KB) - {text_preview}")
            
            print(f"\n📁 Output: {OUTPUT_DIR}")
            print(f"📊 Total: {len(data['audio_files'])} files, {total_size/1024:.1f} KB")
            
            return data
            
        else:
            print("\n❌ API returned unsuccessful response")
            print(f"   Response: {data}")
            return None
            
    except requests.exceptions.ConnectionError:
        print("\n❌ Connection Error: Could not connect to API")
        print("   Make sure the server is running!")
        return None
        
    except requests.exceptions.Timeout:
        print("\n❌ Timeout: Request took too long (>180s)")
        return None
        
    except requests.exceptions.HTTPError as e:
        print(f"\n❌ HTTP Error: {e}")
        try:
            print(f"   Detail: {response.json().get('detail', response.text)}")
        except:
            print(f"   Response: {response.text}")
        return None
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return None


def interactive_mode():
    """
    Interactive mode for customizing all parameters.
    """
    print("\n" + "=" * 60)
    print("🎛️  Interactive Configuration")
    print("=" * 60)
    
    # Show voices first
    voices = get_available_voices()
    if not voices:
        return
    
    # Topic
    print("\n📌 Enter conversation topic (or press Enter for default):")
    print("   Default: 'Ordering coffee at a cafe'")
    topic = input("   > ").strip() or "Ordering coffee at a cafe"
    
    # Difficulty
    print("\n📊 Select difficulty:")
    print("   1. beginner")
    print("   2. elementary")
    print("   3. intermediate (default)")
    print("   4. upper_intermediate")
    print("   5. advanced")
    diff_choice = input("   > ").strip()
    difficulties = ["beginner", "elementary", "intermediate", "upper_intermediate", "advanced"]
    difficulty = difficulties[int(diff_choice)-1] if diff_choice.isdigit() and 1 <= int(diff_choice) <= 5 else "intermediate"
    
    # Length
    print("\n📏 Select length:")
    print("   1. short (default)")
    print("   2. medium")
    print("   3. long")
    len_choice = input("   > ").strip()
    lengths = ["short", "medium", "long"]
    length = lengths[int(len_choice)-1] if len_choice.isdigit() and 1 <= int(len_choice) <= 3 else "short"
    
    # Characters
    print("\n👤 Character 1 name (default: Sarah):")
    character1 = input("   > ").strip() or "Sarah"
    
    print("\n👤 Character 2 name (default: John):")
    character2 = input("   > ").strip() or "John"
    
    # Genders
    print(f"\n🎭 Gender for {character1} (male/female, default: female):")
    gender1 = input("   > ").strip().lower() or "female"
    gender1 = gender1 if gender1 in ["male", "female"] else "female"
    
    print(f"\n🎭 Gender for {character2} (male/female, default: male):")
    gender2 = input("   > ").strip().lower() or "male"
    gender2 = gender2 if gender2 in ["male", "female"] else "male"
    
    # Voice IDs
    print(f"\n🎤 Voice ID for {character1} (e.g., female_1, or Enter for auto):")
    voice_id1 = input("   > ").strip() or None
    
    print(f"\n🎤 Voice ID for {character2} (e.g., male_2, or Enter for auto):")
    voice_id2 = input("   > ").strip() or None
    
    # Speech speed
    print("\n⏱️  Speech speed:")
    print("   0.5  = Very fast")
    print("   0.75 = Fast")
    print("   1.0  = Normal (default)")
    print("   1.25 = Slow")
    print("   1.5  = Very slow")
    print("   2.0  = Extra slow")
    speed_input = input("   > ").strip()
    try:
        speech_speed = float(speed_input) if speed_input else 1.0
        speech_speed = max(0.25, min(3.0, speech_speed))
    except ValueError:
        speech_speed = 1.0
    
    # Generate
    generate_conversation_with_audio(
        topic=topic,
        difficulty=difficulty,
        length=length,
        character1=character1,
        character2=character2,
        gender1=gender1,
        gender2=gender2,
        voice_id1=voice_id1,
        voice_id2=voice_id2,
        speech_speed=speech_speed
    )


def quick_test():
    """Quick test with sensible defaults."""
    print("\n🚀 Quick Test Mode")
    generate_conversation_with_audio(
        topic="Meeting a new colleague at work",
        difficulty="intermediate",
        length="short",
        character1="Emma",
        character2="David",
        gender1="female",
        gender2="male",
        voice_id1="female_2",
        voice_id2="male_3",
        speech_speed=1.0,
        special_details="Include introducing themselves and asking about their roles"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test the Listening API")
    parser.add_argument("--quick", "-q", action="store_true", help="Quick test with defaults")
    parser.add_argument("--topic", "-t", type=str, help="Conversation topic")
    parser.add_argument("--difficulty", "-d", type=str, choices=["beginner", "elementary", "intermediate", "upper_intermediate", "advanced"], default="intermediate")
    parser.add_argument("--length", "-l", type=str, choices=["short", "medium", "long"], default="short")
    parser.add_argument("--voice1", type=str, help="Voice ID for character 1 (e.g., female_1)")
    parser.add_argument("--voice2", type=str, help="Voice ID for character 2 (e.g., male_2)")
    parser.add_argument("--speed", "-s", type=float, default=1.0, help="Speech speed (0.5-2.0)")
    parser.add_argument("--voices", "-v", action="store_true", help="List available voices")
    
    args = parser.parse_args()
    
    print("\n" + "=" * 60)
    print("🎧 Listening API Test Script")
    print("=" * 60)
    
    if args.voices:
        get_available_voices()
    elif args.quick:
        quick_test()
    elif args.topic:
        # Direct mode with arguments
        generate_conversation_with_audio(
            topic=args.topic,
            difficulty=args.difficulty,
            length=args.length,
            voice_id1=args.voice1,
            voice_id2=args.voice2,
            speech_speed=args.speed
        )
    else:
        # Interactive mode
        print("\nOptions:")
        print("  1. Interactive mode (customize everything)")
        print("  2. Quick test (use defaults)")
        print("  3. Show available voices")
        
        choice = input("\nSelect (1/2/3): ").strip()
        
        if choice == "1":
            interactive_mode()
        elif choice == "2":
            quick_test()
        elif choice == "3":
            get_available_voices()
        else:
            print("Invalid choice, running quick test...")
            quick_test()
    
    print("\n" + "=" * 60)
    print("✅ Done!")
    print("=" * 60)
