from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from typing import Optional, List, Dict
from sqlalchemy.orm import Session
from databasehr.database import SessionLocal
from databasehr.models import Application
import os
import json
import tempfile
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from utils1.cleanconv import clean_conversation

# Initialize templates
templates = Jinja2Templates(directory="templates")

router = APIRouter(prefix="/api/hr", tags=["ai-interview-analysis"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/ai-interview-analysis")
async def analyze_interview_with_ai(
    application_id: int = Form(...),
    hr_audio: Optional[UploadFile] = File(None),
    candidate_audio: Optional[UploadFile] = File(None),
    interview_video: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    """
    Endpoint pour l'analyse IA des fichiers média d'entretien.
    """
    try:
        print("Yassine analyzing interview with ai")
        # Vérifier que l'application existe
        application = db.query(Application).filter(
            Application.id == application_id
        ).first()
        print(f"Yassine application found: {application.id if application else 'None'}")
        
        if not application:
            raise HTTPException(status_code=404, detail="Application not found")
        
        # Vérifier qu'au moins un fichier est fourni
        if not hr_audio and not candidate_audio and not interview_video:
            raise HTTPException(status_code=400, detail="At least one media file is required")
        
        # Créer des fichiers temporaires
        temp_files = []
        print("Yassine temp files created",temp_files)
        try:
            print("Yassine trying to save files")
            # Sauvegarder les fichiers uploadés
            hr_audio_path = None
            candidate_audio_path = None
            video_path = None
            
            if hr_audio:
                hr_audio_path = tempfile.mktemp(suffix=".wav")
                with open(hr_audio_path, "wb") as f:
                    f.write(await hr_audio.read())
                temp_files.append(hr_audio_path)
            
            if candidate_audio:
                candidate_audio_path = tempfile.mktemp(suffix=".wav")
                with open(candidate_audio_path, "wb") as f:
                    f.write(await candidate_audio.read())
                temp_files.append(candidate_audio_path)
            
            if interview_video:
                video_path = tempfile.mktemp(suffix=".mp4")
                with open(video_path, "wb") as f:
                    f.write(await interview_video.read())
                temp_files.append(video_path)
            
            # Utiliser la fonction clean_conversation
            print("Starting AI analysis with clean_conversation...")
            analysis_result = clean_conversation(
                hr_audio_path or "", 
                candidate_audio_path or "", 
                video_path or "",
                application_id
            )
            
            print(f"Analysis result type: {type(analysis_result)}")
            print(f"Analysis result: {analysis_result}")
            
            # Handle the new combined format (conversation + analysis)
            if isinstance(analysis_result, dict) and "conversation" in analysis_result and "analysis" in analysis_result:
                # New combined format: conversation + comprehensive analysis
                analysis_data = {
                    "type": "combined_analysis",
                    "conversation": analysis_result["conversation"],
                    "analysis": analysis_result["analysis"]
                }
            elif isinstance(analysis_result, dict):
                # Comprehensive analysis only
                analysis_data = {
                    "type": "comprehensive_analysis",
                    "data": analysis_result
                }
            elif isinstance(analysis_result, list):
                # Old format: conversation list
                analysis_data = {
                    "type": "conversation_analysis", 
                    "data": analysis_result
                }
            else:
                # Fallback format
                analysis_data = {
                    "type": "fallback",
                    "data": [{
                        "speaker": "System",
                        "emotion": "neutral",
                        "text": str(analysis_result)
                    }]
                }
            
            print(f"Final analysis data: {analysis_data}")
            
            # Sauvegarder dans la base de données
            try:
                print(f"Before save - hasattr(Application, 'ai_interview_analysis') = {hasattr(Application, 'ai_interview_analysis')}")
                # Tentative via l'attribut ORM (chemin préféré)
                if hasattr(application, 'ai_interview_analysis'):
                    current_val = getattr(application, 'ai_interview_analysis')
                    print(f"Before save - application.ai_interview_analysis: {current_val}")
                    setattr(application, 'ai_interview_analysis', json.dumps(analysis_data))
                    print(f"After assignment - application.ai_interview_analysis: {application.ai_interview_analysis}")
                    db.commit()
                    print(f"Database commit successful for application {application_id} (ORM path)")
                    db.refresh(application)
                    print(f"After refresh - application.ai_interview_analysis: {application.ai_interview_analysis}")
                else:
                    # Fallback: écriture SQL brute si l'attribut ORM n'existe pas
                    print("ORM attribute missing — falling back to raw SQL UPDATE")
                    from sqlalchemy import text
                    db.execute(
                        text("UPDATE applications SET ai_interview_analysis = :data WHERE id = :id"),
                        {"data": json.dumps(analysis_data), "id": application_id}
                    )
                    db.commit()
                    print(f"Database commit successful for application {application_id} (raw SQL path)")
            except Exception as save_error:
                print(f"Error saving to database: {save_error}")
                db.rollback()
                raise save_error
            
            # Rediriger vers la page de résultats
            return RedirectResponse(
                url=f"/api/hr/interview-analysis-results/{application_id}",
                status_code=303
            )
        
        finally:
            # Nettoyer les fichiers temporaires
            for temp_file in temp_files:
                try:
                    if os.path.exists(temp_file):
                        os.remove(temp_file)
                except Exception as e:
                    print(f"Error removing temp file {temp_file}: {e}")
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'analyse IA: {str(e)}")

@router.get("/check-analysis/{application_id}")
async def check_analysis_exists(application_id: int, db: Session = Depends(get_db)):
    """Check if AI analysis exists for an application"""
    try:
        print(f"Yassine checking analysis for application {application_id}")
        
        # Try ORM first
        application = db.query(Application).filter(
            Application.id == application_id
        ).first()
        
        if not application:
            print(f"Application {application_id} not found")
            return {"has_analysis": False, "analysis_data": None}
        
        # Check if analysis exists
        has_analysis = False
        analysis_data = None
        
        try:
            if hasattr(application, 'ai_interview_analysis') and application.ai_interview_analysis:
                has_analysis = True
                analysis_data = application.ai_interview_analysis
                print(f"Found analysis via ORM: {has_analysis}")
            else:
                print("No analysis found via ORM, trying raw SQL")
                # Fallback to raw SQL
                from sqlalchemy import text
                row = db.execute(
                    text("SELECT ai_interview_analysis FROM applications WHERE id = :id"),
                    {"id": application_id}
                ).fetchone()
                
                if row and row[0]:
                    has_analysis = True
                    analysis_data = row[0]
                    print(f"Found analysis via raw SQL: {has_analysis}")
                else:
                    print("No analysis found via raw SQL either")
                    
        except Exception as e:
            print(f"Error checking analysis: {e}")
            has_analysis = False

        print(f"Yassine has_analysis: {has_analysis}")
        return {
            "has_analysis": has_analysis,
            "analysis_data": analysis_data,
            "application_id": application_id
        }
        
    except Exception as e:
        print(f"Error in check_analysis_exists: {e}")
        return {"has_analysis": False, "analysis_data": None, "error": str(e)}

@router.get("/interview-analysis-results/{application_id}")
async def show_interview_analysis_results(application_id: int, request: Request, db: Session = Depends(get_db)):
    """Afficher la page de résultats de l'analyse IA"""
    print(f"Yassine showing interview analysis results for application {application_id}")
    try:
        print("Querying application from database...")
        application = db.query(Application).filter(
            Application.id == application_id
        ).first()
        print("Application queried.")

        
        print(f"Application found: {application is not None}")
        if application:
            print(f"Application ID: {application.id}")
            print(f"AI analysis data: {application.ai_interview_analysis}")
            print(f"AI analysis data type: {type(application.ai_interview_analysis)}")
            print("test")
        
        if not application:
            print("Application not found in database")
            raise HTTPException(status_code=404, detail="Application not found")
        
        # Lire la donnée via ORM si possible, sinon fallback SQL brut
        raw_json = None
        if hasattr(application, 'ai_interview_analysis'):
            raw_json = application.ai_interview_analysis
            print(f"Read via ORM - ai_interview_analysis present: {raw_json is not None}")
        else:
            print("ORM attribute missing — trying raw SQL SELECT")
            from sqlalchemy import text
            row = db.execute(
                text("SELECT ai_interview_analysis FROM applications WHERE id = :id"),
                {"id": application_id}
            ).fetchone()
            raw_json = row[0] if row else None
            print(f"Read via raw SQL - ai_interview_analysis present: {raw_json is not None}")

        if not raw_json:
            print("No AI analysis found in database - column is None or empty")
            print(f"Application status: {application.status}")
            print(f"Application columns: {[c.name for c in application.__table__.columns]}")
            raise HTTPException(status_code=404, detail="No AI analysis found for this application")

        print("AI analysis data found, parsing JSON...")
        analysis = json.loads(raw_json)
        print(f"Analysis loaded: {len(analysis) if analysis else 0} items")
        
        return templates.TemplateResponse("HR-dep/interview-analysis-results.html", {
            "request": request,
            "candidate_id": application.candidate_profile_id,
            "application_id": application_id,
            "analysis": analysis
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'affichage des résultats: {str(e)}")
