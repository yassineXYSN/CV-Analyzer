from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from database import SessionLocal
from routers.client_dep import interview
from routers.client_dep.dependencies import get_db, get_current_user
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from databaseclient.models import Application, Job, Company, Department, JobSkill, Notification  # Added Job-related imports
import os


router = APIRouter()
# Templates
# Aller au dossier parent (c'est là que se trouve le vrai dossier templates)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

# Dossier correct des templates (C:\Users\yassine\Documents\GitHub\Training\templates)
templates_dir = os.path.join(BASE_DIR, "templates")

templates = Jinja2Templates(directory=templates_dir)


@router.get("/", response_class=HTMLResponse)
def home(request: Request, db: Session = Depends(get_db)):
    current_user = get_current_user(request, db)

    return templates.TemplateResponse("client-dep/index.html", {
        "request": request,
        "current_user": current_user
    })


@router.get("/api/job-profiles")
def get_job_profiles(db: Session = Depends(get_db)):
    """
    Fetch active job profiles from the database to populate the profile selector
    """
    try:
        # Get active jobs with their company and skills information
        jobs = db.query(Job).join(Company).join(Department).filter(
            Job.status == 'active'
        ).limit(50).all()  # Limit to 50 most recent jobs
        
        job_profiles = []
        for job in jobs:
            # Get job skills
            job_skills = db.query(JobSkill).filter(JobSkill.job_id == job.id).all()
            skills_list = [skill.skill_name for skill in job_skills]
            
            # Create profile data
            profile_data = {
                "id": job.id,
                "title": job.title,
                "company": job.company.company_name if job.company else "Entreprise",
                "department": job.department.name if job.department else "Département",
                "description": job.description[:200] + "..." if len(job.description) > 200 else job.description,
                "requirements": job.requirements,
                "responsibilities": job.responsibilities,
                "skills": skills_list,
                "employment_type": job.employment_type,
                "salary_min": float(job.salary_min) if job.salary_min else None,
                "salary_max": float(job.salary_max) if job.salary_max else None,
                "priority": job.priority,
                "created_at": job.created_at.isoformat() if job.created_at else None
            }
            job_profiles.append(profile_data)
        
        return JSONResponse(content={
            "success": True,
            "profiles": job_profiles
        })
        
    except Exception as e:
        print(f"Error fetching job profiles: {e}")
        return JSONResponse(content={
            "success": False,
            "profiles": [],
            "error": str(e)
        }, status_code=500)


@router.get("/api/job/{job_id}")
def get_job_details(job_id: int, db: Session = Depends(get_db)):
    """
    Get detailed information about a specific job for scoring purposes
    """
    try:
        job = db.query(Job).join(Company).join(Department).filter(
            Job.id == job_id
        ).first()
        
        if not job:
            return JSONResponse(content={
                "success": False,
                "error": "Job not found"
            }, status_code=404)
        
        # Get job skills
        job_skills = db.query(JobSkill).filter(JobSkill.job_id == job.id).all()
        skills_data = [
            {
                "name": skill.skill_name,
                "level": skill.skill_level,
                "required": bool(skill.is_required)
            } for skill in job_skills
        ]
        
        job_details = {
            "id": job.id,
            "title": job.title,
            "company": {
                "name": job.company.company_name if job.company else "Entreprise",
                "industry": job.company.industry if job.company else None,
                "size": job.company.company_size if job.company else None
            },
            "department": job.department.name if job.department else "Département",
            "description": job.description,
            "requirements": job.requirements,
            "responsibilities": job.responsibilities,
            "skills": skills_data,
            "employment_type": job.employment_type,
            "salary_min": float(job.salary_min) if job.salary_min else None,
            "salary_max": float(job.salary_max) if job.salary_max else None,
            "priority": job.priority,
            "experience_level": "intermediate"  # Default, could be derived from requirements
        }
        
        return JSONResponse(content={
            "success": True,
            "job": job_details
        })
        
    except Exception as e:
        print(f"Error fetching job details: {e}")
        return JSONResponse(content={
            "success": False,
            "error": str(e)
        }, status_code=500)

@router.get("/planned-interview", response_class=HTMLResponse)
async def planned_interview_page(request: Request, db: Session = Depends(get_db)):
    """
    Page des entretiens planifiés pour l'utilisateur connecté.
    Affiche tous les entretiens planifiés dans un calendrier.
    """
    current_user = get_current_user(request, db)
    if not current_user:
        # Redirige vers login si l'utilisateur n'est pas connecté
        return templates.TemplateResponse("client-dep/auth/login.html", {
            "request": request,
            "error": "Vous devez être connecté pour voir vos entretiens planifiés"
        })

    # Récupère toutes les notifications d'entretien planifiés acceptés
    notifications = db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.type == "interview_scheduled",
        Notification.response_status == 1  # accepté
    ).order_by(Notification.created_at.desc()).all()

    interviews = []
    for notification in notifications:
        # Récupère l'application liée à la notification
        application = db.query(Application).filter(Application.id == notification.application_id).first()
        if application and application.interview_date:
            interview_date = application.interview_date.isoformat()  # format ISO pour JS
            application_id = application.id
            
            import os
            result_file = f"interview_results/result_{application_id}.json"
            is_completed = os.path.exists(result_file)
            
            interviews.append({
                "interview_date": interview_date,
                "application_id": application_id,
                "is_completed": is_completed
            })

    return templates.TemplateResponse("client-dep/planned-interview.html", {
        "request": request,
        "current_user": current_user,
        "interviews": interviews
    })