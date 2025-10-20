from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
from databasehr.database import SessionLocal
from databasehr.models import Application, HRAdmin

router = APIRouter(prefix="/api/hr", tags=["interview-analysis"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class InterviewAnalysisRequest(BaseModel):
    candidate_id: int
    application_id: int
    overall_rating: int
    positive_points: Optional[str] = None
    improvement_points: Optional[str] = None
    recommendation: str

@router.post("/interview-analysis")
async def save_interview_analysis(
    analysis_data: InterviewAnalysisRequest,
    db: Session = Depends(get_db)
):
    try:
        # Find the application using both candidate_id and application_id for validation
        application = db.query(Application).filter(
            Application.id == analysis_data.application_id,
            Application.candidate_profile_id == analysis_data.candidate_id
        ).first()
        
        if not application:
            raise HTTPException(status_code=404, detail="Application not found for this candidate")
        
        # For now, we'll just update the application status and add a simple note
        # In a real implementation, you might want to create a separate InterviewAnalysis table
        
        # Update application with analysis data
        application.hr_rating = analysis_data.overall_rating
        application.hr_notes = f"Points positifs: {analysis_data.positive_points or 'N/A'}\nPoints d'amélioration: {analysis_data.improvement_points or 'N/A'}\nRecommandation: {analysis_data.recommendation}"
        
        # Update status based on recommendation
        if analysis_data.recommendation in ["strong_hire", "hire"]:
            application.status = "accepted"
        elif analysis_data.recommendation in ["no_hire", "strong_no_hire"]:
            application.status = "rejected"
        
        db.commit()
        
        return {
            "success": True,
            "message": "Analyse d'entretien enregistrée avec succès",
            "application_id": application.id,
            "new_status": application.status
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'enregistrement: {str(e)}")
