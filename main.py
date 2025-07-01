import json
from fastapi import FastAPI, Request, UploadFile, File, Form, Query, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from models import get_jobs_with_pagination, get_job_by_id
import extract_information_cv.text_extractor as text_extractor
import extract_information_cv.textcleaner as textcleaner
import cv_analyzer.data_generator as data_generator
from cv_analyzer.information_analyzer import compute_similarity
from cv_analyzer.description_generator import generate_job_description
from insert_to_db import insert_candidate_data
from pydantic import BaseModel
import os
from dotenv import load_dotenv
from database import engine, SessionLocal
from typing import Optional
from models import Job, Company, Department
import models
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, or_, and_
import math
import re

load_dotenv()
app = FastAPI()

# Création des tables
models.Base.metadata.create_all(bind=engine)

# Créer le dossier static s'il n'existe pas
static_dir = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(static_dir, exist_ok=True)

# Vérifier que le fichier CSS existe
css_file = os.path.join(static_dir, "style.css")
if not os.path.exists(css_file):
    print(f"⚠️  ATTENTION: Le fichier CSS n'existe pas à {css_file}")
    print(f"📁 Dossier static: {static_dir}")
    print(f"📄 Fichiers dans static: {os.listdir(static_dir) if os.path.exists(static_dir) else 'Dossier inexistant'}")
else:
    print(f"✅ Fichier CSS trouvé: {css_file}")

# Monter les fichiers statiques
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Templates
templates_dir = os.path.join(os.path.dirname(__file__), "templates")
templates = Jinja2Templates(directory=templates_dir)

def parse_skills(skills_data):
    """Parse skills list to extract name and percentage"""
    if not skills_data:
        return []
    
    # Si c'est une string JSON, la parser
    if isinstance(skills_data, str):
        try:
            skills_list = json.loads(skills_data)
        except:
            return []
    else:
        skills_list = skills_data
    
    if not isinstance(skills_list, list):
        return []
    
    parsed_skills = []
    for skill in skills_list:
        try:
            skill_str = str(skill)
            if ':' in skill_str:
                parts = skill_str.split(':')
                name = parts[0].strip()
                level_str = parts[1].strip()
                # Extract percentage number
                percentage_match = re.search(r'(\d+)', level_str)
                percentage = int(percentage_match.group(1)) if percentage_match else 0
                parsed_skills.append({
                    'name': name,
                    'level_str': level_str,
                    'percentage': min(percentage, 100)  # Cap at 100%
                })
            else:
                parsed_skills.append({
                    'name': skill_str.strip(),
                    'level_str': '',
                    'percentage': 0
                })
        except Exception as e:
            print(f"Erreur parsing skill {skill}: {e}")
            parsed_skills.append({
                'name': str(skill),
                'level_str': '',
                'percentage': 0
            })
    return parsed_skills

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("client-dep/index.html", {"request": request})

@app.get("/analyze", response_class=HTMLResponse)
def analyze_page(request: Request):
    return templates.TemplateResponse("client-dep/analyze.html", {"request": request})

@app.post("/scan", response_class=HTMLResponse)
async def scan_file(
    request: Request,
    filetoscan: UploadFile = File(...),
    selectedProfiles: str = Form(...)
):
    # Créer le dossier uploads s'il n'existe pas
    os.makedirs("uploads", exist_ok=True)
    
    file_location = f"uploads/{filetoscan.filename}"
    print(selectedProfiles)

    # Save file to disk temporarily
    with open(file_location, "wb") as f:
        f.write(await filetoscan.read())

    # For demonstration purposes, using test data instead of actual processing
    pdf_text = """
    youssef CHTOUROU COMPUTER SCIENCE STUDENT CONTACT yassinechtourou03@gmail.com +00216993465 www.linkedin.com 22 rue karatchi ABOUT ME Born on 16 January 2005. Currently pursuing the BD (Big Data) program at the Higher Institute of Arts and Multimedia (ISAMM) to become a Big Data engineer. Thrives on challenges with a sociable and motivated personality. Passionate about programming with proficiency in multiple languages, committed to expanding skills in the evolving tech field. EDUCATION Computer Science Licence ISAMM 2023-2026 Baccalaureate Mouhamed Dachraoui 2020-2023 EXPERTISE Adaptability Teamwork Communication Creativity LANGUAGES Arabic English French German DIPLOMAS AND CERTIFICATES Certificate PHP Udemy Certificate PHP Certificate CSS and Java Udemy Certificate CSS and Java Baccalaureate Diploma Excellent Grade in Mathematics Baccalaureate Python Intermediate Certificate Sololearn Python Certificate German Language Level A1 Certificate ECL Tunisie Centre d´examen Allemand Microsoft Azure AI Fundamentals: AI Overview Microsoft Profile SKILLS SUMMARY CSS: 80% PHP: 80% Python: 75% C: 75% HTML: 60% Java: 60% HOBBIES 80% 75% 75% 60% 60%
    """
    images_text = ['', '', 'sam']

    summary = """Here is a critical summary based solely on the provided CV text: **The candidate is an undergraduate student currently pursuing a Big Data engineering program at ISAMM (2023-2026), having completed a Baccalaureate with an Excellent grade in Mathematics. Certificates in PHP, CSS, Java, and Python Intermediate level from Udemy/Sololearn indicate foundational technical skills, self-reported as proficient (CSS 80%, PHP 80%, Python 75%, C 75%, HTML 60%, Java 60%), along with a Microsoft Azure AI Fundamentals certificate demonstrating introductory AI knowledge. Soft skills claimed include Adaptability, Teamwork, Communication, and Creativity, and the candidate possesses multilingual capabilities (Arabic, English, French, German - with an A1 German certificate). Critical weaknesses include a complete absence of professional work experience, internships, relevant projects, or leadership roles listed. No specific big data tools, technologies, or frameworks relevant to the stated program goal are mentioned. The CV lacks concrete achievements or project examples validating skills, and the timeframe shows exclusively academic engagement with no practical application evidence. Job history, including dates and roles, is entirely absent.Here is a critical summary based solely on the provided CV text: **The candidate is an undergraduate student currently pursuing a Big Data engineering program at ISAMM (2023-2026), having completed a Baccalaureate with an Excellent grade in Mathematics. Certificates in PHP, CSS, Java, and Python Intermediate level from Udemy/Sololearn indicate foundational technical skills, self-reported as proficient (CSS 80%, PHP 80%, Python 75%, C 75%, HTML 60%, Java 60%), along with a Microsoft Azure AI Fundamentals certificate demonstrating introductory AI knowledge. Soft skills claimed include Adaptability, Teamwork, Communication, and Creativity, and the candidate possesses multilingual capabilities (Arabic, English, French, German - with an A1 German certificate). Critical weaknesses include a complete absence of professional work experience, internships, relevant projects, or leadership roles listed. No specific big data tools, technologies, or frameworks relevant to the stated program goal are mentioned. The CV lacks concrete achievements or project examples validating skills, and the timeframe shows exclusively academic engagement with no practical application evidence. Job history, including dates and roles, is entirely absent.Here is a critical summary based solely on the provided CV text: **The candidate is an undergraduate student currently pursuing a Big Data engineering program at ISAMM (2023-2026), having completed a Baccalaureate with an Excellent grade in Mathematics. Certificates in PHP, CSS, Java, and Python Intermediate level from Udemy/Sololearn indicate foundational technical skills, self-reported as proficient (CSS 80%, PHP 80%, Python 75%, C 75%, HTML 60%, Java 60%), along with a Microsoft Azure AI Fundamentals certificate demonstrating introductory AI knowledge. Soft skills claimed include Adaptability, Teamwork, Communication, and Creativity, and the candidate possesses multilingual capabilities (Arabic, English, French, German - with an A1 German certificate). Critical weaknesses include a complete absence of professional work experience, internships, relevant projects, or leadership roles listed. No specific big data tools, technologies, or frameworks relevant to the stated program goal are mentioned. The CV lacks concrete achievements or project examples validating skills, and the timeframe shows exclusively academic engagement with no practical application evidence. Job history, including dates and roles, is entirely absent.Here is a critical summary based solely on the provided CV text: **The candidate is an undergraduate student currently pursuing a Big Data engineering program at ISAMM (2023-2026), having completed a Baccalaureate with an Excellent grade in Mathematics. Certificates in PHP, CSS, Java, and Python Intermediate level from Udemy/Sololearn indicate foundational technical skills, self-reported as proficient (CSS 80%, PHP 80%, Python 75%, C 75%, HTML 60%, Java 60%), along with a Microsoft Azure AI Fundamentals certificate demonstrating introductory AI knowledge. Soft skills claimed include Adaptability, Teamwork, Communication, and Creativity, and the candidate possesses multilingual capabilities (Arabic, English, French, German - with an A1 German certificate). Critical weaknesses include a complete absence of professional work experience, internships, relevant projects, or leadership roles listed. No specific big data tools, technologies, or frameworks relevant to the stated program goal are mentioned. The CV lacks concrete achievements or project examples validating skills, and the timeframe shows exclusively academic engagement with no practical application evidence. Job history, including dates and roles, is entirely absent.Here is a critical summary based solely on the provided CV text: **The candidate is an undergraduate student currently pursuing a Big Data engineering program at ISAMM (2023-2026), having completed a Baccalaureate with an Excellent grade in Mathematics. Certificates in PHP, CSS, Java, and Python Intermediate level from Udemy/Sololearn indicate foundational technical skills, self-reported as proficient (CSS 80%, PHP 80%, Python 75%, C 75%, HTML 60%, Java 60%), along with a Microsoft Azure AI Fundamentals certificate demonstrating introductory AI knowledge. Soft skills claimed include Adaptability, Teamwork, Communication, and Creativity, and the candidate possesses multilingual capabilities (Arabic, English, French, German - with an A1 German certificate). Critical weaknesses include a complete absence of professional work experience, internships, relevant projects, or leadership roles listed. No specific big data tools, technologies, or frameworks relevant to the stated program goal are mentioned. The CV lacks concrete achievements or project examples validating skills, and the timeframe shows exclusively academic engagement with no practical application evidence. Job history, including dates and roles, is entirely absent."""

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
            "email": "ahbedhmid@gmail.com",
            "linkedin": "www.linkedin.com",
            "phone": "99896635"
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
        "name": "ahmed hamido",
        "profile": "Born on 16 January 2005. Currently pursuing the BD (Big Data) program at the Higher Institute of Arts and Multimedia (ISAMM) to become a Big Data engineer. Thrives on challenges with a sociable and motivated personality. Passionate about programming with proficiency in multiple languages, committed to expanding skills in the evolving tech field.",
        "skills": [
            "CSS: 80%",
            "PHP: 30%",
            "Python: 75%",
            "C: 75%",
            "HTML: 60%",
            "Java: 60%"
        ],
        "title": "COMPUTER SCIENCE STUDENT",
        "yearsOfExperience": "0"
    }
    skills_titles = [skill.split(":")[0] for skill in data_json["skills"]]
    skills_titles_str = ", ".join(skills_titles)

    # Insérer les données en base
    candidate_id = insert_candidate_data(data_json, summary)

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
        "candidate_id": candidate_id
    })

@app.get("/profile/{candidate_id}", response_class=HTMLResponse)
def profile_detail(request: Request, candidate_id: int):
    db = SessionLocal()
    try:
        # Récupérer les données du candidat depuis la base
        profile = db.query(models.ProfileCandidat).filter(models.ProfileCandidat.id == candidate_id).first()
        if not profile:
            print(f"Profile not found for ID: {candidate_id}")
            return templates.TemplateResponse("client-dep/profile_detail.html", {
                "request": request,
                "profile": None,
                "contact": None,
                "analyse": None,
                "parsed_skills": []
            })
        
        contact = db.query(models.Contact).filter(models.Contact.id == profile.contact_id).first()
        analyse = db.query(models.AnalyseCandidat).filter(models.AnalyseCandidat.id == profile.analyse_id).first()
        
        # Debug: afficher le type et contenu de profile.skills
        print(f"Profile skills type: {type(profile.skills)}")
        print(f"Profile skills content: {profile.skills}")
        
        # Parse skills to extract percentages
        parsed_skills = parse_skills(profile.skills)
        
        # Récupérer les valeurs des attributs d'abord
        education_value = getattr(profile, 'education', None)
        languages_value = getattr(profile, 'languages', None)
        certificates_value = getattr(profile, 'certificates', None)
        
        # Parse education if it's a JSON string
        parsed_education = []
        if education_value:
            try:
                if isinstance(education_value, str):
                    parsed_education = json.loads(education_value)
                else:
                    parsed_education = education_value
            except:
                parsed_education = []
        
        # Parse languages if it's a JSON string
        parsed_languages = []
        if languages_value:
            try:
                if isinstance(languages_value, str):
                    parsed_languages = json.loads(languages_value)
                else:
                    parsed_languages = languages_value
            except:
                parsed_languages = []
        
        # Parse certificates if it's a JSON string
        parsed_certificates = []
        if certificates_value:
            try:
                if isinstance(certificates_value, str):
                    parsed_certificates = json.loads(certificates_value)
                else:
                    parsed_certificates = certificates_value
            except:
                parsed_certificates = []
        
        # Create a simple object to hold profile data
        class ProfileData:
            def __init__(self, **kwargs):
                for key, value in kwargs.items():
                    setattr(self, key, value)

        profile_data = ProfileData(
            id=profile.id,
            name=profile.name,
            title=profile.title,
            profile=profile.profile,
            education=parsed_education,
            languages=parsed_languages,
            certificates=parsed_certificates,
            years_of_experience=getattr(profile, 'yearOfExperience', None),
            experience=getattr(profile, 'experience', None),
            projects=getattr(profile, 'projects', None),
            hobbies=getattr(profile, 'hobbies', None),
            references=getattr(profile, 'references', None),
            additional_info=getattr(profile, 'additional_info', None)
        )

        print(f"Profile found: {profile.name}")
        print(f"Parsed skills: {parsed_skills}")
        print(f"Parsed education: {parsed_education}")

        return templates.TemplateResponse("client-dep/profile_detail.html", {
            "request": request,
            "profile": profile_data,
            "contact": contact,
            "analyse": analyse,
            "parsed_skills": parsed_skills
        })
    except Exception as e:
        print(f"Erreur dans profile_detail: {e}")
        import traceback
        traceback.print_exc()
        return templates.TemplateResponse("client-dep/profile_detail.html", {
            "request": request,
            "profile": None,
            "contact": None,
            "analyse": None,
            "parsed_skills": []
        })
    finally:
        db.close()

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

@app.get("/login", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("client-dep/auth/login.html", {"request": request})

@app.get("/dashboard", response_class=HTMLResponse)
def home1(request: Request):
    return templates.TemplateResponse("HR-dep/dashboard-admin.html", {"request": request})

@app.get("/signup", response_class=HTMLResponse)
def home2(request: Request):
    return templates.TemplateResponse("client-dep/auth/signup.html", {"request": request})


@app.get("/hr-login", response_class=HTMLResponse)
def home3(request: Request):
    return templates.TemplateResponse("HR-dep/auth/hr-login.html", {"request": request})

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Pagination helper class
class Pagination:
    def __init__(self, page: int, per_page: int, total: int):
        self.current_page = page
        self.per_page = per_page
        self.total_jobs = total
        self.total_pages = math.ceil(total / per_page) if per_page > 0 else 0
        self.has_prev = page > 1
        self.has_next = page < self.total_pages
        self.prev_page = page - 1 if self.has_prev else None
        self.next_page = page + 1 if self.has_next else None

# Search parameters helper class
class SearchParams:
    def __init__(self, search: str = "", location: str = "", category: str = "", 
                 employment_type: str = "", salary_min: Optional[int] = None, 
                 salary_max: Optional[int] = None):
        self.search = search
        self.location = location
        self.category = category
        self.employment_type = employment_type
        self.salary_min = salary_min
        self.salary_max = salary_max

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("client-dep/index.html", {"request": request})

@app.get("/analyze", response_class=HTMLResponse)
async def analyze(request: Request):
    return templates.TemplateResponse("client-dep/analyze.html", {"request": request})

@app.get("/jobs", response_class=HTMLResponse)
async def jobs_page(
    request: Request,
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    search: str = Query(""),
    location: str = Query(""),
    category: str = Query(""),
    employment_type: str = Query(""),
    salary_min: Optional[int] = Query(None),
    salary_max: Optional[int] = Query(None),
    sort: str = Query("newest")
):
    per_page = 12
    
    # Build base query with all necessary joins
    query = db.query(Job).options(
        joinedload(Job.company),
        joinedload(Job.department)
    )
    
    # Join tables only once
    company_joined = False
    department_joined = False
    
    # Apply filters
    filters = [Job.status == 'active']
    
    # Search filter
    if search:
        if not company_joined:
            query = query.join(Company)
            company_joined = True
        
        search_filter = or_(
            Job.title.ilike(f"%{search}%"),
            Job.description.ilike(f"%{search}%"),
            Company.company_name.ilike(f"%{search}%")
        )
        filters.append(search_filter)
    
    # Location filter
    if location:
        if not company_joined:
            query = query.join(Company)
            company_joined = True
        
        filters.append(Company.address.ilike(f"%{location}%"))
    
    # Category filter
    if category:
        if not department_joined:
            query = query.join(Department)
            department_joined = True
        
        filters.append(Department.name.ilike(f"%{category}%"))
    
    # Employment type filter
    if employment_type:
        filters.append(Job.employment_type == employment_type)
    
    # Salary filters
    if salary_min:
        filters.append(Job.salary_min >= salary_min)
    
    if salary_max:
        filters.append(Job.salary_max <= salary_max)
    
    # Apply all filters
    query = query.filter(and_(*filters))
    
    # Apply sorting
    if sort == "newest":
        query = query.order_by(Job.created_at.desc())
    elif sort == "oldest":
        query = query.order_by(Job.created_at.asc())
    elif sort == "salary_high":
        query = query.order_by(Job.salary_max.desc().nullslast())
    elif sort == "salary_low":
        query = query.order_by(Job.salary_min.asc().nullslast())
    
    # Get total count
    total_jobs = query.count()
    
    # Apply pagination
    offset = (page - 1) * per_page
    jobs = query.offset(offset).limit(per_page).all()
    
    # Create pagination object
    pagination = Pagination(page, per_page, total_jobs)
    
    # Create search params object
    search_params = SearchParams(search, location, category, employment_type, salary_min, salary_max)
    
    return templates.TemplateResponse("client-dep/jobs.html", {
        "request": request,
        "jobs": jobs,
        "pagination": pagination,
        "search_params": search_params
    })

@app.get("/jobs/{job_id}", response_class=HTMLResponse)
async def job_detail(request: Request, job_id: int, db: Session = Depends(get_db)):
    job = db.query(Job).options(
        joinedload(Job.company),
        joinedload(Job.department)
    ).filter(Job.id == job_id).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Increment view count
    job.views_count += 1
    db.commit()
    
    return templates.TemplateResponse("client-dep/job_detail.html", {
        "request": request,
        "job": job
    })

@app.get("/profile", response_class=HTMLResponse)
async def profile(request: Request):
    return templates.TemplateResponse("client-dep/profile_detail.html", {"request": request})

@app.get("/result", response_class=HTMLResponse)
async def result(request: Request):
    return templates.TemplateResponse("client-dep/result.html", {"request": request})

@app.get("/auth/login", response_class=HTMLResponse)
async def login(request: Request):
    return templates.TemplateResponse("client-dep/auth/login.html", {"request": request})

@app.get("/auth/signup", response_class=HTMLResponse)
async def signup(request: Request):
    return templates.TemplateResponse("client-dep/auth/client-signup.html", {"request": request})

# API endpoints for job interactions
@app.post("/api/jobs/{job_id}/save")
async def save_job(job_id: int, db: Session = Depends(get_db)):
    """Save job to user's favorites"""
    # This would typically save to a user's saved jobs
    # For now, just return success
    return {"success": True, "message": "Offre ajoutée aux favoris"}

@app.delete("/api/jobs/{job_id}/save")
async def unsave_job(job_id: int, db: Session = Depends(get_db)):
    """Remove job from user's favorites"""
    # This would typically remove from user's saved jobs
    # For now, just return success
    return {"success": True, "message": "Offre retirée des favoris"}

@app.post("/api/jobs/{job_id}/apply")
async def apply_to_job(job_id: int, db: Session = Depends(get_db)):
    """Submit job application"""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Increment application count
    job.applications_count = (job.applications_count or 0) + 1
    db.commit()
    
    return {"success": True, "message": "Candidature envoyée avec succès!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
