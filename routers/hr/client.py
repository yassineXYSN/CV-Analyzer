from fastapi import APIRouter, Request, UploadFile, File, Form
from fastapi.responses import HTMLResponse
from insert_to_db import insert_candidate_data
import os
import json
import re
from database import SessionLocal
from models import ProfileCandidat

router = APIRouter()

@router.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("client-dep/index.html", {"request": request})

@router.get("/analyze", response_class=HTMLResponse)
def analyze_page(request: Request):
    return templates.TemplateResponse("client-dep/analyze.html", {"request": request})

@router.post("/scan", response_class=HTMLResponse)
async def scan_file(
    request: Request,
    filetoscan: UploadFile = File(...),
    selectedProfiles: str = Form(...)
):
    os.makedirs("uploads", exist_ok=True)
    file_location = f"uploads/{filetoscan.filename}"
    
    with open(file_location, "wb") as f:
        f.write(await filetoscan.read())

    # Données de test
    pdf_text = "Sample CV text..."
    summary = "Sample analysis..."
    score = 68.02
    
    data_json = {
        "certificates": ["Certificate PHP", "Python Certificate"],
        "contact": {
            "address": "22 rue karatchi",
            "email": "test@email.com",
            "linkedin": "www.linkedin.com",
            "phone": "123456789"
        },
        "education": [
            {
                "degree": "Computer Science",
                "institution": "University",
                "years": "2020-2024"
            }
        ],
        "languages": ["French", "English"],
        "name": "Test User",
        "profile": "Test profile description",
        "skills": ["Python: 80%", "JavaScript: 70%"],
        "title": "Developer",
        "yearsOfExperience": "2"
    }
    
    candidate_id = insert_candidate_data(data_json, summary)
    
    return templates.TemplateResponse("client-dep/result.html", {
        "request": request,
        "filename": filetoscan.filename,
        "pdf_text": pdf_text,
        "images_text": [],
        "summary": summary,
        "score": score,
        "user_info": data_json,
        "skills_titles": "Python, JavaScript",
        "candidate_id": candidate_id
    })