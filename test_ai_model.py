#!/usr/bin/env python3
"""
Test script to verify the Hugging Face AI model is working correctly
"""

import os
from huggingface_hub import InferenceClient
import json

# Use the same token and model as in quiz_generator.py
HF_ACCESS_TOKEN = "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"
HF_MODEL = "deepseek-ai/DeepSeek-R1-0528-Qwen3-8B"

def test_ai_connection():
    """Test basic AI model connection"""
    print("🧪 Testing AI model connection...")
    
    try:
        client = InferenceClient(
            model=HF_MODEL,
            token=HF_ACCESS_TOKEN,
            timeout=60,
        )
        
        # Simple test prompt
        test_prompt = "Generate a simple JSON object with one field 'test' set to 'success'"
        
        completion = client.chat.completions.create(
            model=HF_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": test_prompt
                }
            ],
            temperature=0.1,
            max_tokens=100
        )
        
        print("✅ AI model connection successful!")
        print(f"Response: {completion.choices[0].message.content}")
        return True
        
    except Exception as e:
        print(f"❌ AI model connection failed: {e}")
        return False

def test_quiz_generation():
    """Test quiz generation with a simple prompt"""
    print("\n🧪 Testing quiz generation...")
    
    try:
        client = InferenceClient(
            model=HF_MODEL,
            token=HF_ACCESS_TOKEN,
            timeout=60,
        )
        
        # Simple quiz prompt
        quiz_prompt = """Generate a simple quiz with 2 questions in JSON format:

{
    "quiz_title": "Test Quiz",
    "difficulty": "facile",
    "job_title": "Test",
    "questions": [
        {
            "id": 1,
            "question": "What is 2+2?",
            "options": {"A": "3", "B": "4", "C": "5", "D": "6"},
            "correct_answer": "B",
            "explanation": "2+2=4",
            "category": "technique",
            "skill_related": "Math"
        }
    ]
}

Respond ONLY with the JSON, no explanation."""
        
        completion = client.chat.completions.create(
            model=HF_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": quiz_prompt
                }
            ],
            temperature=0.1,
            max_tokens=500
        )
        
        response_content = completion.choices[0].message.content
        print("✅ Quiz generation successful!")
        print(f"Raw response: {response_content}")
        
        # Try to parse JSON
        try:
            # Remove any markdown or extra text
            import re
            if response_content is None:
                response_content = ""
            response_content = re.sub(r"<think>.*?</think>", "", response_content, flags=re.DOTALL)
            response_content = response_content.replace("```json", "").replace("```", "")
            
            # Find JSON object
            match = re.search(r"\{.*\}", response_content, re.DOTALL)
            if match:
                json_str = match.group(0)
                quiz_data = json.loads(json_str)
                print("✅ JSON parsing successful!")
                print(f"Quiz title: {quiz_data.get('quiz_title', 'N/A')}")
                print(f"Number of questions: {len(quiz_data.get('questions', []))}")
                return True
            else:
                print("❌ No JSON object found in response")
                return False
                
        except json.JSONDecodeError as e:
            print(f"❌ JSON parsing failed: {e}")
            return False
        
    except Exception as e:
        print(f"❌ Quiz generation failed: {e}")
        return False

def test_model_behavior():
    """Test different prompt styles to see what works best"""
    print("\n🧪 Testing different prompt styles...")
    
    prompts = [
        # Style 1: Direct and simple
        "Generate a JSON object with one field 'test' set to 'success'. Respond only with JSON.",
        
        # Style 2: With system message simulation
        "You are a JSON generator. Generate a JSON object with one field 'test' set to 'success'. Respond only with JSON.",
        
        # Style 3: Very explicit
        "Create a JSON object. The JSON should have one field called 'test' with value 'success'. Output ONLY the JSON, nothing else."
    ]
    
    try:
        client = InferenceClient(
            model=HF_MODEL,
            token=HF_ACCESS_TOKEN,
            timeout=60,
        )
        
        for i, prompt in enumerate(prompts, 1):
            print(f"\n--- Testing prompt style {i} ---")
            print(f"Prompt: {prompt}")
            
            completion = client.chat.completions.create(
                model=HF_MODEL,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1,
                max_tokens=100
            )
            
            response = completion.choices[0].message.content
            print(f"Response: {response}")
            
            # Check if response contains JSON
            if response and "{" in response and "}" in response:
                print("✅ Contains JSON-like structure")
            else:
                print("❌ No JSON-like structure found")
                
    except Exception as e:
        print(f"❌ Model behavior test failed: {e}")

if __name__ == "__main__":
    print("🚀 Starting AI model tests...\n")
    
    # Test 1: Basic connection
    connection_ok = test_ai_connection()
    
    if connection_ok:
        # Test 2: Quiz generation
        quiz_ok = test_quiz_generation()
        
        # Test 3: Model behavior
        test_model_behavior()
        
        print("\n📊 Test Summary:")
        print(f"Connection: {'✅ OK' if connection_ok else '❌ FAILED'}")
        print(f"Quiz Generation: {'✅ OK' if quiz_ok else '❌ FAILED'}")
        
        if connection_ok and quiz_ok:
            print("\n🎉 AI model is working correctly!")
        else:
            print("\n⚠️  Some tests failed. Check the output above for details.")
    else:
        print("\n❌ Cannot proceed with tests due to connection failure.") 