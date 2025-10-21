from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from databasehr.database import SessionLocal
from databasehr.models import Application, ProfileCandidat, Job
import json

router = APIRouter(prefix="/api/hr", tags=["interview-results"])
templates = Jinja2Templates(directory="templates")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/interview-results-page/{candidate_id}")
async def get_interview_results_page(candidate_id: int, request: Request, db: Session = Depends(get_db)):
    """Page pour afficher les résultats d'analyse d'entretien"""
    try:
        # Récupérer l'application avec les informations du candidat et du job
        application = db.query(Application).join(
            ProfileCandidat, Application.candidate_profile_id == ProfileCandidat.id
        ).join(
            Job, Application.job_id == Job.id
        ).filter(
            Application.candidate_profile_id == candidate_id
        ).first()
        
        if not application:
            raise HTTPException(status_code=404, detail="Application not found")
        
        # Vérifier s'il y a une analyse IA
        if not application.ai_interview_analysis:
            raise HTTPException(status_code=404, detail="No AI analysis found for this candidate")
        
        analysis = json.loads(application.ai_interview_analysis)
        
        # Préparer les données pour le template
        context = {
            "request": request,
            "candidate": {
                "id": application.candidate_profile.id,
                "name": f"{application.candidate_profile.first_name} {application.candidate_profile.last_name}",
                "email": application.candidate_profile.email,
                "phone": application.candidate_profile.phone
            },
            "job": {
                "id": application.job.id,
                "title": application.job.title,
                "company": application.job.company_name
            },
            "analysis": analysis,
            "application": {
                "id": application.id,
                "status": application.status,
                "applied_at": application.applied_at
            }
        }
        
        return templates.TemplateResponse("HR-dep/interview_results.html", context)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération des résultats: {str(e)}")

@router.get("/interview-results/{candidate_id}")
async def get_interview_results(candidate_id: int, db: Session = Depends(get_db)):
    """Récupérer les résultats d'analyse d'entretien en JSON"""
    try:
        # Récupérer l'application avec les informations du candidat et du job
        application = db.query(Application).join(
            ProfileCandidat, Application.candidate_profile_id == ProfileCandidat.id
        ).join(
            Job, Application.job_id == Job.id
        ).filter(
            Application.candidate_profile_id == candidate_id
        ).first()
        
        if not application:
            raise HTTPException(status_code=404, detail="Application not found")
        
        # Vérifier s'il y a une analyse IA
        if not application.ai_interview_analysis:
            raise HTTPException(status_code=404, detail="No AI analysis found for this candidate")
        
        analysis = json.loads(application.ai_interview_analysis)
        
        # Préparer les données pour le template
        context = {
            "candidate": {
                "id": application.candidate_profile.id,
                "name": f"{application.candidate_profile.first_name} {application.candidate_profile.last_name}",
                "email": application.candidate_profile.email,
                "phone": application.candidate_profile.phone
            },
            "job": {
                "id": application.job.id,
                "title": application.job.title,
                "company": application.job.company_name
            },
            "analysis": analysis,
            "application": {
                "id": application.id,
                "status": application.status,
                "applied_at": application.applied_at
            }
        }
        
        return context
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération des résultats: {str(e)}")

@router.get("/interview-results")
async def list_interview_results(request: Request, db: Session = Depends(get_db)):
    """Liste des candidats avec des analyses d'entretien disponibles"""
    try:
        # Récupérer toutes les applications avec des analyses IA
        applications = db.query(Application).join(
            ProfileCandidat, Application.candidate_profile_id == ProfileCandidat.id
        ).join(
            Job, Application.job_id == Job.id
        ).filter(
            Application.ai_interview_analysis.isnot(None)
        ).all()
        
        results = []
        for app in applications:
            analysis = json.loads(app.ai_interview_analysis)
            results.append({
                "candidate_id": app.candidate_profile_id,
                "candidate_name": f"{app.candidate_profile.first_name} {app.candidate_profile.last_name}",
                "job_title": app.job.title,
                "company": app.job.company_name,
                "analysis_date": app.applied_at,
                "conversation_turns": len(analysis),
                "application_id": app.id
            })
        
        return {
            "success": True,
            "results": results
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération de la liste: {str(e)}")
