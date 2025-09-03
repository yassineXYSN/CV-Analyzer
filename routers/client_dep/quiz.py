from fastapi import APIRouter, Depends, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime, timedelta
import json
import logging
from typing import Optional

from databaseclient.models import Quiz, QuizQuestion, QuizAttempt, QuizAnswer, User, ProfileCandidat
from routers.client_dep.dependencies import get_db, get_current_user, require_auth

# Setup
router = APIRouter()
templates = Jinja2Templates(directory="templates")
logger = logging.getLogger(__name__)



@router.get("/quizzes", response_class=HTMLResponse)
async def quizzes_list(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_auth)
):
    """
    Display list of available quizzes for the current user
    """
    try:
        # Get all quizzes assigned to the current user
        if not current_user.profile:
            # User doesn't have a profile yet
            return templates.TemplateResponse("client-dep/quizzes_list.html", {
                "request": request,
                "current_user": current_user,
                "quizzes": [],
                "no_profile": True
            })
            
        quizzes = db.query(Quiz).filter(
            and_(
                Quiz.candidate_id == current_user.profile.id,
                Quiz.status == 'active'
            )
        ).all()
        
        # Get quiz attempts for each quiz
        quiz_data = []
        for quiz in quizzes:
            # Check if quiz is already completed
            existing_attempt = db.query(QuizAttempt).filter(
                and_(
                    QuizAttempt.quiz_id == quiz.id,
                    QuizAttempt.candidate_id == current_user.profile.id,
                    QuizAttempt.status.in_(['completed', 'expired'])
                )
            ).first()
            
            # Check if there's an active attempt
            active_attempt = db.query(QuizAttempt).filter(
                and_(
                    QuizAttempt.quiz_id == quiz.id,
                    QuizAttempt.candidate_id == current_user.profile.id,
                    QuizAttempt.status == 'in_progress'
                )
            ).first()
            
            quiz_info = {
                'id': quiz.id,
                'title': quiz.title,
                'description': quiz.description,
                'time_limit': quiz.time_limit,
                'status': 'completed' if existing_attempt else 'active' if active_attempt else 'available',
                'attempt_id': existing_attempt.id if existing_attempt else None,
                'score': existing_attempt.score if existing_attempt else None,
                'max_score': existing_attempt.total_questions if existing_attempt else None,
                'completed_at': existing_attempt.end_time if existing_attempt else None
            }
            quiz_data.append(quiz_info)
        
        return templates.TemplateResponse("client-dep/quizzes_list.html", {
            "request": request,
            "current_user": current_user,
            "quizzes": quiz_data
        })
        
    except Exception as e:
        logger.error(f"Error loading quizzes list: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

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
                Quiz.candidate_id == current_user.profile.id,
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
                QuizAttempt.candidate_id == current_user.profile.id,
                QuizAttempt.status.in_(['completed', 'expired'])
            )
        ).first()
        
        if existing_attempt:
            return templates.TemplateResponse("client-dep/quiz_completed.html", {
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
                QuizAttempt.candidate_id == current_user.profile.id,
                QuizAttempt.status == 'in_progress'
            )
        ).first()
        
        # Check if time has expired for existing attempt
        if active_attempt:
            time_limit = timedelta(minutes=quiz.time_limit	)
            # Use start_time column from database
            start_time = active_attempt.start_time
            if datetime.now() > start_time + time_limit:
                # Mark as expired
                active_attempt.status = 'expired'
                active_attempt.end_time = datetime.now()
                db.commit()

                return templates.TemplateResponse("client-dep/quiz_completed.html", {
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
        
        # Debug: Print question data to understand the structure
        for q in questions:
            print(f"DEBUG: Question {q.id}: options={q.options}, type={type(q.options)}")
            if q.options:
                print(f"DEBUG: Options content: {q.options}")
                print(f"DEBUG: Options length: {len(q.options) if isinstance(q.options, list) else 'Not a list'}")
                
                # Handle case where options might be stored as JSON string
                if isinstance(q.options, str):
                    try:
                        import json
                        q.options = json.loads(q.options)
                        print(f"DEBUG: Parsed options from string: {q.options}")
                    except json.JSONDecodeError:
                        print(f"DEBUG: Failed to parse options as JSON: {q.options}")
                        q.options = []
        
        # Calculate remaining time
        remaining_time = None
        if active_attempt:
            # Use start_time column from database
            start_time = active_attempt.start_time
            elapsed = datetime.now() - start_time
            total_time = timedelta(minutes=quiz.time_limit	)
            remaining_time = max(0, int((total_time - elapsed).total_seconds()))
        else:
            remaining_time = quiz.time_limit * 60
        
        return templates.TemplateResponse("client-dep/quiz_take.html", {
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
                Quiz.candidate_id == current_user.profile.id,
                Quiz.status == 'active'
            )
        ).first()
        
        if not quiz:
            raise HTTPException(status_code=404, detail="Quiz not found")
        
        # Check for existing attempts
        existing_attempt = db.query(QuizAttempt).filter(
            and_(
                QuizAttempt.quiz_id == quiz_id,
                QuizAttempt.candidate_id == current_user.profile.id
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
            candidate_id=current_user.profile.id,
            # start_time will be set automatically by the model default
            status='in_progress'
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
                QuizAttempt.candidate_id == current_user.profile.id,
                QuizAttempt.status == 'in_progress'
            )
        ).first()
        
        if not attempt:
            raise HTTPException(status_code=404, detail="No active quiz attempt found")
        
        # Parse answers
        try:
            answers_data = json.loads(answers)
            print(f"DEBUG: Parsed answers data: {answers_data}")
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid answers format")
        
        # Get quiz questions
        questions = db.query(QuizQuestion).filter(
            QuizQuestion.quiz_id == quiz_id
        ).all()
        
        questions_dict = {q.id: q for q in questions}
        total_correct = 0
        total_questions = len(questions)
        
        # Process each answer
        for question_id_str, answer_data in answers_data.items():
            question_id = int(question_id_str)
            question = questions_dict.get(question_id)
            
            if not question:
                continue
            
            # Get selected option(s) - handle different data formats
            # Frontend sends 'selected_option' for multiple choice and 'answer' for text input
            selected_options = answer_data.get('selected_option') or answer_data.get('answer', [])
            print(f"DEBUG: Question {question_id} - Raw selected_options: {selected_options}, type: {type(selected_options)}")
            
            # Handle different data types that might be sent from frontend
            # The database requires valid JSON in selected_options field
            if isinstance(selected_options, str):
                # Store as JSON string (wrapped in quotes)
                selected_options_json = json.dumps(selected_options)
            elif isinstance(selected_options, (list, tuple)):
                # Store as JSON array
                selected_options_json = json.dumps(selected_options)
            elif isinstance(selected_options, (int, float)):
                # Store as JSON number
                selected_options_json = json.dumps(selected_options)
            else:
                # Fallback: convert to string and store as JSON
                selected_options_json = json.dumps(str(selected_options))
            
            # Ensure we have valid JSON (database constraint requires this)
            if not selected_options_json:
                selected_options_json = json.dumps("No answer provided")
            
            print(f"DEBUG: Question {question_id} - Processed selected_options_json: {selected_options_json}")
            print(f"DEBUG: Question {question_id} - JSON length: {len(selected_options_json)}")
            print(f"DEBUG: Question {question_id} - JSON repr: {repr(selected_options_json)}")
            
            # Determine if answer is correct
            is_correct = False
            if question.correct_answer:
                print(f"DEBUG: Question {question_id} - Correct answer: {question.correct_answer}, Options: {question.options}")
                # The correct_answer is stored as a string representing the index (1-based)
                # We need to compare the selected option with the correct option
                try:
                    correct_index = int(question.correct_answer) - 1  # Convert to 0-based index
                    if question.options and correct_index >= 0 and correct_index < len(question.options):
                        correct_option = question.options[correct_index]
                        print(f"DEBUG: Question {question_id} - Correct option: {correct_option}")
                        # Compare the selected option with the correct option (use original selected_options for comparison)
                        if str(selected_options) == str(correct_option):
                            is_correct = True
                            total_correct += 1
                            print(f"DEBUG: Question {question_id} - Answer is CORRECT!")
                        else:
                            print(f"DEBUG: Question {question_id} - Answer is INCORRECT. Selected: '{selected_options}', Expected: '{correct_option}'")
                except (ValueError, IndexError, TypeError) as e:
                    print(f"DEBUG: Question {question_id} - Error in answer checking: {e}")
                    # Fallback: direct string comparison
                    if str(selected_options) == str(question.correct_answer):
                        is_correct = True
                        total_correct += 1
                        print(f"DEBUG: Question {question_id} - Answer is CORRECT (fallback)!")
                    else:
                        print(f"DEBUG: Question {question_id} - Answer is INCORRECT (fallback). Selected: '{selected_options}', Expected: '{question.correct_answer}'")

            quiz_answer = QuizAnswer(
                attempt_id=attempt.id,
                question_id=question_id,
                selected_options=selected_options_json,
                is_correct=is_correct,
                time_taken_seconds=answer_data.get('time_taken_seconds', 0)
            )
            db.add(quiz_answer)
        
        # Update attempt
        attempt.end_time = datetime.now()
        attempt.status = 'completed'
        attempt.score = total_correct
        attempt.total_correct = total_correct
        attempt.total_questions = total_questions
        
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
                QuizAttempt.candidate_id == current_user.profile.id,
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
        
        return templates.TemplateResponse("client-dep/quiz_results.html", {
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
                QuizAttempt.candidate_id == current_user.profile.id,
                QuizAttempt.status == 'in_progress'
            )
        ).first()
        
        if not attempt:
            return {"success": False, "message": "No active attempt found"}
        
        quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
        if not quiz:
            return {"success": False, "message": "Quiz not found"}
        
        # Use start_time column from database
        start_time = attempt.start_time
        elapsed = datetime.now() - start_time
        total_time = timedelta(minutes=quiz.time_limit	)
        remaining = total_time - elapsed
        
        if remaining.total_seconds() <= 0:
            # Time expired, mark attempt as expired
            attempt.status = 'expired'
            attempt.end_time = datetime.now()
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
