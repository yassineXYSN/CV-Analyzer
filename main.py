import json
from fastapi import FastAPI, Request, UploadFile, File, Form, Query, Depends, HTTPException, Cookie, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
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
from models import Job, Company, Department, Application, ProfileCandidat, User, UserSession
import models
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, or_, and_
import math
import re
from auth import (
    authenticate_user, create_user, hash_password, create_user_session, 
    get_user_from_session, delete_user_session
)

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

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(request: Request, db: Session = Depends(get_db)) -> Optional[User]:
    """Get current user from session"""
    session_token = request.cookies.get("session_token")
    if not session_token:
        return None
    return get_user_from_session(db, session_token)

def require_auth(request: Request, db: Session = Depends(get_db)) -> User:
    """Require authentication, raise 401 if not authenticated"""
    user = get_current_user(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user

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
def home(request: Request, db: Session = Depends(get_db)):
    current_user = get_current_user(request, db)
    return templates.TemplateResponse("client-dep/index.html", {
        "request": request,
        "current_user": current_user
    })

@app.get("/analyze", response_class=HTMLResponse)
def analyze_page(request: Request, db: Session = Depends(get_db)):
    current_user = get_current_user(request, db)
    return templates.TemplateResponse("client-dep/analyze.html", {
        "request": request,
        "current_user": current_user
    })

@app.post("/scan", response_class=HTMLResponse)
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

@app.get("/profile/{candidate_id}", response_class=HTMLResponse)
def profile_detail(request: Request, candidate_id: int, db: Session = Depends(get_db)):
    current_user = get_current_user(request, db)
    
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
                "parsed_skills": [],
                "current_user": current_user
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
            years_of_experience=profile.yearOfExperience,
            profile_picture=profile.profile_picture,
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
            "parsed_skills": parsed_skills,
            "current_user": current_user
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
            "parsed_skills": [],
            "current_user": current_user
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

# Authentication routes
@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request, db: Session = Depends(get_db)):
    current_user = get_current_user(request, db)
    if current_user:
        return RedirectResponse(url="/", status_code=302)
    return templates.TemplateResponse("client-dep/auth/login.html", {"request": request})

@app.post("/login")
async def login(
    request: Request,
    response: Response,
    email: str = Form(...),
    password: str = Form(...),
    remember_me: bool = Form(False),
    db: Session = Depends(get_db)
):
    try:
        user = authenticate_user(db, email, password)
        if not user:
            return {"success": False, "message": "Email ou mot de passe incorrect"}
        
        if not user.is_active:
            return {"success": False, "message": "Compte désactivé"}
        
        # Create session
        session_token = create_user_session(db, user.id, remember_me)
        
        # Set cookie
        max_age = 30 * 24 * 60 * 60 if remember_me else 24 * 60 * 60  # 30 days or 1 day
        response.set_cookie(
            key="session_token",
            value=session_token,
            max_age=max_age,
            httponly=True,
            secure=False,  # Set to True in production with HTTPS
            samesite="lax"
        )
        
        return {"success": True, "message": "Connexion réussie"}
        
    except Exception as e:
        print(f"Login error: {str(e)}")
        return {"success": False, "message": "Erreur lors de la connexion"}

@app.get("/signup", response_class=HTMLResponse)
def signup_page(request: Request, db: Session = Depends(get_db)):
    current_user = get_current_user(request, db)
    if current_user:
        return RedirectResponse(url="/", status_code=302)
    return templates.TemplateResponse("client-dep/auth/signup.html", {"request": request})

@app.post("/signup")
async def signup(
    request: Request,
    response: Response,  # Add response parameter
    first_name: str = Form(...),
    last_name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
    db: Session = Depends(get_db)
):
    try:
        # Validation
        if password != confirm_password:
            return {"success": False, "message": "Les mots de passe ne correspondent pas"}
        
        if len(password) < 8:
            return {"success": False, "message": "Le mot de passe doit contenir au moins 8 caractères"}
        
        # Check if user exists
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            return {"success": False, "message": "Un compte avec cet email existe déjà"}
        
        # Create user
        # Create user
        user = create_user(db, email, password, first_name, last_name)
        
        # Automatically log in the user
        session_token = create_user_session(db, user.id, remember_me=False)
        
        # Set session cookie
        response.set_cookie(
            key="session_token",
            value=session_token,
            max_age=24 * 60 * 60,  # 1 day
            httponly=True,
            secure=False,  # Set to True in production with HTTPS
            samesite="lax"
        )
        
        return {"success": True, "redirect_url": "/signup/step2"}
        
    except Exception as e:
        print(f"Signup error: {str(e)}")
        return {"success": False, "message": "Erreur lors de la création du compte"}
    
# Add new signup step routes
@app.get("/signup/step2", response_class=HTMLResponse)
def signup_step2_page(request: Request, db: Session = Depends(get_db)):
    current_user = get_current_user(request, db)
    if not current_user:
        return RedirectResponse(url="/login", status_code=302)
    return templates.TemplateResponse("client-dep/auth/signup-step2.html", {
        "request": request,
        "current_user": current_user
    })

@app.post("/signup/step2")
async def signup_step2(
    request: Request,
    response: Response,
    filetoscan: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    current_user = get_current_user(request, db)
    if not current_user:
        return {"success": False, "message": "Authentication required"}

        current_user = get_current_user(request, db)
    
    # Créer le dossier uploads s'il n'existe pas
    os.makedirs("uploads", exist_ok=True)
    
    file_location = f"uploads/{filetoscan.filename}"

    # Save file to disk temporarily
    with open(file_location, "wb") as f:
        f.write(await filetoscan.read())

    # For demonstration purposes, using test data instead of actual processing
    pdf_text = """
    youssef CHTOUROU COMPUTER SCIENCE STUDENT CONTACT yassinechtourou03@gmail.com +00216993465 www.linkedin.com 22 rue karatchi ABOUT ME Born on 16 January 2005. Currently pursuing the BD (Big Data) program at the Higher Institute of Arts and Multimedia (ISAMM) to become a Big Data engineer. Thrives on challenges with a sociable and motivated personality. Passionate about programming with proficiency in multiple languages, committed to expanding skills in the evolving tech field. EDUCATION Computer Science Licence ISAMM 2023-2026 Baccalaureate Mouhamed Dachraoui 2020-2023 EXPERTISE Adaptability Teamwork Communication Creativity LANGUAGES Arabic English French German DIPLOMAS AND CERTIFICATES Certificate PHP Udemy Certificate PHP Certificate CSS and Java Udemy Certificate CSS and Java Baccalaureate Diploma Excellent Grade in Mathematics Baccalaureate Python Intermediate Certificate Sololearn Python Certificate German Language Level A1 Certificate ECL Tunisie Centre d´examen Allemand Microsoft Azure AI Fundamentals: AI Overview Microsoft Profile SKILLS SUMMARY CSS: 80% PHP: 80% Python: 75% C: 75% HTML: 60% Java: 60% HOBBIES 80% 75% 75% 60% 60%
    """
    images_text = ['', '', 'sam']

    summary = """Here is a critical summary based solely on the provided CV text: **The candidate is an undergraduate student currently pursuing a Big Data engineering program at ISAMM (2023-2026), having completed a Baccalaureate with an Excellent grade in Mathematics. Certificates in PHP, CSS, Java, and Python Intermediate level from Udemy/Sololearn indicate foundational technical skills, self-reported as proficient (CSS 80%, PHP 80%, Python 75%, C 75%, HTML 60%, Java 60%), along with a Microsoft Azure AI Fundamentals certificate demonstrating introductory AI knowledge. Soft skills claimed include Adaptability, Teamwork, Communication, and Creativity, and the candidate possesses multilingual capabilities (Arabic, English, French, German - with an A1 German certificate). Critical weaknesses include a complete absence of professional work experience, internships, relevant projects, or leadership roles listed. No specific big data tools, technologies, or frameworks relevant to the stated program goal are mentioned. The CV lacks concrete achievements or project examples validating skills, and the timeframe shows exclusively academic engagement with no practical application evidence. Job history, including dates and roles, is entirely absent."""

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
        "yearsOfExperience": "0",
        "profilePic": "/static/client-dep/images/placeholder.svg"
    }
    skills_titles = [skill.split(":")[0] for skill in data_json["skills"]]
    skills_titles_str = ", ".join(skills_titles)

    # Insérer les données en base et lier au user si connecté
    candidate_id = insert_candidate_data(data_json, summary, current_user.id)

    # Redirect to profile detail page
    return RedirectResponse(url=f"/profile/{candidate_id}", status_code=303)

@app.post("/profile/{candidate_id}/upload-picture")
async def upload_profile_picture(
    candidate_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_auth)
):
    # Check if the candidate profile belongs to the current user
    profile = db.query(models.ProfileCandidat).filter(
        models.ProfileCandidat.id == candidate_id,
        models.ProfileCandidat.user_id == current_user.id
    ).first()
    
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    # Create upload directory if not exists
    os.makedirs("static/uploads/profile_pictures", exist_ok=True)
    
    # Generate unique filename
    file_ext = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = f"static/uploads/profile_pictures/{unique_filename}"
    
    # Save the file
    with open(file_path, "wb") as f:
        f.write(await file.read())
    
    # Update profile in database
    profile.profile_picture = f"/{file_path}"  # Store relative path
    db.commit()
    
    return {"success": True, "profile_picture": profile.profile_picture}

@app.post("/logout")
async def logout(request: Request, response: Response, db: Session = Depends(get_db)):
    session_token = request.cookies.get("session_token")
    if session_token:
        delete_user_session(db, session_token)
    
    response.delete_cookie("session_token")
    return templates.TemplateResponse("client-dep/index.html", {
        "request": request,
        "current_user": None
    })

@app.get("/api/auth/status")
async def auth_status(request: Request, db: Session = Depends(get_db)):
    """Check current authentication status"""
    try:
        current_user = get_current_user(request, db)
        if current_user:
            return {
                "authenticated": True,
                "user": {
                    "id": current_user.id,
                    "email": current_user.email,
                    "first_name": current_user.first_name,
                    "last_name": current_user.last_name,
                    "name": f"{current_user.first_name} {current_user.last_name}".strip(),
                    "is_active": current_user.is_active
                }
            }
        else:
            return {"authenticated": False}
    except Exception as e:
        print(f"Auth status error: {str(e)}")
        return {"authenticated": False}

@app.get("/components/header.html", response_class=HTMLResponse)
async def get_header_component(request: Request):
    """Serve the header component"""
    try:
        with open("components/header.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(content="<div>Header component not found</div>", status_code=404)

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

@app.get("/jobs", response_class=HTMLResponse)
async def jobs_page(
    request: Request,
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    search: str = Query(""),
    location: str = Query(""),
    category: str = Query(""),
    employment_type: str = Query(""),
    salary_min: Optional[str] = Query(None),
    salary_max: Optional[str] = Query(None),
    sort: str = Query("newest")
):
    current_user = get_current_user(request, db)
    
    # Convert salary strings to integers, handling empty strings
    salary_min_int = None
    salary_max_int = None

    if salary_min and salary_min.strip():
        try:
            salary_min_int = int(salary_min)
        except ValueError:
            salary_min_int = None

    if salary_max and salary_max.strip():
        try:
            salary_max_int = int(salary_max)
        except ValueError:
            salary_max_int = None

    print(f"Salary filters - Min: {salary_min_int}, Max: {salary_max_int}")
    
    per_page = 12
    
    # Build base query with eager loading
    query = db.query(Job).options(
        joinedload(Job.company),
        joinedload(Job.department)
    )
    
    # Always join Company and Department for flexible searching
    query = query.join(Company, Job.company_id == Company.id, isouter=True)
    query = query.join(Department, Job.department_id == Department.id, isouter=True)
    
    # Apply filters - only add filters that have values
    filters = [Job.status == 'active']
    
    # Search filter - search across multiple fields with flexible matching
    if search and search.strip():
        search_term = f"%{search.strip()}%"
        search_filter = or_(
            Job.title.ilike(search_term),
            Job.description.ilike(search_term),
            Job.requirements.ilike(search_term),
            Company.company_name.ilike(search_term),
            Department.name.ilike(search_term),
            # Also search in job tags if they exist
            Job.tags.ilike(search_term) if hasattr(Job, 'tags') else False
        )
        filters.append(search_filter)
    
    # Location filter - flexible location matching
    if location and location.strip():
        location_term = f"%{location.strip()}%"
        location_filter = or_(
            Company.address.ilike(location_term),
            Job.location.ilike(location_term) if hasattr(Job, 'location') else False
        )
        filters.append(location_filter)
    
    # Category filter - flexible category matching
    if category and category.strip():
        category_term = f"%{category.strip()}%"
        category_filter = or_(
            Department.name.ilike(category_term),
            Job.title.ilike(category_term),
            Job.description.ilike(category_term),
            Job.tags.ilike(category_term) if hasattr(Job, 'tags') else False
        )
        filters.append(category_filter)
    
    # Employment type filter - flexible matching
    if employment_type and employment_type.strip():
        if employment_type.lower() != 'all':
            employment_filter = or_(
                Job.employment_type.ilike(f"%{employment_type}%"),
                Job.employment_type == employment_type
            )
            filters.append(employment_filter)
    
    # Improved salary filters
    if salary_min_int and salary_min_int > 0:
        # User wants jobs that pay at least salary_min_int
        # Include jobs where the maximum salary meets the minimum requirement
        # OR where minimum salary meets the requirement (if max is null)
        salary_min_filter = or_(
            and_(Job.salary_max.isnot(None), Job.salary_max >= salary_min_int),
            and_(Job.salary_max.is_(None), Job.salary_min >= salary_min_int),
            # Also include jobs where salary_min >= user's minimum (they definitely meet the requirement)
            Job.salary_min >= salary_min_int
        )
        filters.append(salary_min_filter)
        print(f"Applied minimum salary filter: >= {salary_min_int}")

    if salary_max_int and salary_max_int > 0:
        # User wants jobs within their budget (salary_max_int)
        # Include jobs where the minimum salary is within budget
        # OR where maximum salary is within budget (if min is null)
        salary_max_filter = or_(
            and_(Job.salary_min.isnot(None), Job.salary_min <= salary_max_int),
            and_(Job.salary_min.is_(None), Job.salary_max <= salary_max_int),
            # Also include jobs where salary_max <= user's maximum (they're definitely within budget)
            Job.salary_max <= salary_max_int
        )
        filters.append(salary_max_filter)
        print(f"Applied maximum salary filter: <= {salary_max_int}")
    
    # Apply all filters
    if filters:
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
    elif sort == "relevance" and search:
        # For relevance, prioritize title matches, then company, then description
        query = query.order_by(
            Job.title.ilike(f"%{search}%").desc(),
            Company.company_name.ilike(f"%{search}%").desc(),
            Job.created_at.desc()
        )
    else:
        # Default to newest
        query = query.order_by(Job.created_at.desc())
    
    # Get total count
    total_jobs = query.count()
    print(f"Total jobs found: {total_jobs}")
    
    # Apply pagination
    offset = (page - 1) * per_page
    jobs = query.offset(offset).limit(per_page).all()
    
    # Debug: print some job salary info
    for job in jobs[:3]:  # Just first 3 jobs
        print(f"Job: {job.title}, Salary: {job.salary_min}-{job.salary_max}")
    
    # Create pagination object
    pagination = Pagination(page, per_page, total_jobs)
    
    # Create search params object
    search_params = SearchParams(search, location, category, employment_type, salary_min_int, salary_max_int)
    
    # Get all departments for category dropdown - make it more flexible
    try:
        departments = db.query(Department.name).filter(Department.name.isnot(None)).distinct().all()
        categories = [dept[0] for dept in departments if dept[0]]
        
        # Add some common categories if none exist
        if not categories:
            categories = [
                "Développement", "Marketing", "Design", "Finance", 
                "Ressources Humaines", "Ventes", "Support Client"
            ]
    except:
        categories = [
            "Développement", "Marketing", "Design", "Finance", 
            "Ressources Humaines", "Ventes", "Support Client"
        ]
    
    return templates.TemplateResponse("client-dep/jobs.html", {
        "request": request,
        "jobs": jobs,
        "pagination": pagination,
        "search_params": search_params,
        "sort": sort,
        "categories": categories,
        "total_jobs": total_jobs,
        "current_user": current_user
    })

@app.get("/jobs/{job_id}", response_class=HTMLResponse)
async def job_detail(request: Request, job_id: int, db: Session = Depends(get_db)):
    current_user = get_current_user(request, db)
    
    job = db.query(Job).options(
        joinedload(Job.company),
        joinedload(Job.department)
    ).filter(Job.id == job_id).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Increment view count
    job.views_count = (job.views_count or 0) + 1
    db.commit()
    
    # Check if user has applied
    has_applied = False
    if current_user:
        # Get the candidate profile for the current user
        candidate_profile = db.query(ProfileCandidat).filter(
            ProfileCandidat.user_id == current_user.id
        ).first()

        if candidate_profile:
            application = db.query(Application).filter(
                and_(
                    Application.job_id == job_id,
                    Application.candidate_profile_id == candidate_profile.id
                )
            ).first()
            has_applied = application is not None

    return templates.TemplateResponse("client-dep/job_detail.html", {
        "request": request,
        "job": job,
        "current_user": current_user,
        "has_applied": has_applied
    })

# API endpoints for job interactions
@app.post("/api/jobs/{job_id}/save")
async def save_job(job_id: int, request: Request, db: Session = Depends(get_db)):
    """Save job to user's favorites"""
    current_user = get_current_user(request, db)
    if not current_user:
        return {"success": False, "message": "Vous devez être connecté pour sauvegarder une offre"}
    
    # This would typically save to a user's saved jobs table
    # For now, just return success
    return {"success": True, "message": "Offre ajoutée aux favoris"}

@app.delete("/api/jobs/{job_id}/save")
async def unsave_job(job_id: int, request: Request, db: Session = Depends(get_db)):
    """Remove job from user's favorites"""
    current_user = get_current_user(request, db)
    if not current_user:
        return {"success": False, "message": "Vous devez être connecté"}
    
    # This would typically remove from user's saved jobs
    # For now, just return success
    return {"success": True, "message": "Offre retirée des favoris"}

class ApplicationRequest(BaseModel):
    message: Optional[str] = None

@app.post("/api/jobs/{job_id}/apply")
async def apply_to_job(job_id: int, application_data: ApplicationRequest, request: Request, db: Session = Depends(get_db)):
    """Submit job application - requires authentication"""
    try:
        # Require authentication
        current_user = get_current_user(request, db)
        if not current_user:
            return {"success": False, "message": "Vous devez être connecté pour postuler à une offre"}
        
        # Check if job exists
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Get user's candidate profile
        candidate_profile = db.query(ProfileCandidat).filter(ProfileCandidat.user_id == current_user.id).first()
        if not candidate_profile:
            return {"success": False, "message": "Vous devez d'abord analyser votre CV pour créer votre profil candidat"}
        
        # Check if application already exists
        existing_application = db.query(Application).filter(
            and_(Application.job_id == job_id, Application.user_id == current_user.id)
        ).first()
        
        if existing_application:
            return {"success": False, "message": "Vous avez déjà postulé à cette offre"}
        
        # Create new application
        new_application = Application(
            job_id=job_id,
            candidate_profile_id=candidate_profile.id,
            user_id=current_user.id,
            status='pending',
            source='job_portal'
        )
        
        db.add(new_application)
        
        # Increment application count for the job
        job.applications_count = (job.applications_count or 0) + 1
        
        db.commit()
        
        print(f"Application created: Job {job_id}, User {current_user.id}, Candidate {candidate_profile.id}")
        
        return {
            "success": True, 
            "message": f"Candidature envoyée avec succès pour le poste '{job.title}'!",
            "application_id": new_application.id
        }
        
    except Exception as e:
        db.rollback()
        print(f"Error applying to job: {str(e)}")
        return {"success": False, "message": "Erreur lors de l'envoi de la candidature"}

@app.get("/api/jobs/{job_id}/application-status")
async def check_application_status(job_id: int, request: Request, db: Session = Depends(get_db)):
    """Check if user has already applied to this job"""
    try:
        current_user = get_current_user(request, db)
        if not current_user:
            return {"has_applied": False}
        
        application = db.query(Application).filter(
            and_(Application.job_id == job_id, Application.user_id == current_user.id)
        ).first()
        
        if application:
            return {
                "has_applied": True,
                "application_date": application.application_date.isoformat(),
                "status": application.status
            }
        else:
            return {"has_applied": False}
            
    except Exception as e:
        print(f"Error checking application status: {str(e)}")
        return {"has_applied": False}

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard_page(request: Request, db: Session = Depends(get_db)):
    current_user = get_current_user(request, db)
    if not current_user:
        return RedirectResponse(url="/login", status_code=302)
    
    # Get user's applications
    applications = db.query(Application).options(
        joinedload(Application.job).joinedload(Job.company),
        joinedload(Application.job).joinedload(Job.department)
    ).filter(Application.user_id == current_user.id).order_by(Application.created_at.desc()).all()
    
    return templates.TemplateResponse("client-dep/dashboard.html", {
        "request": request,
        "current_user": current_user,
        "applications": applications
    })

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
