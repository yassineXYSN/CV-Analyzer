#!/usr/bin/env python3
"""
Final comprehensive test for DeepSeek quiz generation
"""

import sys
import os
import json
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from quiz_generator import QuizGenerator

def main():
    print("🚀 DeepSeek Quiz Generation Test")
    print("=" * 40)
    
    qg = QuizGenerator()
    
    # Test configuration
    job_title = "JavaScript Developer"
    skills = [
        {"skill_name": "JavaScript", "skill_level": "Advanced", "is_required": True},
        {"skill_name": "React", "skill_level": "Intermediate", "is_required": True}
    ]
    
    print(f"Job: {job_title}")
    print("Skills: JavaScript (Advanced), React (Intermediate)")
    print("\n🤖 Generating quiz with AI...")
    
    try:
        quiz = qg.generate_recruitment_quiz(
            job_title=job_title,
            required_skills_with_levels=skills,
            job_description="Frontend development role",
            num_questions=2,
            past_questions=[]
        )
        
        print("✅ Quiz generated!")
        
        if quiz and quiz.get('questions'):
            questions = quiz['questions']
            print(f"📊 Generated {len(questions)} questions")
            
            for i, q in enumerate(questions, 1):
                print(f"\n--- Question {i} ---")
                print(f"Text: {q.get('question', 'N/A')}")
                print(f"Skill: {q.get('skill_related', 'N/A')}")
                print(f"Options: {list(q.get('options', {}).keys())}")
                print(f"Answer: {q.get('correct_answer', 'N/A')}")
            
            # Save results
            with open('final_quiz_test.json', 'w', encoding='utf-8') as f:
                json.dump(quiz, f, indent=2, ensure_ascii=False)
            
            print(f"\n💾 Results saved to: final_quiz_test.json")
            print("🎉 Test completed successfully!")
            
        else:
            print("❌ No questions generated")
            if quiz and quiz.get('warning'):
                print(f"Warning: {quiz['warning']}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
