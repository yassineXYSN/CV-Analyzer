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
from pydantic import BaseModel
import os
from dotenv import load_dotenv
import json
load_dotenv()
app = FastAPI()

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
    YASSINE CHTOUROU COMPUTER SCIENCE STUDENT CONTACT yassinechtourou03@gmail.com +00216993465 www.linkedin.com 22 rue karatchi ABOUT ME Born on 16 January 2005. Currently pursuing the BD (Big Data) program at the Higher Institute of Arts and Multimedia (ISAMM) to become a Big Data engineer. Thrives on challenges with a sociable and motivated personality. Passionate about programming with proficiency in multiple languages, committed to expanding skills in the evolving tech field. EDUCATION Computer Science Licence ISAMM 2023-2026 Baccalaureate Mouhamed Dachraoui 2020-2023 EXPERTISE Adaptability Teamwork Communication Creativity LANGUAGES Arabic English French German DIPLOMAS AND CERTIFICATES Certificate PHP Udemy Certificate PHP Certificate CSS and Java Udemy Certificate CSS and Java Baccalaureate Diploma Excellent Grade in Mathematics Baccalaureate Python Intermediate Certificate Sololearn Python Certificate German Language Level A1 Certificate ECL Tunisie Centre d´examen Allemand Microsoft Azure AI Fundamentals: AI Overview Microsoft Profile SKILLS SUMMARY CSS: 80% PHP: 80% Python: 75% C: 75% HTML: 60% Java: 60% HOBBIES 80% 75% 75% 60% 60%
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
    "name": "YASSINE CHTOUROU",
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
        pdf_text = data.get('pdf_text')
        """
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
        improvements = parse_bullet_points(improvements_raw)"""
        
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

def parse_category_scores(raw_text):
    """Parse category scores from raw text"""
    try:
        # Try to find JSON in the text
        json_match = re.search(r'\{[^}]*\}', raw_text)
        if json_match:
            json_str = json_match.group()
            return json.loads(json_str)
        else:
            # Fallback: create default scores
            return {
                "Work Experience": 75,
                "Skills & Technical Expertise": 80,
                "Education": 70,
                "Certifications & Training": 65,
                "Soft Skills & Leadership": 72,
                "Overall Structure & Presentation": 78
            }
    except Exception as e:
        print(f"Error parsing category scores: {e}")
        return {
            "Work Experience": 75,
            "Skills & Technical Expertise": 80,
            "Education": 70,
            "Certifications & Training": 65,
            "Soft Skills & Leadership": 72,
            "Overall Structure & Presentation": 78
        }

def parse_bullet_points(raw_text):
    """Parse bullet points from raw text"""
    try:
        # Split by lines and filter bullet points
        lines = raw_text.split('\n')
        bullet_points = []
        
        for line in lines:
            line = line.strip()
            # Remove bullet point markers
            if line.startswith('•') or line.startswith('-') or line.startswith('*'):
                bullet_points.append(line[1:].strip())
            elif line.startswith('- '):
                bullet_points.append(line[2:].strip())
            elif line and not line.startswith('#') and len(line) > 10:
                # If it's a substantial line without bullet markers, include it
                bullet_points.append(line)
        
        # Filter out empty or very short points
        bullet_points = [point for point in bullet_points if len(point) > 5]
        
        return bullet_points[:8]  # Limit to 8 points max
        
    except Exception as e:
        print(f"Error parsing bullet points: {e}")
        return ["Erreur lors de l'analyse des points"]
