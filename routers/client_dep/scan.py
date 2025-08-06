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
        
        print("Hello from create_detailed_analysis")
        print("PDF text length:", len(pdf_text) if pdf_text else 0)
        
        print("Generating categorie scores...")
        categorie_scores_raw = data_generator.generate_categorie_scores(pdf_text)
        print("Categorie scores generated:", categorie_scores_raw[:200] + "..." if len(categorie_scores_raw) > 200 else categorie_scores_raw)
        
        print("Generating good points...")
        good_points_raw = data_generator.generate_good_points(pdf_text)
        print("Good points generated:", good_points_raw[:200] + "..." if len(good_points_raw) > 200 else good_points_raw)
        
        print("Generating weak points...")
        weak_points_raw = data_generator.generate_weak_points(pdf_text)
        print("Weak points generated:", weak_points_raw[:200] + "..." if len(weak_points_raw) > 200 else weak_points_raw)
        
        print("Generating improvements...")
        improvements_raw = data_generator.generate_improvements(pdf_text, good_points_raw, weak_points_raw, categorie_scores_raw)
        print("Improvements generated:", improvements_raw[:200] + "..." if len(improvements_raw) > 200 else improvements_raw)
        
        # Parse the results
        categorie_scores = parse_category_scores(categorie_scores_raw)
        good_points = parse_bullet_points(good_points_raw)
        weak_points = parse_bullet_points(weak_points_raw)
        improvements = parse_bullet_points(improvements_raw)

        # Add this return statement
        return {
            "success": True,
            "categorie_scores": categorie_scores,
            "good_points": good_points,
            "weak_points": weak_points,
            "improvements": improvements
        }
        
    except Exception as e:
        print(f"Error in create_detailed_analysis: {str(e)}")
        return {"success": False, "error": str(e)}
    



import json

def parse_category_scores(categorie_scores_raw: str) -> dict:
    """
    Parses category scores JSON string into a dictionary.
    Handles common formatting issues like extra text or code blocks.
    """
    # Clean the string by removing common non-JSON elements
    cleaned = categorie_scores_raw.strip()
    
    # Remove markdown code blocks if present
    if cleaned.startswith("```json") and cleaned.endswith("```"):
        cleaned = cleaned[7:-3].strip()
    elif cleaned.startswith("```") and cleaned.endswith("```"):
        cleaned = cleaned[3:-3].strip()
    
    # Extract JSON substring between curly braces
    start_idx = cleaned.find('{')
    end_idx = cleaned.rfind('}')
    
    if start_idx == -1 or end_idx == -1:
        return {}
    
    json_str = cleaned[start_idx:end_idx+1]
    
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        return {}


def parse_bullet_points(text: str) -> list[str]:
    """
    Parses bullet point text into a clean list of strings.
    Handles various bullet styles and cleans extra formatting.
    """
    lines = text.splitlines()
    bullet_points = []
    bullet_indicators = ('-', '*', '•', '→')
    
    for line in lines:
        stripped = line.strip()
        
        # Skip empty lines
        if not stripped:
            continue
            
        # Remove numeric prefixes (1., 2.) if present
        if stripped[:2].replace('.', '').isdigit():
            stripped = stripped[2:].lstrip()
        
        # Check for bullet indicators
        if any(stripped.startswith(indicator) for indicator in bullet_indicators):
            # Remove the bullet symbol and any following space
            content = stripped[1:].lstrip()
            bullet_points.append(content)
        else:
            # Capture lines without bullets if they're part of continuous text
            if bullet_points and not bullet_points[-1].endswith(('.', '!', '?')):
                bullet_points[-1] += " " + stripped
            else:
                bullet_points.append(stripped)
    
    # Remove any markdown formatting artifacts
    return [point.replace("**", "").replace("__", "") for point in bullet_points]
