#!/usr/bin/env python3
"""
Simple test script to check quiz generation functionality
"""

import json
from database import SessionLocal
from databaseclient.models import ProfileCandidat, Contact, AnalyseCandidat
from models import QuizAttempt
from quiz_service import QuizService

def create_sample_candidate():
    """Create a sample candidate for testing"""
    db = SessionLocal()
    try:
        # Check if candidate already exists
        existing_candidate = db.query(ProfileCandidat).filter(ProfileCandidat.name == "Test Candidate").first()
        if existing_candidate:
            print(f"✅ Sample candidate already exists with ID: {existing_candidate.id}")
            return existing_candidate.id
        
        # Create contact
        contact = Contact(
            email="test@example.com",
            phone="+1234567890",
            linkedin="https://linkedin.com/in/test",
            address="123 Test Street"
        )
        db.add(contact)
        db.flush()
        
        # Create analysis
        analysis = AnalyseCandidat(
            analyse="Sample analysis for test candidate"
        )
        db.add(analysis)
        db.flush()
        
        # Create candidate profile
        candidate = ProfileCandidat(
            name="Test Candidate",
            title="Développeur Full Stack",
            profile="Experienced full stack developer with expertise in Python, JavaScript, and React",
            contact_id=contact.id,
            analyse_id=analysis.id,
            yearOfExperience=3,
            education=json.dumps([
                {"degree": "Bachelor in Computer Science", "institution": "Test University", "year": 2020}
            ]),
            languages=json.dumps([
                {"language": "French", "level": "Native"},
                {"language": "English", "level": "Fluent"}
            ]),
            certificates=json.dumps([
                {"name": "AWS Certified Developer", "issuer": "Amazon", "year": 2022}
            ]),
            skills=json.dumps([
                "Python: Advanced",
                "JavaScript: Advanced", 
                "React: Intermediate",
                "Node.js: Intermediate",
                "SQL: Advanced"
            ])
        )
        db.add(candidate)
        db.commit()
        db.refresh(candidate)
        
        print(f"✅ Sample candidate created with ID: {candidate.id}")
        return candidate.id
        
    except Exception as e:
        print(f"❌ Error creating sample candidate: {e}")
        db.rollback()
        return None
    finally:
        db.close()

def test_quiz_generation():
    """Test quiz generation functionality"""
    print("🧪 Testing quiz generation...")
    
    # Create sample candidate
    candidate_id = create_sample_candidate()
    if not candidate_id:
        print("❌ Failed to create sample candidate")
        return
    
    # Initialize quiz service
    quiz_service = QuizService()
    
    try:
        # Generate quiz
        quizzes = quiz_service.generate_quiz_for_candidate(
            candidate_id=candidate_id,
            job_title="Développeur Full Stack",
            num_questions=5
        )
        
        if quizzes:
            print("✅ Quiz generation successful!")
            print(f"Generated {len(quizzes)} quiz(zes)")
            
            for i, quiz in enumerate(quizzes):
                print(f"\n📝 Quiz {i+1}:")
                print(f"  - Quiz ID: {quiz.get('quiz_id', 'N/A')}")
                print(f"  - Title: {quiz.get('quiz_title', 'N/A')}")
                print(f"  - Questions: {len(quiz.get('questions', []))}")
                
                if 'warning' in quiz:
                    print(f"  - Warning: {quiz['warning']}")
                
                # Show first question as example
                questions = quiz.get('questions', [])
                if questions:
                    first_q = questions[0]
                    print(f"  - Sample question: {first_q.get('question', 'N/A')[:100]}...")
        else:
            print("❌ No quizzes generated")
            
    except Exception as e:
        print(f"❌ Error in quiz generation: {e}")
        import traceback
        traceback.print_exc()

def test_quiz_evaluation():
    """Test quiz evaluation functionality"""
    print("\n🧪 Testing quiz evaluation...")
    
    # Get the first quiz attempt from database
    db = SessionLocal()
    try:
        attempt = db.query(QuizAttempt).first()
        if not attempt:
            print("❌ No quiz attempts found in database")
            return
        
        print(f"✅ Found quiz attempt ID: {attempt.id}")
        
        # Create sample answers
        questions = attempt.questions or []
        answers = {}
        for i, q in enumerate(questions[:5]):  # Answer first 5 questions
            if isinstance(q, dict) and 'options' in q:
                # Choose first option as answer
                first_option = list(q['options'].keys())[0] if q['options'] else 'A'
                answers[i+1] = first_option
        
        print(f"Sample answers: {answers}")
        
        # Test evaluation
        quiz_service = QuizService()
        evaluation = quiz_service.submit_quiz_attempt(
            quiz_id=attempt.id,
            candidate_id=attempt.candidate_id,
            answers=answers
        )
        
        if evaluation:
            print("✅ Quiz evaluation successful!")
            print(f"Total score: {evaluation.get('total_score', 'N/A')}%")
            print(f"Category scores: {evaluation.get('category_scores', 'N/A')}")
        else:
            print("❌ Quiz evaluation failed")
            
    except Exception as e:
        print(f"❌ Error in quiz evaluation: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    print("🚀 Starting quiz functionality tests...")
    test_quiz_generation()
    test_quiz_evaluation()
    print("\n✅ Tests completed!") 