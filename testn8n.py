#!/usr/bin/env python3
"""
Test script for N8N workflow integration
"""

import requests
import json
from datetime import datetime

# Configuration
N8N_WEBHOOK_URL = "https://your-n8n-instance.com/webhook"
TEST_DATA = {
    "application_info": {
        "application_id": 1,
        "application_date": datetime.now().isoformat(),
        "status": "pending",
        "hr_rating": None,
        "hr_notes": None,
        "compatibility_score": None,
        "compatibility_reason": None
    },
    "job_info": {
        "id": 1,
        "title": "Software Developer",
        "description": "Full-stack developer position",
        "requirements": "Python, JavaScript, React",
        "employment_type": "full-time",
        "salary_min": 50000,
        "salary_max": 70000
    },
    "candidate_profile": {
        "id": 1,
        "name": "Test Candidate",
        "title": "Software Engineer",
        "profile": "Experienced developer",
        "education": "Computer Science Degree",
        "skills": ["Python", "JavaScript", "React", "Node.js"]
    },
    "quiz_data": {
        "quiz_info": {
            "id": 1,
            "title": "Technical Assessment",
            "total_questions": 10,
            "time_limit": 30
        },
        "attempt_info": {
            "score": 85.0,
            "total_correct": 8,
            "total_questions": 10,
            "duration_seconds": 1200,
            "status": "completed"
        },
        "questions": [
            {
                "id": 1,
                "skill_name": "Python",
                "question_text": "What is the output of print(2**3)?",
                "correct_answer": "8",
                "user_answer": {"selected_option": "8", "is_correct": True}
            }
        ]
    }
}

def test_n8n_webhook():
    """Test N8N webhook connection"""
    try:
        print("Testing N8N webhook connection...")
        
        # Test quiz analysis webhook
        quiz_url = f"{N8N_WEBHOOK_URL}/analyze-quiz"
        response = requests.post(quiz_url, json=TEST_DATA, timeout=10)
        
        if response.status_code == 200:
            print("✅ N8N webhook test successful!")
            print(f"Response: {response.json()}")
        else:
            print(f"❌ N8N webhook test failed: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ N8N webhook test error: {str(e)}")
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")

def test_quiz_analysis():
    """Test quiz analysis workflow"""
    try:
        print("Testing quiz analysis workflow...")
        
        quiz_data = TEST_DATA.copy()
        quiz_data["workflow_type"] = "quiz_analysis"
        
        response = requests.post(f"{N8N_WEBHOOK_URL}/analyze-quiz", json=quiz_data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Quiz analysis successful!")
            print(f"Analysis result: {result.get('ReviewParagraph', 'No analysis returned')}")
        else:
            print(f"❌ Quiz analysis failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Quiz analysis error: {str(e)}")

if __name__ == "__main__":
    print("N8N Integration Test")
    print("=" * 50)
    
    # Test webhook connection
    test_n8n_webhook()
    
    print("\n" + "=" * 50)
    
    # Test quiz analysis
    test_quiz_analysis()
    
    print("\nTest completed!")
