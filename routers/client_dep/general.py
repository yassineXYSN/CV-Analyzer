from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from database import SessionLocal
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


@router.post("/api/candidate/choose-interview-slot")
async def candidate_choose_interview_slot(request: dict, db: Session = Depends(get_db)):
    """
    Endpoint pour que le candidat confirme son choix de créneau d'entretien
    """
    try:
        slot_id = request.get('slot_id')
        application_id = request.get('application_id')
        
        if not slot_id or not application_id:
            return JSONResponse(content={
                "success": False,
                "message": "slot_id et application_id sont requis"
            }, status_code=400)
        
        print(f"🎯 CANDIDATE CHOICE CLIENT: Candidat {application_id} choisit le créneau {slot_id}")
        
        # Utiliser la base de données HR pour chercher le slot
        from databasehr.database import SessionLocal as HRSessionLocal
        from databasehr.models import InterviewSlot, SlotStatus, Application as HRApplication
        
        hr_db = HRSessionLocal()
        try:
            # Vérifier que le créneau existe et est confirmé par le HR
            slot = hr_db.query(InterviewSlot).filter(
                InterviewSlot.id == slot_id,
                InterviewSlot.application_id == application_id,
                InterviewSlot.is_confirmed == True
            ).first()
            
            if not slot:
                return JSONResponse(content={
                    "success": False,
                    "message": "Créneau non trouvé ou non confirmé"
                }, status_code=400)
            
            # Mettre le statut du créneau à "reserved" (choisi par le candidat)
            slot.status = SlotStatus.RESERVED
            
            # Récupérer l'application côté HR
            hr_application = hr_db.query(HRApplication).filter(HRApplication.id == application_id).first()
            if hr_application:
                # Maintenant remplir les champs d'entretien
                print(f"🔍 DEBUG CLIENT: Avant mise à jour - interview_date: {hr_application.interview_date}, interview_time: {hr_application.interview_time}, interview_type: {hr_application.interview_type}")
                
                hr_application.interview_date = slot.start_time
                hr_application.interview_time = slot.start_time.strftime('%H:%M')
                hr_application.interview_type = "Entretien confirmé"
                hr_application.status = 'interview_scheduled'
                
                print(f"🔍 DEBUG CLIENT: Après mise à jour - interview_date: {hr_application.interview_date}, interview_time: {hr_application.interview_time}, interview_type: {hr_application.interview_type}")
                print(f"✅ CANDIDATE CHOICE CLIENT: Données d'entretien mises à jour pour l'application {hr_application.id}")
            else:
                print(f"❌ CANDIDATE CHOICE CLIENT: Application HR {application_id} non trouvée")
            
            hr_db.commit()
            print(f"🔍 DEBUG CLIENT: Commit HR effectué")
            
            return JSONResponse(content={
                "success": True,
                "message": "Choix de créneau confirmé avec succès",
                "slot": {
                    "id": slot.id,
                    "start_time": slot.start_time.isoformat(),
                    "end_time": slot.end_time.isoformat(),
                    "status": slot.status.value
                }
            })
            
        finally:
            hr_db.close()
        
    except Exception as e:
        print(f"❌ CANDIDATE CHOICE CLIENT ERROR: {str(e)}")
        return JSONResponse(content={
            "success": False,
            "message": f"Erreur lors de la confirmation: {str(e)}"
        }, status_code=500)