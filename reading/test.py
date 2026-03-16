"""
Test script for Reading Practice API
"""

import requests
import argparse
from pathlib import Path

# API Configuration
API_BASE_URL = "http://localhost:8000/api/v1"


def get_options():
    """Fetch and display all available options."""
    print("\n" + "=" * 60)
    print("📋 Available Options")
    print("=" * 60)
    
    try:
        # Content Types
        response = requests.get(f"{API_BASE_URL}/reading/content-types", timeout=10)
        if response.ok:
            data = response.json()
            print("\n📝 CONTENT TYPES:")
            print("-" * 50)
            for ct in data['content_types']:
                print(f"  {ct['value']:<15} | {ct['description']}")
        
        # Difficulty Levels
        response = requests.get(f"{API_BASE_URL}/reading/difficulty-levels", timeout=10)
        if response.ok:
            data = response.json()
            print("\n📊 DIFFICULTY LEVELS:")
            print("-" * 50)
            for dl in data['difficulty_levels']:
                print(f"  {dl['value']:<20} | {dl['name']}")
        
        # Text Lengths
        response = requests.get(f"{API_BASE_URL}/reading/text-lengths", timeout=10)
        if response.ok:
            data = response.json()
            print("\n📏 TEXT LENGTHS:")
            print("-" * 50)
            for tl in data['text_lengths']:
                print(f"  {tl['value']:<12} | {tl['description']}")
        
        # Writing Styles
        response = requests.get(f"{API_BASE_URL}/reading/writing-styles", timeout=10)
        if response.ok:
            data = response.json()
            print("\n✍️  WRITING STYLES (optional):")
            print("-" * 50)
            for ws in data['writing_styles']:
                print(f"  {ws['value']:<15} | {ws['description']}")
        
        # Tense Preferences
        response = requests.get(f"{API_BASE_URL}/reading/tense-preferences", timeout=10)
        if response.ok:
            data = response.json()
            print("\n⏰ TENSE PREFERENCES (optional):")
            print("-" * 50)
            for tp in data['tense_preferences']:
                print(f"  {tp['value']:<12} | {tp['description']}")
        
        return True
        
    except requests.exceptions.ConnectionError:
        print("\n❌ Connection Error: Could not connect to API")
        print("   Make sure the server is running: python api.py")
        return False
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False


def generate_text(
    concept: str,
    content_type: str = "article",
    difficulty: str = "intermediate",
    length: str = "medium",
    required_words: list = None,
    writing_style: str = None,
    tense_preference: str = None,
    additional_details: str = None
):
    """Generate a reading text using the API."""
    
    if required_words is None:
        required_words = ["example", "important", "learn"]
    
    payload = {
        "concept": concept,
        "content_type": content_type,
        "difficulty": difficulty,
        "length": length,
        "required_words": required_words
    }
    
    if writing_style:
        payload["writing_style"] = writing_style
    if tense_preference:
        payload["tense_preference"] = tense_preference
    if additional_details:
        payload["additional_details"] = additional_details
    
    print("\n" + "=" * 60)
    print("📝 Generating Reading Text")
    print("=" * 60)
    print("\n📋 Request Parameters:")
    for key, value in payload.items():
        if key == "required_words":
            print(f"   {key}: {', '.join(value)}")
        else:
            print(f"   {key}: {value}")
    
    url = f"{API_BASE_URL}/reading/generate-text"
    print(f"\n🌐 POST {url}")
    print("   ⏳ Generating... (this may take a moment)")
    
    try:
        response = requests.post(url, json=payload, timeout=120)
        response.raise_for_status()
        
        data = response.json()
        
        if data.get("success"):
            print("\n✅ Success!")
            print(f"\n📌 Title: {data['title']}")
            print(f"📊 Difficulty: {data['difficulty']}")
            print(f"📝 Content Type: {data['content_type']}")
            print(f"📏 Word Count: {data['word_count']}")
            
            print("\n" + "-" * 50)
            print("📖 GENERATED TEXT:")
            print("-" * 50)
            print(data['text'])
            
            print("\n" + "-" * 50)
            print("✅ Required Words Used:")
            print(f"   {', '.join(data['required_words_used'])}")
            
            if data['required_words_missing']:
                print("\n⚠️  Required Words MISSING:")
                print(f"   {', '.join(data['required_words_missing'])}")
            else:
                print("\n✅ All required words were used!")
            
            return data
        else:
            print("\n❌ API returned unsuccessful response")
            print(f"   Response: {data}")
            return None
            
    except requests.exceptions.ConnectionError:
        print("\n❌ Connection Error: Could not connect to API")
        print("   Make sure the server is running!")
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


def quick_test():
    """Run a quick test with example parameters."""
    print("\n🚀 Quick Test Mode")
    
    generate_text(
        concept="The benefits of learning English as a second language",
        content_type="article",
        difficulty="intermediate",
        length="medium",
        required_words=["language", "communication", "opportunity", "global", "career", "culture"],
        writing_style="neutral",
        tense_preference="present",
        additional_details="Focus on practical benefits for young professionals"
    )


def interactive_mode():
    """Interactive mode for customizing parameters."""
    print("\n" + "=" * 60)
    print("🎛️  Interactive Text Generation")
    print("=" * 60)
    
    # Show options first
    if not get_options():
        return
    
    print("\n" + "=" * 60)
    print("Enter your parameters:")
    print("=" * 60)
    
    # Concept
    print("\n📌 Enter the concept/topic:")
    concept = input("   > ").strip() or "Learning a new skill"
    
    # Content Type
    print("\n📝 Content type (article, story, email, etc.):")
    content_type = input("   > ").strip() or "article"
    
    # Difficulty
    print("\n📊 Difficulty (beginner, elementary, intermediate, upper_intermediate, advanced):")
    difficulty = input("   > ").strip() or "intermediate"
    
    # Length
    print("\n📏 Length (short, medium, long, very_long):")
    length = input("   > ").strip() or "medium"
    
    # Required Words
    print("\n📚 Required words (comma-separated):")
    print("   Example: learn, practice, improve, skill, success")
    words_input = input("   > ").strip()
    required_words = [w.strip() for w in words_input.split(",")] if words_input else ["learn", "important", "practice"]
    
    # Writing Style (optional)
    print("\n✍️  Writing style (optional, press Enter to skip):")
    writing_style = input("   > ").strip() or None
    
    # Tense Preference (optional)
    print("\n⏰ Tense preference (optional, press Enter to skip):")
    tense_preference = input("   > ").strip() or None
    
    # Additional Details (optional)
    print("\n📝 Additional details (optional, press Enter to skip):")
    additional_details = input("   > ").strip() or None
    
    # Generate
    generate_text(
        concept=concept,
        content_type=content_type,
        difficulty=difficulty,
        length=length,
        required_words=required_words,
        writing_style=writing_style,
        tense_preference=tense_preference,
        additional_details=additional_details
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test the Reading Practice API")
    parser.add_argument("--quick", "-q", action="store_true", help="Quick test with defaults")
    parser.add_argument("--options", "-o", action="store_true", help="Show available options")
    parser.add_argument("--concept", "-c", type=str, help="Topic/concept for the text")
    parser.add_argument("--type", "-t", type=str, default="article", help="Content type")
    parser.add_argument("--difficulty", "-d", type=str, default="intermediate", help="Difficulty level")
    parser.add_argument("--length", "-l", type=str, default="medium", help="Text length")
    parser.add_argument("--words", "-w", type=str, help="Required words (comma-separated)")
    parser.add_argument("--style", "-s", type=str, help="Writing style")
    parser.add_argument("--tense", type=str, help="Tense preference")
    
    args = parser.parse_args()
    
    print("\n" + "=" * 60)
    print("📖  Reading Practice API Test Script")
    print("=" * 60)
    
    if args.options:
        get_options()
    elif args.quick:
        quick_test()
    elif args.concept:
        # Direct mode with arguments
        words = [w.strip() for w in args.words.split(",")] if args.words else ["example", "important", "learn"]
        generate_text(
            concept=args.concept,
            content_type=args.type,
            difficulty=args.difficulty,
            length=args.length,
            required_words=words,
            writing_style=args.style,
            tense_preference=args.tense
        )
    else:
        # Interactive menu
        print("\nOptions:")
        print("  1. Interactive mode (customize everything)")
        print("  2. Quick test (use defaults)")
        print("  3. Show available options")
        
        choice = input("\nSelect (1/2/3): ").strip()
        
        if choice == "1":
            interactive_mode()
        elif choice == "2":
            quick_test()
        elif choice == "3":
            get_options()
        else:
            print("Invalid choice, running quick test...")
            quick_test()
    
    print("\n" + "=" * 60)
    print("✅ Done!")
    print("=" * 60)
