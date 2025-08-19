import json
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI, Request, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi import FastAPI
from pydantic import BaseModel
import os
from dotenv import load_dotenv
from databasehr.database import engine, SessionLocal
import databasehr.models as models
from routers.hr import (
    authhr, company, department, 
    employee, job, application, candidate, 
    dashboard
)
from database import engine
import databaseclient.models as models
from routers.client_dep import auth, jobs, profiles, scan, general, notifications

from models import QuizAttempt
import re
from quiz_service import QuizService

load_dotenv()
app = FastAPI()

# Create database tables
app.include_router(auth.router)
app.include_router(jobs.router)
app.include_router(profiles.router)
app.include_router(scan.router)
app.include_router(general.router)
app.include_router(notifications.router)

# Création des tables
models.Base.metadata.create_all(bind=engine)

# Create static directory
static_dir = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(static_dir, exist_ok=True)

# Create uploads directory
uploads_dir = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(uploads_dir, exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory=static_dir), name="static")
app.mount("/uploads", StaticFiles(directory=uploads_dir), name="uploads")

# Initialize templates
templates = Jinja2Templates(directory="templates")
# Include routers
app.include_router(authhr.router)
app.include_router(company.router)
app.include_router(department.router)
app.include_router(employee.router)
app.include_router(job.router)
app.include_router(application.router)
app.include_router(candidate.router)
app.include_router(dashboard.router)

# Quiz endpoints
quiz_service = QuizService()

@app.post("/generate-quiz")
async def generate_quiz(request: Request):
    """Generate quizzes for a candidate (one per skill)"""
    try:
        data = await request.json()
        candidate_id = data.get("candidate_id")
        job_title = data.get("job_title", "Développeur")
        num_questions = data.get("num_questions", 10)
        if not candidate_id:
            return {"success": False, "error": "Candidate ID is required"}
        try:
            quizzes = quiz_service.generate_quiz_for_candidate(
                candidate_id=candidate_id,
                job_title=job_title,
                num_questions=num_questions
            )
        except Exception as e:
            return {"success": False, "error": str(e)}
        return {"success": True, "quizzes": quizzes}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/submit-multi-quiz")
async def submit_multi_quiz(request: Request):
    """Submit multiple per-skill quizzes and get combined evaluation"""
    try:
        data = await request.json()
        submissions = data.get("submissions", [])  # List of {quiz_id, candidate_id, answers}
        if not submissions:
            return {"success": False, "error": "No submissions provided"}
        all_evaluations = []
        total_score = 0
        for sub in submissions:
            quiz_id = sub.get("quiz_id")
            candidate_id = sub.get("candidate_id")
            answers = sub.get("answers", {})
            if not quiz_id or not candidate_id:
                continue
            evaluation = quiz_service.submit_quiz_attempt(quiz_id, candidate_id, answers)
            all_evaluations.append(evaluation)
            total_score += evaluation.get("total_score", 0)
        avg_score = total_score / len(all_evaluations) if all_evaluations else 0
        return {"success": True, "evaluations": all_evaluations, "average_score": avg_score}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/quiz/{quiz_id}")
async def get_quiz(quiz_id: int):
    """Get a specific quiz by ID"""
    try:
        quiz_data = quiz_service.get_quiz(quiz_id)
        if not quiz_data:
            return {"success": False, "error": "Quiz not found"}
        
        return {"success": True, "quiz": quiz_data}
        
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/submit-quiz")
async def submit_quiz(request: Request):
    """Submit quiz answers and get evaluation"""
    try:
        data = await request.json()
        quiz_id = data.get("quiz_id")
        candidate_id = data.get("candidate_id")
        answers = data.get("answers", {})
        timer = data.get("timer")  # <-- Accept timer value
        
        if not quiz_id or not candidate_id:
            return {"success": False, "error": "Quiz ID and Candidate ID are required"}
        
        evaluation = quiz_service.submit_quiz_attempt(quiz_id, candidate_id, answers)
        # Attach timer to evaluation for immediate display
        if timer:
            evaluation["timer"] = timer
        
        return {"success": True, "evaluation": evaluation}
        
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/quiz-history/{candidate_id}")
async def get_quiz_history(candidate_id: int):
    """Get quiz history for a candidate"""
    try:
        history = quiz_service.get_candidate_quiz_history(candidate_id)
        return {"success": True, "history": history}
        
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/quiz-stats/{quiz_id}")
async def get_quiz_statistics(quiz_id: int):
    """Get statistics for a specific quiz"""
    try:
        stats = quiz_service.get_quiz_statistics(quiz_id)
        return {"success": True, "statistics": stats}
        
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/take-quiz/{candidate_id}", response_class=HTMLResponse)
async def take_quiz(
    request: Request,
    candidate_id: int,
    num_questions: int = Query(5),
    assignment_id: int = Query(None),
    job_id: int = Query(None),
    job_title: str = Query(None)
):
    """Display all per-skill quizzes for a candidate on one page"""
    try:
        # Check if this is a job-based quiz assignment
        if assignment_id:
            db = SessionLocal()
            try:
                from models import JobQuizAssignment
                assignment = db.query(JobQuizAssignment).filter(
                    JobQuizAssignment.id == assignment_id,
                    JobQuizAssignment.candidate_id == candidate_id
                ).first()
                
                if assignment and assignment.quiz_attempt_id:
                    # Get existing quiz attempt
                    from models import QuizAttempt
                    quiz_attempt = db.query(QuizAttempt).filter(QuizAttempt.id == assignment.quiz_attempt_id).first()
                    if quiz_attempt:
                        questions = quiz_attempt.questions
                        # Derive skill name from first question's skill_related if available
                        derived_skill = None
                        try:
                            if isinstance(questions, list) and questions:
                                first_q = questions[0] if isinstance(questions[0], dict) else None
                                if first_q and first_q.get('skill_related'):
                                    derived_skill = str(first_q.get('skill_related')).strip()
                        except Exception:
                            derived_skill = None
                        quizzes = [{
                            "quiz_id": quiz_attempt.id,
                            "skill": derived_skill or quiz_attempt.job_title,
                            "job_title": quiz_attempt.job_title,
                            "questions": questions
                        }]
                        return templates.TemplateResponse("client-dep/quiz.html", {
                            "request": request,
                            "quizzes": quizzes,
                            "candidate_id": candidate_id,
                            "assignment_id": assignment_id,
                            "error_message": None
                        })
            finally:
                db.close()
        
        # Fallback to job-based skill quiz generation using Compétences Requises
        error_message = None
        quizzes = []
        try:
            if job_id is None and not job_title:
                raise ValueError("Paramètre manquant: fournissez 'job_id' ou 'job_title' pour générer le QCM.")
            quizzes = quiz_service.generate_quiz_for_candidate(
                candidate_id=candidate_id,
                job_title=job_title or "",
                num_questions=num_questions,
                job_id=job_id
            )
        except Exception as e:
            error_message = f"Erreur lors de la génération du QCM: {str(e)}"
        
        # Show all quizzes, including those with warnings or placeholder questions
        if not quizzes:
            error_message = "Aucune question générée pour les compétences du candidat. Veuillez réessayer ou contacter l'administrateur."
        
        return templates.TemplateResponse("client-dep/quiz.html", {
            "request": request,
            "quizzes": quizzes or [],
            "candidate_id": candidate_id,
            "error_message": error_message
        })
    except Exception as e:
        import traceback
        error_message = f"Erreur lors de la génération du QCM: {str(e)}"
        return templates.TemplateResponse("client-dep/quiz.html", {
            "request": request,
            "quizzes": [],
            "candidate_id": candidate_id,
            "error_message": error_message
        })

@app.get("/quiz-results/{attempt_id}", response_class=HTMLResponse)
async def quiz_results(request: Request, attempt_id: int):
    """Display quiz results for a specific attempt"""
    try:
        db = SessionLocal()
        attempt = db.query(QuizAttempt).filter(QuizAttempt.id == attempt_id).first()
        if not attempt:
            return templates.TemplateResponse("client-dep/quiz_results.html", {
                "request": request,
                "evaluation": None,
                "candidate_id": None,
                "timer": None
            })
        # Create evaluation object from attempt data
        evaluation = {
            "total_score": attempt.total_score,
            "category_scores": attempt.category_scores,
            "detailed_results": attempt.detailed_results,
            "quiz_title": attempt.job_title,
            "job_title": attempt.job_title
        }
        timer = request.query_params.get('timer')
        return templates.TemplateResponse("client-dep/quiz_results.html", {
            "request": request,
            "evaluation": evaluation,
            "candidate_id": attempt.candidate_id,
            "timer": timer
        })
    except Exception as e:
        return templates.TemplateResponse("client-dep/quiz_results.html", {
            "request": request,
            "evaluation": None,
            "candidate_id": None,
            "timer": None
        })
    finally:
        db.close()

@app.get("/multi-quiz-results", response_class=HTMLResponse)
async def multi_quiz_results(request: Request, attempt_ids: str):
    """Display results for multiple quiz attempts (by attempt_ids comma-separated)"""
    try:
        db = SessionLocal()
        ids = [int(i) for i in attempt_ids.split(",") if i.strip().isdigit()]
        attempts = db.query(QuizAttempt).filter(QuizAttempt.id.in_(ids)).all()
        evaluations = []
        candidate_id = None
        candidate_name = None
        
        for attempt in attempts:
            if candidate_id is None:
                candidate_id = attempt.candidate_id
                # Fetch candidate name
                from databaseclient.models import ProfileCandidat
                candidate = db.query(ProfileCandidat).filter(ProfileCandidat.id == candidate_id).first()
                if candidate:
                    candidate_name = candidate.name
        
        for attempt in attempts:
            evaluations.append({
                "total_score": attempt.total_score,
                "category_scores": attempt.category_scores,
                "detailed_results": attempt.detailed_results,
                "quiz_title": attempt.job_title,
                "job_title": attempt.job_title
            })
        
        return templates.TemplateResponse("client-dep/multi_quiz_results.html", {
            "request": request,
            "evaluations": evaluations,
            "candidate_id": candidate_id,
            "candidate_name": candidate_name
        })
    except Exception as e:
        return templates.TemplateResponse("client-dep/multi_quiz_results.html", {
            "request": request,
            "evaluations": [],
            "candidate_id": None,
            "candidate_name": None
        })
    finally:
        db.close()
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

