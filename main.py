import json
from fastapi import FastAPI, Request, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import extract_information_cv.text_extractor as text_extractor
import extract_information_cv.textcleaner as textcleaner
import extract_information_cv.data_generator as data_generator
from cv_analyzer.information_analyzer import compute_similarity
from cv_analyzer.description_generator import generate_job_description
from insert_to_db import insert_candidate_data
from pydantic import BaseModel
import os
from dotenv import load_dotenv
from database import engine
import models



import json
load_dotenv()
app = FastAPI()

# Création des tables
models.Base.metadata.create_all(bind=engine)

# Créer le dossier static s'il n'existe pas
os.makedirs("static", exist_ok=True)

# Monter les fichiers statiques CORRECTEMENT
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/analyze", response_class=HTMLResponse)
def analyze_page(request: Request):
    return templates.TemplateResponse("analyze.html", {"request": request})

@app.post("/scan", response_class=HTMLResponse)
async def scan_file(
    request: Request,
    filetoscan: UploadFile = File(...),
    job_description: str = Form(...)
):
    # Créer le dossier uploads s'il n'existe pas
    os.makedirs("uploads", exist_ok=True)
    
    file_location = f"uploads/{filetoscan.filename}"

    # Save file to disk temporarily
    with open(file_location, "wb") as f:
        f.write(await filetoscan.read())
    """
    # Process the file
    print("Extracting text from the file...")
    pdf_text, images_text = text_extractor.process_file(file_location)
    print("Text extraction completed.")

    # Clean up
    print("Cleaning up the extracted text...")
    pdf_text = textcleaner.cleantext(pdf_text)
    print("Cleaned up the extracted text.")
    # Generate summary
    print("Generating summary ...")
    summary = data_generator.generate_summary(pdf_text, images_text)
    print("Summary generation completed.")
    print("Generating structured data ...")
    data_json = data_generator.generate_json(pdf_text)
    print("Structured data generation completed.")

    # Compute matching score
    score = compute_similarity(summary, job_description)
    """

    # For demonstration purposes, using test data instead of actual processing
    pdf_text = """
    youssef CHTOUROU COMPUTER SCIENCE STUDENT CONTACT yassinechtourou03@gmail.com +00216993465 www.linkedin.com 22 rue karatchi ABOUT ME Born on 16 January 2005. Currently pursuing the BD (Big Data) program at the Higher Institute of Arts and Multimedia (ISAMM) to become a Big Data engineer. Thrives on challenges with a sociable and motivated personality. Passionate about programming with proficiency in multiple languages, committed to expanding skills in the evolving tech field. EDUCATION Computer Science Licence ISAMM 2023-2026 Baccalaureate Mouhamed Dachraoui 2020-2023 EXPERTISE Adaptability Teamwork Communication Creativity LANGUAGES Arabic English French German DIPLOMAS AND CERTIFICATES Certificate PHP Udemy Certificate PHP Certificate CSS and Java Udemy Certificate CSS and Java Baccalaureate Diploma Excellent Grade in Mathematics Baccalaureate Python Intermediate Certificate Sololearn Python Certificate German Language Level A1 Certificate ECL Tunisie Centre d´examen Allemand Microsoft Azure AI Fundamentals: AI Overview Microsoft Profile SKILLS SUMMARY CSS: 80% PHP: 80% Python: 75% C: 75% HTML: 60% Java: 60% HOBBIES 80% 75% 75% 60% 60%
    """
    images_text = ['', '', 'sam']

    summary = """Here is a critical summary based solely on the provided CV text: **The candidate is an undergraduate student currently pursuing a Big Data engineering program at ISAMM (2023-2026), having completed a Baccalaureate with an Excellent grade in Mathematics. Certificates in PHP, CSS, Java, and Python Intermediate level from Udemy/Sololearn indicate foundational technical skills, self-reported as proficient (CSS 80%, PHP 80%, Python 75%, C 75%, HTML 60%, Java 60%), along with a Microsoft Azure AI Fundamentals certificate demonstrating introductory AI knowledge. Soft skills claimed include Adaptability, Teamwork, Communication, and Creativity, and the candidate possesses multilingual capabilities (Arabic, English, French, German - with an A1 German certificate). Critical weaknesses include a complete absence of professional work experience, internships, relevant projects, or leadership roles listed. No specific big data tools, technologies, or frameworks relevant to the stated program goal are mentioned. The CV lacks concrete achievements or project examples validating skills, and the timeframe shows exclusively academic engagement with no practical application evidence. Job history, including dates and roles, is entirely absent."""

    score = 68.02

    data_json = {
    "certificates": [
        "Certificate PHP",
        "Udemy Certificate PHP",
        "Certificate CSS and Java",
        "Udemy Certificate CSS and Java",
        "Baccalaureate Diploma",
        "Excellent Grade in Mathematics Baccalaureate",
        "Python Intermediate Certificate",
        "Sololearn Python Certificate",
        "German Language Level A1 Certificate",
        "ECL Tunisie Centre d\u00b4examen Allemand",
        "Microsoft Azure AI Fundamentals: AI Overview",
        "Microsoft Profile"
    ],
    "contact": {
        "address": "22 rue karatchi",
        "email": "yassinechtourou03@gmail.com",
        "linkedin": "www.linkedin.com",
        "phone": "+00216993465"
    },
    "education": [
        {
        "degree": "Computer Science Licence",
        "institution": "ISAMM",
        "years": "2023-2026"
        },
        {
        "degree": "Baccalaureate",
        "institution": "Mouhamed Dachraoui",
        "years": "2020-2023"
        }
    ],
    "languages": [
        "Arabic",
        "English",
        "French",
        "German"
    ],
    "name": "youssef CHTOUROU",
    "profile": "Born on 16 January 2005. Currently pursuing the BD (Big Data) program at the Higher Institute of Arts and Multimedia (ISAMM) to become a Big Data engineer. Thrives on challenges with a sociable and motivated personality. Passionate about programming with proficiency in multiple languages, committed to expanding skills in the evolving tech field.",
    "skills": [
        "CSS: 80%",
        "PHP: 80%",
        "Python: 75%",
        "C: 75%",
        "HTML: 60%",
        "Java: 60%"
    ],
    "title": "COMPUTER SCIENCE STUDENT",
    "yearsOfExperience":"0"
    }
    skills_titles = [skill.split(":")[0] for skill in data_json["skills"]]
    skills_titles_str = ", ".join(skills_titles)



    # Juste avant le return :
    insert_candidate_data(data_json, summary)

    # Ensuite on affiche la page avec les résultats
    return templates.TemplateResponse("result.html", {
        "request": request,
        "filename": filetoscan.filename,
        "pdf_text": pdf_text,
        "images_text": images_text,
        "summary": summary,
        "score": score,
        "user_info": data_json,
        "job_description": job_description,
        "skills_titles": skills_titles_str,
})


class TopicRequest(BaseModel):
    topic: str

@app.post("/generate-description")
async def generate_description(request: TopicRequest):
    description = generate_job_description(request.topic)
    return {"description": description}

@app.post("/create-detailed-analysis")
async def create_detailed_analysis(request: Request):
    try:
        data = await request.json()
        filename = data.get('filename')
        summary = data.get('summary')
        pdf_text = data.get('pdf_text')
        score = data.get('score')
        
        # Simulate processing time (remove in production)
        import time
        import asyncio
        await asyncio.sleep(3)  # Simulate 3 seconds of processing
        
        # Initialize client for detailed analysis
        client = "textcleaner.intialize_client()"
        
        # Generate detailed recommendations based on score
        recommendations = "generate_detailed_recommendations(score, summary, client)"
        
        # Analyze skills
        skills_analysis = "analyze_skills(summary, pdf_text, client)"
        
        # Analyze keywords
        keyword_analysis = "analyze_keywords(summary, pdf_text)"
        
        return {
            "success": True,
            "recommendations": recommendations,
            "skills_analysis": skills_analysis,
            "keyword_analysis": keyword_analysis,
            "processing_time": "3.2s"
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}
    
    