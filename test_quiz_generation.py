#!/usr/bin/env python3
"""
Test script to verify quiz generation and AI model functionality
"""

import json
from quiz_generator import QuizGenerator, query_deepseek

def test_ai_model():
    """Test the AI model connection and response"""
    print("🔍 Testing AI model connection...")
    
    test_prompt = """Generate a simple test response in JSON format:
    {
        "status": "working",
        "message": "AI model is functioning correctly"
    }
    
    Respond ONLY with the JSON object above."""
    
    try:
        response = query_deepseek(test_prompt)
        print(f"✅ AI Model Response: {response}")
        
        if response.get("success"):
            print("✅ AI model is working correctly!")
            return True
        else:
            print(f"❌ AI model error: {response.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ AI model test failed: {str(e)}")
        return False

def test_quiz_generation():
    """Test quiz generation with job skills"""
    print("\n🎯 Testing quiz generation based on job skills...")
    
    # Sample job skills data
    job_title = "Python Developer"
    required_skills_with_levels = [
        {
            "skill_name": "Python",
            "skill_level": "Advanced",
            "is_required": True
        },
        {
            "skill_name": "Django",
            "skill_level": "Intermediate", 
            "is_required": True
        },
        {
            "skill_name": "PostgreSQL",
            "skill_level": "Intermediate",
            "is_required": False
        }
    ]
    
    job_description = "We are looking for an experienced Python developer to join our team. The candidate should have strong experience with Django framework and database management."
    
    try:
        generator = QuizGenerator()
        print(f"📝 Generating quiz for: {job_title}")
        print(f"📋 Skills: {[skill['skill_name'] + ' (' + skill['skill_level'] + ')' for skill in required_skills_with_levels]}")
        
        quiz_data = generator.generate_recruitment_quiz(
            job_title=job_title,
            required_skills_with_levels=required_skills_with_levels,
            job_description=job_description,
            num_questions=5,  # Small number for testing
            past_questions=[]
        )
        
        print("✅ Quiz generated successfully!")
        print(f"📊 Quiz Title: {quiz_data.get('quiz_title', 'N/A')}")
        print(f"📈 Number of questions: {len(quiz_data.get('questions', []))}")
        
        # Display first question as example
        if quiz_data.get('questions'):
            first_q = quiz_data['questions'][0]
            print(f"\n📝 Sample Question:")
            print(f"   Question: {first_q.get('question', 'N/A')}")
            print(f"   Options: {list(first_q.get('options', {}).keys())}")
            print(f"   Correct Answer: {first_q.get('correct_answer', 'N/A')}")
            print(f"   Skill Related: {first_q.get('skill_related', 'N/A')}")
        
        if quiz_data.get('warning'):
            print(f"⚠️  Warning: {quiz_data['warning']}")
            
        return True
        
    except Exception as e:
        print(f"❌ Quiz generation failed: {str(e)}")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting Quiz Generation System Tests\n")
    
    # Test 1: AI Model Connection
    ai_working = test_ai_model()
    
    # Test 2: Quiz Generation
    if ai_working:
        quiz_working = test_quiz_generation()
        
        if quiz_working:
            print("\n🎉 All tests passed! Quiz generation system is working correctly.")
        else:
            print("\n❌ Quiz generation test failed.")
    else:
        print("\n❌ Cannot test quiz generation - AI model is not working.")
    
    print("\n" + "="*50)
    print("Test Summary:")
    print(f"AI Model: {'✅ Working' if ai_working else '❌ Failed'}")
    if ai_working:
        quiz_working = test_quiz_generation()
        print(f"Quiz Generation: {'✅ Working' if quiz_working else '❌ Failed'}")

if __name__ == "__main__":
    main()
