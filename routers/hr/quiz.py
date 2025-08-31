from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from databasehr.session_manager import current_user_session
from databasehr.database import SessionLocal
from databasehr.models import HRAdmin, Quiz, QuizSkill, QuizQuestion, ProfileCandidat
import os
import requests
from datetime import datetime, timezone
from sqlalchemy.orm import Session

router = APIRouter(prefix="/api/hr/quiz", tags=["Quiz"])


def get_current_hr_user():
    """Simple dependency to get current HR user from session"""
    user_id = current_user_session.get('user_id')
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    db = SessionLocal()
    try:
        user = db.query(HRAdmin).filter(HRAdmin.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return {"id": user.id, "email": user.email, "first_name": user.first_name, "last_name": user.last_name}
    finally:
        db.close()

def get_db():
    """Database dependency"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class QuizSkillConfig(BaseModel):
    name: str
    questions: int
    difficulty: str

class QuizCreateRequest(BaseModel):
    title: str
    time_limit: int
    skills: List[QuizSkillConfig]
    job_id: Optional[int] = None
    candidate_id: Optional[int] = None

@router.post("/create")
async def create_quiz(quiz_data: QuizCreateRequest, current_user=Depends(get_current_hr_user), db: Session = Depends(get_db)):
    """
    Create a new quiz based on form data and store in database
    """
    try:

        quiz = Quiz(
            title=quiz_data.title,
            time_limit=quiz_data.time_limit,
            job_id=quiz_data.job_id,
            candidate_id=quiz_data.candidate_id,
            created_by_admin_id=current_user["id"],
            status='draft',
            total_questions=sum(skill.questions for skill in quiz_data.skills if skill.questions > 0)
        )
        
        db.add(quiz)
        db.commit()
        db.refresh(quiz)
        
        for skill in quiz_data.skills:
            if skill.questions > 0:
                print('=>>>>>>>>>>>>>>>>>'+skill.difficulty+"<<<<<<<<<<<<<<<<<<<")
                quiz_skill = QuizSkill(
                    quiz_id=quiz.id,
                    skill_name=skill.name,
                    questions_count=skill.questions,
                    difficulty=skill.difficulty
                )
                db.add(quiz_skill)
        
        db.commit()

        quiz_request = {
            "quiz_id": quiz.id,  # Include quiz_id for n8n response handling
            "skills": [
                {
                    "name": skill.name,
                    "questions": skill.questions,
                    "difficulty": skill.difficulty
                }
                for skill in quiz_data.skills if skill.questions > 0
            ]
        }

        url = os.getenv("N8N_QUIZ_WEBHOOK_URL")
        print("=============================")
        print(quiz_request)
        print("=============================")
        
        quiz.n8n_webhook_url = url
        quiz.n8n_webhook_triggered = True
        
        try:
            response = requests.post(url, json=quiz_request)
            print("Status Code:", response.status_code)
            print("Response:", response.text)
            
            if response.status_code == 200:
                response_data = response.json()
                quiz.n8n_response = response_data
                
                # Process and store questions from n8n response
                await process_n8n_quiz_response(db, quiz.id, response_data)
                
                quiz.status = 'active'
            else:
                quiz.webhook_error = f"HTTP {response.status_code}: {response.text}"
                
        except Exception as webhook_error:
            quiz.webhook_error = str(webhook_error)
            print(f"Webhook error: {webhook_error}")
        
        db.commit()

        return {
            "success": True,
            "message": "Quiz created and stored successfully",
            "quiz_id": quiz.id,
            "quiz_data": {
                "title": quiz_data.title,
                "time_limit": quiz_data.time_limit,
                "skills_count": len(quiz_data.skills),
                "job_id": quiz_data.job_id,
                "candidate_id": quiz_data.candidate_id,
                "total_questions": quiz.total_questions
            }
        }

    except Exception as e:
        db.rollback()
        print(f"Error creating quiz: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating quiz: {str(e)}")

async def process_n8n_quiz_response(db: Session, quiz_id: int, n8n_response: List[dict]):
    """
    Process n8n response and store quiz questions in database
    Expected format: [{"name":"java","questions":[{"question":"...","options":["..."],"correctAnswerNumber":1}],"difficulty":"medium"}]
    """
    try:
        question_order = 1
        
        for skill_data in n8n_response:
            skill_name = skill_data.get("name", "")
            difficulty = skill_data.get("difficulty", "medium")
            questions = skill_data.get("questions", [])
            
            for question_data in questions:
                quiz_question = QuizQuestion(
                    quiz_id=quiz_id,
                    skill_name=skill_name,
                    question_text=question_data.get("question", ""),
                    question_type='multiple_choice',
                    difficulty=difficulty,
                    options=question_data.get("options", []),
                    correct_answer=str(question_data.get("correctAnswerNumber", 1)),
                    question_order=question_order,
                    points=1,
                    estimated_time_seconds=60
                )
                
                db.add(quiz_question)
                question_order += 1
        
        db.commit()
        print(f"Successfully stored {question_order - 1} questions for quiz {quiz_id}")
        
    except Exception as e:
        db.rollback()
        print(f"Error processing n8n response for quiz {quiz_id}: {str(e)}")
        raise e

@router.post("/webhook/n8n-response")
async def handle_n8n_response(quiz_id: int, response_data: List[dict], db: Session = Depends(get_db)):
    """
    Handle n8n webhook response for async quiz question generation
    """
    try:
        quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
        if not quiz:
            raise HTTPException(status_code=404, detail="Quiz not found")
        
        # Store the response
        quiz.n8n_response = response_data
        
        # Process and store questions
        await process_n8n_quiz_response(db, quiz_id, response_data)
        
        # Update quiz status
        quiz.status = 'active'
        quiz.updated_at = datetime.now(timezone.utc)
        
        db.commit()
        
        return {
            "success": True,
            "message": f"Quiz {quiz_id} updated with {len(response_data)} skill sets",
            "quiz_id": quiz_id
        }
        
    except Exception as e:
        db.rollback()
        print(f"Error handling n8n response: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing response: {str(e)}")

@router.get("/{quiz_id}")
async def get_quiz(quiz_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_hr_user)):
    """
    Get quiz details with questions
    """
    try:
        quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
        if not quiz:
            raise HTTPException(status_code=404, detail="Quiz not found")
        
        # Get quiz skills
        skills = db.query(QuizSkill).filter(QuizSkill.quiz_id == quiz_id).all()
        
        # Get quiz questions
        questions = db.query(QuizQuestion).filter(QuizQuestion.quiz_id == quiz_id).order_by(QuizQuestion.question_order).all()
        
        return {
            "quiz": {
                "id": quiz.id,
                "title": quiz.title,
                "time_limit": quiz.time_limit,
                "total_questions": quiz.total_questions,
                "status": quiz.status,
                "job_id": quiz.job_id,
                "candidate_id": quiz.candidate_id,
                "created_at": quiz.created_at,
                "updated_at": quiz.updated_at
            },
            "skills": [
                {
                    "name": skill.skill_name,
                    "questions_count": skill.questions_count,
                    "difficulty": skill.difficulty
                }
                for skill in skills
            ],
            "questions": [
                {
                    "id": q.id,
                    "skill_name": q.skill_name,
                    "question_text": q.question_text,
                    "options": q.options,
                    "correct_answer": q.correct_answer,
                    "difficulty": q.difficulty,
                    "points": q.points,
                    "question_order": q.question_order
                }
                for q in questions
            ]
        }
        
    except Exception as e:
        print(f"Error getting quiz: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving quiz: {str(e)}")
