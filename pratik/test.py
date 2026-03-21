"""
Test script for Practice (Pratik) API endpoints.

Run this script to test the conversation practice functionality.
"""

import asyncio
import httpx
import json

BASE_URL = "http://localhost:8000/api/v1/practice"


async def test_create_scenario():
    """Test creating a new conversation scenario."""
    print("\n" + "="*60)
    print("TEST 1: Creating a new conversation scenario")
    print("="*60)
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/create-scenario",
            json={
                "topic": "Weekend hobbies and activities",
                "ai_role": "friend",
                "difficulty": "intermediate",
                "vocabulary_words": ["hiking", "photography", "relaxing", "exciting"],
                "additional_context": "Focus on past tense and expressing opinions",
                "user_name": "Alex",
                "target_exchanges": 5
            },
            timeout=60.0
        )
        
        print(f"Status: {response.status_code}")
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2)}")
        
        return data.get("session_id")


async def test_conversation(session_id: str):
    """Test having a conversation."""
    print("\n" + "="*60)
    print("TEST 2: Having a conversation")
    print("="*60)
    
    messages = [
        "I went hiking last weekend in the mountains. It was really refreshing!",
        "Yes, I took many photos of the sunset. Photography is my favorite hobby.",
        "I usually go hiking every Saturday morning. Sometimes my friends join me.",
        "I think hiking helps me relax and forget about work stress.",
        "Thank you for the nice conversation! Goodbye!"
    ]
    
    async with httpx.AsyncClient() as client:
        for i, message in enumerate(messages, 1):
            print(f"\n--- Turn {i} ---")
            print(f"User: {message}")
            
            response = await client.post(
                f"{BASE_URL}/send-message",
                json={
                    "session_id": session_id,
                    "user_message": message
                },
                timeout=60.0
            )
            
            data = response.json()
            print(f"AI: {data.get('ai_message', 'No response')}")
            
            feedback = data.get('feedback', {})
            if feedback.get('praise'):
                print(f"✓ Praise: {feedback['praise']}")
            if feedback.get('corrections'):
                print(f"✗ Corrections: {feedback['corrections']}")
            
            print(f"Progress: {data.get('current_exchange')}/{data.get('total_exchanges')}")
            
            if data.get('conversation_ended'):
                print("\n🎉 Conversation completed!")
                print(f"Summary: {json.dumps(data.get('session_summary'), indent=2)}")
                break
            
            await asyncio.sleep(1)  # Small delay between messages


async def test_different_roles():
    """Test creating scenarios with different AI roles."""
    print("\n" + "="*60)
    print("TEST 3: Testing different AI roles")
    print("="*60)
    
    roles = [
        ("teacher", "Grammar practice", "Learning English grammar"),
        ("recruiter", "Job interview", "Applying for a software developer position"),
        ("doctor", "Health checkup", "Discussing healthy lifestyle choices"),
    ]
    
    async with httpx.AsyncClient() as client:
        for role, topic, context in roles:
            print(f"\n--- Role: {role.upper()} ---")
            
            response = await client.post(
                f"{BASE_URL}/create-scenario",
                json={
                    "topic": topic,
                    "ai_role": role,
                    "difficulty": "intermediate",
                    "additional_context": context,
                    "target_exchanges": 3
                },
                timeout=60.0
            )
            
            data = response.json()
            print(f"Opening: {data.get('opening_message', 'No message')[:100]}...")
            print(f"Session ID: {data.get('session_id')}")


async def test_health():
    """Test health endpoint."""
    print("\n" + "="*60)
    print("TEST: Health Check")
    print("="*60)
    
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")


async def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("PRACTICE API TEST SUITE")
    print("="*60)
    
    # Health check
    await test_health()
    
    # Create scenario and have conversation
    session_id = await test_create_scenario()
    
    if session_id:
        await test_conversation(session_id)
    
    # Test different roles
    await test_different_roles()
    
    print("\n" + "="*60)
    print("ALL TESTS COMPLETED")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())
