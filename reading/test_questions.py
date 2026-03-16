"""
Test script for Question Generator API
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_generate_questions():
    """Test the generate-questions endpoint."""
    
    # Sample reading text
    reading_text = """
    Climate change is one of the most pressing issues facing our planet today. 
    Scientists have observed significant changes in global temperatures over the past century, 
    with the average temperature rising by approximately 1.1 degrees Celsius since the pre-industrial era.
    
    The main cause of this warming is the increased concentration of greenhouse gases in the atmosphere, 
    primarily carbon dioxide from burning fossil fuels. These gases trap heat from the sun, 
    creating a "greenhouse effect" that warms the Earth's surface.
    
    The effects of climate change are already visible around the world. Glaciers are melting, 
    sea levels are rising, and extreme weather events are becoming more frequent and severe. 
    Many species are struggling to adapt to these rapid changes in their environments.
    
    To address this crisis, governments and organizations worldwide are working to reduce 
    greenhouse gas emissions and transition to renewable energy sources. Individual actions, 
    such as reducing energy consumption and using public transportation, also play an important role 
    in the fight against climate change.
    """
    
    # Test request
    request_data = {
        "reading_text": reading_text,
        "difficulty": "intermediate",
        "question_count": 5,
        "keywords": ["climate change", "greenhouse gases", "renewable energy", "temperature"],
        "additional_instructions": "Include at least one vocabulary question and one main idea question"
    }
    
    print("=" * 60)
    print("Testing Question Generation API")
    print("=" * 60)
    
    try:
        response = requests.post(
            f"{BASE_URL}/reading/generate-questions",
            json=request_data
        )
        
        print(f"\nStatus Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"\nSuccess: {result['success']}")
            print(f"Difficulty: {result['difficulty']}")
            print(f"Question Count: {result['question_count']}")
            print("\n" + "=" * 60)
            print("Generated Questions:")
            print("=" * 60)
            
            for q in result['questions']:
                print(f"\nQuestion {q['question_number']}: {q['question_text']}")
                for opt in q['options']:
                    correct_marker = " ✓" if opt['is_correct'] else ""
                    print(f"  {opt['label']}) {opt['text']}{correct_marker}")
                print(f"  Correct Answer: {q['correct_answer']}")
                print(f"  Explanation: {q['explanation']}")
        else:
            print(f"\nError: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("\nError: Could not connect to the API. Make sure the server is running.")
    except Exception as e:
        print(f"\nError: {e}")


def test_difficulty_levels():
    """Test the question difficulty levels endpoint."""
    
    print("\n" + "=" * 60)
    print("Testing Question Difficulty Levels Endpoint")
    print("=" * 60)
    
    try:
        response = requests.get(f"{BASE_URL}/reading/question-difficulty-levels")
        
        if response.status_code == 200:
            result = response.json()
            print("\nAvailable Difficulty Levels:")
            for level in result['difficulty_levels']:
                print(f"\n  {level['name']} ({level['value']})")
                print(f"    {level['description']}")
        else:
            print(f"\nError: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("\nError: Could not connect to the API. Make sure the server is running.")


def test_beginner_questions():
    """Test generating beginner level questions."""
    
    reading_text = """
    My name is Tom. I am a student. I go to school every day.
    I like to read books. My favorite subject is English.
    I have many friends at school. We play together after class.
    """
    
    request_data = {
        "reading_text": reading_text,
        "difficulty": "beginner",
        "question_count": 3
    }
    
    print("\n" + "=" * 60)
    print("Testing Beginner Level Questions")
    print("=" * 60)
    
    try:
        response = requests.post(
            f"{BASE_URL}/reading/generate-questions",
            json=request_data
        )
        
        if response.status_code == 200:
            result = response.json()
            for q in result['questions']:
                print(f"\nQ{q['question_number']}: {q['question_text']}")
                for opt in q['options']:
                    print(f"  {opt['label']}) {opt['text']}")
                print(f"  Answer: {q['correct_answer']}")
        else:
            print(f"\nError: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("\nError: Could not connect to the API.")


if __name__ == "__main__":
    # Run tests
    test_difficulty_levels()
    test_generate_questions()
    test_beginner_questions()
