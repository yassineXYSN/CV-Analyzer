from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from databasehr.session_manager import current_user_session
from databasehr.database import SessionLocal
from databasehr.models import HRAdmin, Quiz, QuizSkill, QuizQuestion, ProfileCandidat, Notification, Job, Application, Company
import os
import requests
from datetime import datetime, timezone
from sqlalchemy.orm import Session
import threading
from fastapi import BackgroundTasks

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
async def create_quiz(background_tasks: BackgroundTasks, quiz_data: QuizCreateRequest, current_user=Depends(get_current_hr_user), db: Session = Depends(get_db)):
    """
    Create a new quiz based on form data and store in database
    """
    quiz_id = None
    try:
        # Debug: Print quiz creation data
        print(f"DEBUG: Creating quiz with job_id={quiz_data.job_id}, candidate_id={quiz_data.candidate_id}")
        
        # Validate required data
        if not quiz_data.title or not quiz_data.title.strip():
            raise HTTPException(status_code=400, detail="Quiz title is required")
        
        if quiz_data.time_limit <= 0:
            raise HTTPException(status_code=400, detail="Time limit must be greater than 0")
        
        if not quiz_data.skills or len(quiz_data.skills) == 0:
            raise HTTPException(status_code=400, detail="At least one skill is required")
        
        # Validate skills
        total_questions = 0
        for skill in quiz_data.skills:
            if not skill.name or not skill.name.strip():
                raise HTTPException(status_code=400, detail="Skill name cannot be empty")
            if skill.questions < 0:
                raise HTTPException(status_code=400, detail="Number of questions cannot be negative")
            total_questions += skill.questions
        
        if total_questions == 0:
            raise HTTPException(status_code=400, detail="At least one skill must have questions > 0")
        
        # Create quiz
        quiz = Quiz(
            title=quiz_data.title.strip(),
            time_limit=quiz_data.time_limit,
            job_id=quiz_data.job_id,
            candidate_id=quiz_data.candidate_id,
            created_by_admin_id=current_user["id"],
            status='draft',
            total_questions=total_questions
        )
        
        db.add(quiz)
        db.commit()
        db.refresh(quiz)
        quiz_id = quiz.id
        
        # Debug: Print created quiz data
        print(f"DEBUG: Quiz created successfully with id={quiz.id}, job_id={quiz.job_id}, candidate_id={quiz.candidate_id}")
        
        # Add quiz skills
        for skill in quiz_data.skills:
            if skill.questions > 0:
                quiz_skill = QuizSkill(
                    quiz_id=quiz.id,
                    skill_name=skill.name.strip(),
                    questions_count=skill.questions,
                    difficulty=skill.difficulty
                )
                db.add(quiz_skill)
        
        db.commit()

        # Prepare n8n request
        quiz_request = {
            "quiz_id": quiz.id,
            "skills": [
                {
                    "name": skill.name.strip(),
                    "questions": skill.questions,
                    "difficulty": skill.difficulty
                }
                for skill in quiz_data.skills if skill.questions > 0
            ]
        }

        n8nurl = os.getenv("N8N_QUIZ_WEBHOOK_URL")
        if not n8nurl:
            raise HTTPException(status_code=500, detail="N8N webhook URL not configured")
        
        print("=============================")
        print(quiz_request)
        print("=============================")
        
        # Update quiz with webhook info
        quiz.n8n_webhook_url = n8nurl
        quiz.n8n_webhook_triggered = True
        
        # Call n8n webhook
        try:
            response = requests.post(n8nurl, json=quiz_request, timeout=60)
            
            if response.status_code == 200:
                response_data = response.json()
                quiz.n8n_response = response_data
                
                # Process and store questions from n8n response
                await process_n8n_quiz_response(db, quiz.id, response_data)
                
                quiz.status = 'active'
                db.commit()
            else:
                error_msg = f"HTTP {response.status_code}: {response.text}"
                quiz.webhook_error = error_msg
                quiz.status = 'error'
                db.commit()
                raise HTTPException(status_code=500, detail=f"Failed to generate quiz questions: {error_msg}")
                
        except requests.exceptions.RequestException as webhook_error:
            error_msg = f"Webhook request failed: {str(webhook_error)}"
            quiz.webhook_error = error_msg
            quiz.status = 'error'
            db.commit()
            raise HTTPException(status_code=500, detail=error_msg)
        except Exception as webhook_error:
            error_msg = f"Webhook error: {str(webhook_error)}"
            quiz.webhook_error = error_msg
            quiz.status = 'error'
            db.commit()
            raise HTTPException(status_code=500, detail=error_msg)

        # Send notification (non-critical, don't fail if this fails)
        try:
            candidat = db.query(ProfileCandidat).filter(ProfileCandidat.id == quiz.candidate_id).first()
            admin = db.query(HRAdmin).filter(HRAdmin.id == current_user["id"]).first()
            job = db.query(Job).filter(Job.id == quiz_data.job_id).first()
            
            if candidat and job:
                application = db.query(Application).filter(
                    Application.candidate_profile_id == candidat.id, 
                    Application.job_id == job.id
                ).first()
                company = db.query(Company).filter(Company.id == job.company_id).first()
                
                base_url = os.getenv("APP_BASE_URL", "http://127.0.0.1:8000")
                background_tasks.add_task(send_test_notification_via_api,
                    base_url,
                    user_id=candidat.user_id if candidat else None,
                    type="application_status_change",
                    title=quiz_data.title,
                    message="A new quiz has been created for you. Please check your quizzes page to start.",
                    application_id=application.id if application else None,
                    job_id=job.id if job else None,
                    status="pending",
                    company_name=company.company_name if company else None,
                    job_title=job.title if job else None,
                    admin_name=f"{admin.first_name} {admin.last_name}" if admin else None,
                )
        except Exception as notification_error:
            # Log notification error but don't fail the quiz creation
            print(f"Notification error (non-critical): {notification_error}")
            
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

    except HTTPException:
        # Re-raise HTTP exceptions as they are already properly formatted
        db.rollback()
        raise
    except Exception as e:
        # Rollback any database changes
        db.rollback()
        
        # If we created a quiz, try to delete it
        if quiz_id:
            try:
                db.query(Quiz).filter(Quiz.id == quiz_id).delete()
                db.query(QuizSkill).filter(QuizSkill.quiz_id == quiz_id).delete()
                db.query(QuizQuestion).filter(QuizQuestion.quiz_id == quiz_id).delete()
                db.commit()
                print(f"Cleaned up quiz {quiz_id} after error")
            except Exception as cleanup_error:
                print(f"Error during cleanup: {cleanup_error}")
                db.rollback()
        
        print(f"Error creating quiz: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating quiz: {str(e)}")

async def process_n8n_quiz_response(db: Session, quiz_id: int, n8n_response: List[dict]):
    """
    Process n8n response and store quiz questions in database
    Expected format: [{"name":"java","questions":[{"question":"...","options":["..."],"correctAnswerNumber":1}],"difficulty":"medium"}]
    """
    try:
        if not n8n_response or not isinstance(n8n_response, list):
            raise ValueError("Invalid n8n response format: expected a list")
        
        question_order = 1
        questions_added = 0
        
        for skill_data in n8n_response:
            if not isinstance(skill_data, dict):
                print(f"Warning: Skipping invalid skill data: {skill_data}")
                continue
                
            skill_name = skill_data.get("name", "").strip()
            if not skill_name:
                print(f"Warning: Skipping skill with empty name: {skill_data}")
                continue
                
            difficulty = skill_data.get("difficulty", "medium")
            questions = skill_data.get("questions", [])
            
            if not isinstance(questions, list):
                print(f"Warning: Skipping skill '{skill_name}' with invalid questions format")
                continue
            
            for question_data in questions:
                if not isinstance(question_data, dict):
                    print(f"Warning: Skipping invalid question data: {question_data}")
                    continue
                    
                question_text = question_data.get("question", "").strip()
                if not question_text:
                    print(f"Warning: Skipping question with empty text")
                    continue
                
                options = question_data.get("options", [])
                if not isinstance(options, list) or len(options) == 0:
                    print(f"Warning: Skipping question with invalid options: {question_text}")
                    continue
                
                correct_answer = question_data.get("correctAnswerNumber", 1)
                if not isinstance(correct_answer, int) or correct_answer < 1 or correct_answer > len(options):
                    print(f"Warning: Invalid correct answer number for question: {question_text}")
                    correct_answer = 1
                
                quiz_question = QuizQuestion(
                    quiz_id=quiz_id,
                    skill=skill_name,
                    question_text=question_text,
                    options=options,
                    correct_answer=str(correct_answer),
                    question_order=question_order,
                )
                
                db.add(quiz_question)
                question_order += 1
                questions_added += 1
        
        if questions_added == 0:
            raise ValueError("No valid questions found in n8n response")
        
        db.commit()
        print(f"Successfully stored {questions_added} questions for quiz {quiz_id}")
        
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

def send_test_notification_via_api(
    base_url: str,
    user_id: int,
    type: str,
    title: str,
    message: str,
    application_id: int,
    job_id: int,
    status: str,
    company_name: str,
    job_title: str,
    admin_name: str,
):
    url = f"{base_url.rstrip('/')}/api/notifications/test-create"
    payload = {
        "user_id": user_id,
        "type": type,
        "title": title,
        "message": message,
        "application_id": application_id,
        "job_id": job_id,
        "status": status,
        "company_name": company_name,
        "job_title": job_title,
        "admin_name": admin_name,
    }
    resp = requests.post(url, json=payload, timeout=10)
    print("Status:", resp.status_code)
    try:
        print("Response:", resp.json())
    except Exception:
        print("Response text:", resp.text)