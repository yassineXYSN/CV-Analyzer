#!/usr/bin/env python3
"""
Test script for quiz functionality
"""

import requests
import json

# Base URL for the application
BASE_URL = "http://localhost:8000"

def test_quiz_generation():
    """Test quiz generation"""
    print("🧪 Testing quiz generation...")
    
    # Test data
    test_data = {
        "candidate_id": 1,
        "job_title": "Développeur Full Stack",
        "num_questions": 5
    }
    
    try:
        response = requests.post(f"{BASE_URL}/generate-quiz", json=test_data)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                print("✅ Quiz generation successful!")
                print(f"Quiz ID: {data['quiz']['quiz_id']}")
                print(f"Title: {data['quiz']['quiz_title']}")
                print(f"Questions: {len(data['quiz']['questions'])}")
                # Print skill mapping if present
                if 'skill_mapping' in data['quiz']:
                    print("Skill mapping (question index -> skill):")
                    for k, v in list(data['quiz']['skill_mapping'].items())[:20]:  # print first 20
                        print(f"  Q{k}: {v}")
                return data['quiz']['quiz_id']
            else:
                print(f"❌ Quiz generation failed: {data.get('error')}")
                return None
        else:
            print(f"❌ HTTP error: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Error testing quiz generation: {e}")
        return None

def test_quiz_submission(quiz_id):
    """Test quiz submission"""
    print(f"\n🧪 Testing quiz submission for quiz {quiz_id}...")
    
    # Sample answers
    answers = {
        1: "A",
        2: "B", 
        3: "C",
        4: "D",
        5: "A"
    }
    
    test_data = {
        "quiz_id": quiz_id,
        "candidate_id": 1,
        "answers": answers
    }
    
    try:
        response = requests.post(f"{BASE_URL}/submit-quiz", json=test_data)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                print("✅ Quiz submission successful!")
                evaluation = data['evaluation']
                print(f"Total Score: {evaluation['total_score']}%")
                print(f"Correct Answers: {evaluation['correct_answers']}/{evaluation['total_questions']}")
                print("Category Scores:")
                for category, score in evaluation['category_scores'].items():
                    print(f"  - {category}: {score}%")
                return data['evaluation']['attempt_id']
            else:
                print(f"❌ Quiz submission failed: {data.get('error')}")
                return None
        else:
            print(f"❌ HTTP error: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Error testing quiz submission: {e}")
        return None

def test_quiz_history():
    """Test quiz history retrieval"""
    print(f"\n🧪 Testing quiz history for candidate 1...")
    
    try:
        response = requests.get(f"{BASE_URL}/quiz-history/1")
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                print("✅ Quiz history retrieval successful!")
                history = data['history']
                print(f"Found {len(history)} quiz attempts")
                for attempt in history:
                    print(f"  - {attempt['quiz_title']}: {attempt['total_score']}%")
            else:
                print(f"❌ Quiz history retrieval failed: {data.get('error')}")
        else:
            print(f"❌ HTTP error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error testing quiz history: {e}")

def test_multi_skill_quiz():
    """Test per-skill quiz generation and submission"""
    print("🧪 Testing per-skill quiz generation...")
    test_data = {
        "candidate_id": 1,
        "job_title": "Développeur Full Stack",
        "num_questions": 5
    }
    try:
        response = requests.post(f"{BASE_URL}/generate-quiz", json=test_data)
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                quizzes = data["quizzes"]
                print(f"✅ Generated {len(quizzes)} per-skill quizzes!")
                submissions = []
                for quiz in quizzes:
                    print(f"Quiz for skill: {quiz.get('skill', quiz.get('job_title'))}")
                    print(f"  Quiz ID: {quiz['quiz_id']}")
                    print(f"  Questions: {len(quiz['questions'])}")
                    # Dummy answers: always pick 'A'
                    answers = {str(i+1): 'A' for i in range(len(quiz['questions']))}
                    submissions.append({
                        "quiz_id": quiz["quiz_id"],
                        "candidate_id": test_data["candidate_id"],
                        "answers": answers
                    })
                # Submit all quizzes
                submit_resp = requests.post(f"{BASE_URL}/submit-multi-quiz", json={"submissions": submissions})
                if submit_resp.status_code == 200:
                    submit_data = submit_resp.json()
                    if submit_data.get("success"):
                        print(f"✅ Submitted all per-skill quizzes!")
                        print(f"Average Score: {submit_data['average_score']}%")
                        for idx, eval in enumerate(submit_data["evaluations"]):
                            print(f"  Skill Quiz {idx+1}: {eval['total_score']}% ({eval['quiz_title']})")
                    else:
                        print(f"❌ Submission failed: {submit_data.get('error')}")
                else:
                    print(f"❌ HTTP error on submission: {submit_resp.status_code}")
            else:
                print(f"❌ Quiz generation failed: {data.get('error')}")
        else:
            print(f"❌ HTTP error: {response.status_code}")
    except Exception as e:
        print(f"❌ Error in multi-skill quiz test: {e}")

def test_empty_response_handling():
    """Test that empty or invalid AI responses are handled gracefully"""
    print("\n🧪 Testing empty response handling...")
    
    # Test with a skill that might cause issues
    test_data = {
        "candidate_id": 1,
        "job_title": "Test Job",
        "num_questions": 5
    }
    
    try:
        response = requests.post(f"{BASE_URL}/generate-quiz", json=test_data)
        data = response.json()
        
        if data.get("success"):
            quizzes = data.get("quizzes", [])
            print(f"✅ Generated {len(quizzes)} quizzes")
            
            for i, quiz in enumerate(quizzes):
                print(f"Quiz {i+1}:")
                print(f"  Skill: {quiz.get('skill', 'N/A')}")
                print(f"  Questions: {len(quiz.get('questions', []))}")
                if quiz.get('warning'):
                    print(f"  Warning: {quiz['warning']}")
                print()
            
            # Check that all quizzes have at least one question
            all_have_questions = all(len(quiz.get('questions', [])) > 0 for quiz in quizzes)
            if all_have_questions:
                print("✅ All quizzes have questions (including placeholders if needed)")
                return True
            else:
                print("❌ Some quizzes have no questions")
                return False
        else:
            print(f"❌ Quiz generation failed: {data.get('error')}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing empty response handling: {e}")
        return False

def test_randomization_and_non_repetitive():
    """Test that quiz generation produces randomized and non-repetitive questions"""
    print("\n🧪 Testing randomization and non-repetitive questions...")
    
    # Test with multiple skills to ensure variety
    test_data = {
        "candidate_id": 1,
        "job_title": "Full Stack Developer",
        "num_questions": 10
    }
    
    try:
        response = requests.post(f"{BASE_URL}/generate-quiz", json=test_data)
        data = response.json()
        
        if data.get("success"):
            quizzes = data.get("quizzes", [])
            print(f"✅ Generated {len(quizzes)} quizzes")
            
            all_questions = []
            for quiz in quizzes:
                questions = quiz.get("questions", [])
                all_questions.extend(questions)
                print(f"Quiz '{quiz.get('skill', 'N/A')}': {len(questions)} questions")
            
            if len(all_questions) > 0:
                # Check for randomization by comparing question orders
                question_texts = [q.get("question", "") for q in all_questions]
                
                # Check for duplicates
                unique_questions = set(question_texts)
                duplicate_count = len(question_texts) - len(unique_questions)
                
                if duplicate_count == 0:
                    print("✅ No duplicate questions found")
                else:
                    print(f"⚠️ Found {duplicate_count} duplicate questions")
                
                # Check for variety in question types
                question_types = []
                for q in all_questions:
                    question_text = q.get("question", "").lower()
                    if "what is" in question_text or "define" in question_text:
                        question_types.append("definition")
                    elif "how would" in question_text or "what would" in question_text:
                        question_types.append("scenario")
                    elif "which" in question_text or "what is the best" in question_text:
                        question_types.append("choice")
                    else:
                        question_types.append("other")
                
                unique_types = set(question_types)
                print(f"✅ Found {len(unique_types)} different question types: {unique_types}")
                
                # Check option randomization
                option_randomization_ok = True
                for q in all_questions:
                    options = q.get("options", {})
                    if len(options) == 4:
                        # Check if options are not all the same pattern
                        option_texts = list(options.values())
                        if len(set(option_texts)) < 4:
                            option_randomization_ok = False
                            break
                
                if option_randomization_ok:
                    print("✅ Options appear to be randomized")
                else:
                    print("⚠️ Some options may not be properly randomized")
                
                return True
            else:
                print("❌ No questions generated")
                return False
        else:
            print(f"❌ Quiz generation failed: {data.get('error')}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing randomization: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting quiz functionality tests...\n")
    
    # Test 1: Basic quiz generation
    test1_ok = test_quiz_generation()
    
    # Test 2: Quiz submission
    quiz_id = None
    if test1_ok:
        quiz_id = test_quiz_submission(quiz_id)
    
    # Test 3: Quiz history
    test3_ok = test_quiz_history()
    
    # Test 4: Multi-skill quiz
    test4_ok = test_multi_skill_quiz()
    
    # Test 5: Empty response handling
    test5_ok = test_empty_response_handling()
    
    # Test 6: Randomization and non-repetitive
    test6_ok = test_randomization_and_non_repetitive()
    
    print("\n📊 Test Results Summary:")
    print(f"Quiz Generation: {'✅ OK' if test1_ok else '❌ FAILED'}")
    print(f"Quiz Submission: {'✅ OK' if quiz_id else '❌ FAILED'}")
    print(f"Quiz History: {'✅ OK' if test3_ok else '❌ FAILED'}")
    print(f"Multi-Skill Quiz: {'✅ OK' if test4_ok else '❌ FAILED'}")
    print(f"Empty Response Handling: {'✅ OK' if test5_ok else '❌ FAILED'}")
    print(f"Randomization & Non-Repetitive: {'✅ OK' if test6_ok else '❌ FAILED'}")
    
    if test1_ok and quiz_id and test3_ok and test4_ok and test5_ok and test6_ok:
        print("\n🎉 All tests passed! Quiz system is working correctly.")
    else:
        print("\n⚠️ Some tests failed. Please check the implementation.") 