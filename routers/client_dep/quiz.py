from fastapi import APIRouter, Depends, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime, timedelta
import json
import logging
from typing import Optional

from databasehr.database import get_db
from databaseclient.models import Quiz, QuizQuestion, QuizAttempt, QuizAnswer, User, ProfileCandidat
from routers.client_dep.dependencies import get_db, get_current_user,require_auth

# Setup
router = APIRouter()
templates = Jinja2Templates(directory="templates")
logger = logging.getLogger(__name__)

@router.get("/quiz/{quiz_id}", response_class=HTMLResponse)
async def quiz_page(
    request: Request,
    quiz_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_auth)
):
    """
    Display quiz taking page - only accessible by the assigned candidate
    """
    try:
        # Get quiz with candidate verification
        quiz = db.query(Quiz).filter(
            and_(
                Quiz.id == quiz_id,
                Quiz.candidate_id == current_user.profile_id,
                Quiz.status == 'active'
            )
        ).first()
        
        if not quiz:
            raise HTTPException(
                status_code=404, 
                detail="Quiz not found or you don't have permission to access it"
            )
        
        # Check if quiz is already completed
        existing_attempt = db.query(QuizAttempt).filter(
            and_(
                QuizAttempt.quiz_id == quiz_id,
                QuizAttempt.candidate_id == current_user.profile_id,
                QuizAttempt.status.in_(['completed', 'expired'])
            )
        ).first()
        
        if existing_attempt:
            return templates.TemplateResponse("quiz_completed.html", {
                "request": request,
                "current_user": current_user,
                "quiz": quiz,
                "attempt": existing_attempt,
                "message": "You have already completed this quiz."
            })
        
        # Get or create active attempt
        active_attempt = db.query(QuizAttempt).filter(
            and_(
                QuizAttempt.quiz_id == quiz_id,
                QuizAttempt.candidate_id == current_user.profile_id,
                QuizAttempt.status == 'in_progress'
            )
        ).first()
        
        # Check if time has expired for existing attempt
        if active_attempt:
            time_limit = timedelta(minutes=quiz.time_limit	)
            if datetime.now() > active_attempt.started_at + time_limit:
                # Mark as expired
                active_attempt.status = 'expired'
                active_attempt.completed_at = datetime.now()
                db.commit()
                
                return templates.TemplateResponse("quiz_completed.html", {
                    "request": request,
                    "current_user": current_user,
                    "quiz": quiz,
                    "attempt": active_attempt,
                    "message": "Quiz time has expired."
                })
        
        # Get quiz questions
        questions = db.query(QuizQuestion).filter(
            QuizQuestion.quiz_id == quiz_id
        ).order_by(QuizQuestion.question_order).all()
        
        if not questions:
            raise HTTPException(status_code=404, detail="No questions found for this quiz")
        
        # Calculate remaining time
        remaining_time = None
        if active_attempt:
            elapsed = datetime.now() - active_attempt.started_at
            total_time = timedelta(minutes=quiz.time_limit	)
            remaining_time = max(0, int((total_time - elapsed).total_seconds()))
        else:
            remaining_time = quiz.time_limit * 60
        
        return templates.TemplateResponse("quiz_take.html", {
            "request": request,
            "current_user": current_user,
            "quiz": quiz,
            "questions": questions,
            "attempt": active_attempt,
            "remaining_time": remaining_time,
            "total_questions": len(questions)
        })
        
    except Exception as e:
        logger.error(f"Error loading quiz {quiz_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/quiz/{quiz_id}/start")
async def start_quiz(
    quiz_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_auth)
):
    """
    Start a new quiz attempt
    """
    try:
        # Verify quiz access
        quiz = db.query(Quiz).filter(
            and_(
                Quiz.id == quiz_id,
                Quiz.candidate_id == current_user.profile_id,
                Quiz.status == 'active'
            )
        ).first()
        
        if not quiz:
            raise HTTPException(status_code=404, detail="Quiz not found")
        
        # Check for existing attempts
        existing_attempt = db.query(QuizAttempt).filter(
            and_(
                QuizAttempt.quiz_id == quiz_id,
                QuizAttempt.candidate_id == current_user.profile_id
            )
        ).first()
        
        if existing_attempt and existing_attempt.status in ['completed', 'expired']:
            raise HTTPException(status_code=400, detail="Quiz already completed")
        
        if existing_attempt and existing_attempt.status == 'in_progress':
            # Return existing attempt
            return {"success": True, "attempt_id": existing_attempt.id}
        
        # Create new attempt
        new_attempt = QuizAttempt(
            quiz_id=quiz_id,
            candidate_id=current_user.profile_id,
            started_at=datetime.now(),
            status='in_progress',
            ip_address=request.client.host,
            user_agent=request.headers.get('user-agent', ''),
            max_possible_score=sum(q.points for q in quiz.questions)
        )
        
        db.add(new_attempt)
        db.commit()
        db.refresh(new_attempt)
        
        return {"success": True, "attempt_id": new_attempt.id}
        
    except Exception as e:
        logger.error(f"Error starting quiz {quiz_id}: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to start quiz")

@router.post("/quiz/{quiz_id}/submit")
async def submit_quiz(
    quiz_id: int,
    request: Request,
    answers: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_auth)
):
    """
    Submit quiz answers and calculate score
    """
    try:
        # Get active attempt
        attempt = db.query(QuizAttempt).filter(
            and_(
                QuizAttempt.quiz_id == quiz_id,
                QuizAttempt.candidate_id == current_user.profile_id,
                QuizAttempt.status == 'in_progress'
            )
        ).first()
        
        if not attempt:
            raise HTTPException(status_code=404, detail="No active quiz attempt found")
        
        # Parse answers
        try:
            answers_data = json.loads(answers)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid answers format")
        
        # Get quiz questions
        questions = db.query(QuizQuestion).filter(
            QuizQuestion.quiz_id == quiz_id
        ).all()
        
        questions_dict = {q.id: q for q in questions}
        total_score = 0
        max_score = sum(q.points for q in questions)
        
        # Process each answer
        for question_id_str, answer_data in answers_data.items():
            question_id = int(question_id_str)
            question = questions_dict.get(question_id)
            
            if not question:
                continue
            
            # Determine if answer is correct
            is_correct = False
            points_earned = 0
            
            if question.question_type == 'multiple_choice':
                selected_option = answer_data.get('selected_option')
                if selected_option == question.correct_answer:
                    is_correct = True
                    points_earned = question.points
            elif question.question_type == 'true_false':
                selected_answer = answer_data.get('answer', '').lower()
                if selected_answer == question.correct_answer.lower():
                    is_correct = True
                    points_earned = question.points
            elif question.question_type == 'short_answer':
                user_answer = answer_data.get('answer', '').strip().lower()
                correct_answer = question.correct_answer.strip().lower()
                if user_answer == correct_answer:
                    is_correct = True
                    points_earned = question.points
            
            total_score += points_earned
            
            # Save answer
            quiz_answer = QuizAnswer(
                attempt_id=attempt.id,
                question_id=question_id,
                answer_text=answer_data.get('answer', ''),
                selected_options=answer_data.get('selected_option'),
                is_correct=is_correct,
                points_earned=points_earned,
                time_taken_seconds=answer_data.get('time_taken', 0),
                answered_at=datetime.now()
            )
            db.add(quiz_answer)
        
        # Update attempt
        attempt.completed_at = datetime.now()
        attempt.status = 'completed'
        attempt.total_score = total_score
        attempt.max_possible_score = max_score
        attempt.percentage_score = (total_score / max_score * 100) if max_score > 0 else 0
        attempt.time_taken_seconds = int((attempt.completed_at - attempt.started_at).total_seconds())
        
        db.commit()
        
        return RedirectResponse(
            url=f"/quiz/{quiz_id}/results", 
            status_code=303
        )
        
    except Exception as e:
        logger.error(f"Error submitting quiz {quiz_id}: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to submit quiz")

@router.get("/quiz/{quiz_id}/results", response_class=HTMLResponse)
async def quiz_results(
    request: Request,
    quiz_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_auth)
):
    """
    Display quiz results
    """
    try:
        # Get completed attempt
        attempt = db.query(QuizAttempt).filter(
            and_(
                QuizAttempt.quiz_id == quiz_id,
                QuizAttempt.candidate_id == current_user.profile_id,
                QuizAttempt.status.in_(['completed', 'expired'])
            )
        ).first()
        
        if not attempt:
            raise HTTPException(status_code=404, detail="Quiz results not found")
        
        # Get quiz details
        quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
        
        # Get answers with questions
        answers = db.query(QuizAnswer).join(QuizQuestion).filter(
            QuizAnswer.attempt_id == attempt.id
        ).all()
        
        return templates.TemplateResponse("quiz_results.html", {
            "request": request,
            "current_user": current_user,
            "quiz": quiz,
            "attempt": attempt,
            "answers": answers
        })
        
    except Exception as e:
        logger.error(f"Error loading quiz results {quiz_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/quiz/{quiz_id}/time-check")
async def check_time_remaining(
    quiz_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_auth)
):
    """
    API endpoint to check remaining time for active quiz
    """
    try:
        attempt = db.query(QuizAttempt).filter(
            and_(
                QuizAttempt.quiz_id == quiz_id,
                QuizAttempt.candidate_id == current_user.profile_id,
                QuizAttempt.status == 'in_progress'
            )
        ).first()
        
        if not attempt:
            return {"success": False, "message": "No active attempt found"}
        
        quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
        if not quiz:
            return {"success": False, "message": "Quiz not found"}
        
        elapsed = datetime.now() - attempt.started_at
        total_time = timedelta(minutes=quiz.time_limit	)
        remaining = total_time - elapsed
        
        if remaining.total_seconds() <= 0:
            # Time expired, mark attempt as expired
            attempt.status = 'expired'
            attempt.completed_at = datetime.now()
            db.commit()
            return {"success": True, "time_remaining": 0, "expired": True}
        
        return {
            "success": True, 
            "time_remaining": int(remaining.total_seconds()),
            "expired": False
        }
        
    except Exception as e:
        logger.error(f"Error checking time for quiz {quiz_id}: {str(e)}")
        return {"success": False, "message": "Internal server error"}
