from fastapi import APIRouter, Request, UploadFile, File, Form, Depends
from fastapi.responses import HTMLResponse
from database import SessionLocal
from routers.client_dep.dependencies import get_db, get_current_user
import extract_information_cv.text_extractor as text_extractor
import extract_information_cv.textcleaner as textcleaner
import cv_analyzer.data_generator as data_generator
from cv_analyzer.information_analyzer import compute_similarity
from databaseclient.insert_to_db import insert_candidate_data
import os
from pydantic import BaseModel
import cv_analyzer.description_generator as generate_job_description
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

router = APIRouter()
# Templates
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

# Chemin vers le dossier templates
templates_dir = os.path.join(BASE_DIR, "templates")

templates = Jinja2Templates(directory=templates_dir)


class TopicRequest(BaseModel):
    topic: str

@router.get("/analyze", response_class=HTMLResponse)
def analyze_page(request: Request, db: Session = Depends(get_db)):
    current_user = get_current_user(request, db)
    return templates.TemplateResponse("client-dep/analyze.html", {
        "request": request,
        "current_user": current_user
    })

@router.post("/scan", response_class=HTMLResponse)
async def scan_file(
    request: Request,
    filetoscan: UploadFile = File(...),
    selectedProfiles: str = Form(...),
    db: Session = Depends(get_db)
):
    current_user = get_current_user(request, db)
    
    # Créer le dossier uploads s'il n'existe pas
    os.makedirs("uploads", exist_ok=True)
    
    file_location = f"uploads/{filetoscan.filename}"
    print(selectedProfiles)

    # Save file to disk temporarily
    with open(file_location, "wb") as f:
        f.write(await filetoscan.read())
    
    
    # Process the file
    print("Extracting text from the file...")
    pdf_text, images_text = text_extractor.process_file(file_location)
    print("Text extraction completed.")

    # Clean up
    print("Cleaning up the extracted text...")
    pdf_text = textcleaner.cleantext(pdf_text)
    print("Cleaned up the extracted text.")
    # Generate summary.
    print("Generating summary ...")
    summary = data_generator.generate_summary(pdf_text, images_text)
    print("Summary generation completed.")
    print("Generating structured data ...")
    data_json = data_generator.generate_json(pdf_text)
    print(data_json)
    
    jobs_description = generate_job_description.generate_job_description(selectedProfiles)

    # Compute matching score
    score = compute_similarity(summary, jobs_description)
    
    skills_titles = [skill.split(":")[0] for skill in data_json["skills"]]
    skills_titles_str = ", ".join(skills_titles)


    

    # Insérer les données en base et lier au user si connecté
    candidate_id = insert_candidate_data(data_json, summary, current_user.id if current_user else None)

    # Ensuite on affiche la page avec les résultats
    return templates.TemplateResponse("client-dep/result.html", {
        "request": request,
        "filename": filetoscan.filename,
        "pdf_text": pdf_text,
        "images_text": images_text,
        "summary": summary,
        "score": score,
        "user_info": data_json,
        "skills_titles": skills_titles_str,
        "candidate_id": candidate_id,
        "current_user": current_user
    })

@router.post("/create-detailed-analysis")
async def create_detailed_analysis(request: Request):
    try:
        data = await request.json()
        pdf_text = data.get('pdf_text')

        
        # For testing, return sample data
        return {
            "success": True,
            "categorie_scores": {
                "Expérience Professionnelle": 85,
                "Compétences Techniques": 78,
                "Formation & Éducation": 92,
                "Certifications": 65,
                "Compétences Relationnelles": 73,
                "Présentation & Structure": 88
            },
            "good_points": [
                "Solide expérience de 5+ années dans le développement web",
                "Maîtrise excellente des technologies modernes (React, Node.js, Python)",
                "Formation universitaire pertinente en informatique",
                "Projets personnels démontrant la passion pour la technologie",
                "Expérience en gestion d'équipe et leadership technique",
                "Compétences en méthodologies agiles (Scrum, Kanban)",
                "Excellente capacité d'adaptation et d'apprentissage continu",
                "Portfolio bien documenté avec projets variés"
            ],
            "weak_points": [
                "Manque de certifications professionnelles récentes",
                "Peu d'expérience avec les technologies cloud (AWS, Azure)",
                "Absence de projets open source contributifs",
                "Compétences en DevOps limitées",
                "Pas de mention d'expérience en sécurité informatique",
                "Lacunes dans les compétences en analyse de données",
                "Communication écrite pourrait être améliorée"
            ],
            "improvements": [
                "Obtenir des certifications AWS ou Azure pour renforcer les compétences cloud",
                "Contribuer à des projets open source pour démontrer l'engagement communautaire",
                "Suivre une formation en cybersécurité pour élargir le profil technique",
                "Développer des compétences en DevOps (Docker, Kubernetes, CI/CD)",
                "Ajouter des métriques quantifiées aux réalisations professionnelles",
                "Créer un blog technique pour démontrer les compétences en communication",
                "Participer à des conférences ou meetups pour le networking professionnel",
                "Apprendre des outils d'analyse de données (SQL avancé, Python data science)"
            ]
        }
        
    except Exception as e:
        print(f"Error in create_detailed_analysis: {str(e)}")
        return {"success": False, "error": str(e)}