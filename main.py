import json
from fastapi import FastAPI, Request, UploadFile, File, Form, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
import extract_information_cv.text_extractor as text_extractor
import extract_information_cv.textcleaner as textcleaner
import cv_analyzer.data_generator as data_generator
from cv_analyzer.information_analyzer import compute_similarity
from cv_analyzer.description_generator import generate_job_description
from insert_to_db import insert_candidate_data
from auth_utils import authenticate_user, create_admin_user
from company_utils import create_company, update_company, get_user_company, get_company_admins, add_user_to_company
from pydantic import BaseModel
from typing import Optional
import os
from dotenv import load_dotenv
from database import engine, SessionLocal
import models
import re
from datetime import datetime, date

load_dotenv()
app = FastAPI()

# Création des tables
models.Base.metadata.create_all(bind=engine)

# Créer le dossier static s'il n'existe pas
static_dir = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(static_dir, exist_ok=True)

# Monter les fichiers statiques
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Templates
templates_dir = os.path.join(os.path.dirname(__file__), "templates")
templates = Jinja2Templates(directory=templates_dir)

# Modèles pour l'API
class LoginRequest(BaseModel):
    email: str
    password: str

class LoginResponse(BaseModel):
    success: bool
    message: str
    redirect_url: Optional[str] = None
    user: Optional[dict] = None

class CompanySetupRequest(BaseModel):
    company_name: str
    industry: str
    company_size: str
    founded_year: Optional[int] = None
    description: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    linkedin_url: Optional[str] = None
    twitter_url: Optional[str] = None
    facebook_url: Optional[str] = None

class CreateUserRequest(BaseModel):
    email: str
    password: str
    first_name: str
    last_name: str
    role: str = "hr_admin"
    company_id: Optional[int] = None
    access_level: str = "admin"

class DepartmentRequest(BaseModel):
    name: str
    description: Optional[str] = ""
    manager_name: Optional[str] = ""
    color: str = "#e74c3c"
    budget: Optional[float] = 0.0

class EmployeeRequest(BaseModel):
    first_name: str
    last_name: str
    email: str
    department_id: int
    position: str
    phone: Optional[str] = ""
    hire_date: Optional[str] = None
    salary: Optional[float] = None
    employment_type: str = "CDI"
    employee_id: Optional[str] = ""

class JobRequest(BaseModel):
    title: str
    department_id: int
    description: str
    employment_type: str
    priority: str = "normal"
    deadline: Optional[str] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    requirements: Optional[str] = ""
    responsibilities: Optional[str] = ""
    assigned_employee_id: Optional[int] = None

# Session utilisateur simple (en production, utilisez JWT ou sessions sécurisées)
current_user_session = {}

def parse_skills(skills_data):
    """Parse skills list to extract name and percentage"""
    if not skills_data:
        return []
    
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
                percentage_match = re.search(r'(\d+)', level_str)
                percentage = int(percentage_match.group(1)) if percentage_match else 0
                parsed_skills.append({
                    'name': name,
                    'level_str': level_str,
                    'percentage': min(percentage, 100)
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
    # Code existant pour le scan...
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

@app.get("/profile/{candidate_id}", response_class=HTMLResponse)
def profile_detail(request: Request, candidate_id: int):
    db = SessionLocal()
    try:
        profile = db.query(models.ProfileCandidat).filter(models.ProfileCandidat.id == candidate_id).first()
        if not profile:
            return templates.TemplateResponse("client-dep/profile_detail.html", {
                "request": request,
                "profile": None,
                "contact": None,
                "analyse": None,
                "parsed_skills": []
            })
        
        contact = db.query(models.Contact).filter(models.Contact.id == profile.contact_id).first()
        analyse = db.query(models.AnalyseCandidat).filter(models.AnalyseCandidat.id == profile.analyse_id).first()
        parsed_skills = parse_skills(profile.skills)
        
        # Parse JSON fields
        education_value = getattr(profile, 'education', None)
        languages_value = getattr(profile, 'languages', None)
        certificates_value = getattr(profile, 'certificates', None)
        
        parsed_education = []
        if education_value:
            try:
                parsed_education = json.loads(education_value) if isinstance(education_value, str) else education_value
            except:
                parsed_education = []
        
        parsed_languages = []
        if languages_value:
            try:
                parsed_languages = json.loads(languages_value) if isinstance(languages_value, str) else languages_value
            except:
                parsed_languages = []
        
        parsed_certificates = []
        if certificates_value:
            try:
                parsed_certificates = json.loads(certificates_value) if isinstance(certificates_value, str) else certificates_value
            except:
                parsed_certificates = []
        
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
            certificates=parsed_certificates
        )

        return templates.TemplateResponse("client-dep/profile_detail.html", {
            "request": request,
            "profile": profile_data,
            "contact": contact,
            "analyse": analyse,
            "parsed_skills": parsed_skills
        })
    except Exception as e:
        print(f"Erreur dans profile_detail: {e}")
        return templates.TemplateResponse("client-dep/profile_detail.html", {
            "request": request,
            "profile": None,
            "contact": None,
            "analyse": None,
            "parsed_skills": []
        })
    finally:
        db.close()

# Routes pour les pages
@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("client-dep/auth/client-login.html", {"request": request})

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard_page(request: Request):
    return templates.TemplateResponse("HR-dep/hr-dashboard.html", {"request": request})

@app.get("/hr-login", response_class=HTMLResponse)
def hr_login_page(request: Request):
    return templates.TemplateResponse("HR-dep/auth/hr-login.html", {"request": request})

@app.get("/company-setup", response_class=HTMLResponse)
def company_setup_page(request: Request):
    return templates.TemplateResponse("HR-dep/company-setup.html", {"request": request})

@app.get("/company-profile", response_class=HTMLResponse)
def company_profile_page(request: Request):
    try:
        print("🏢 PAGE: Chargement company-profile")
        
        # Récupérer l'utilisateur actuel
        user_id = current_user_session.get('user_id')
        print(f"👤 PAGE: User ID de session: {user_id}")
        
        if not user_id:
            print("❌ PAGE: Utilisateur non connecté, redirection vers login")
            return templates.TemplateResponse("HR-dep/auth/hr-login.html", {"request": request})
        
        # Récupérer l'entreprise de l'utilisateur
        company = get_user_company(user_id)
        print(f"🏢 PAGE: Entreprise trouvée: {company.company_name if company else 'Aucune'}")
        
        company_admins = []
        if company:
            company_admins = get_company_admins(company.id)
            print(f"👥 PAGE: {len(company_admins)} admins trouvés")
        
        return templates.TemplateResponse("HR-dep/company-profile.html", {
            "request": request,
            "company": company,
            "company_admins": company_admins
        })
        
    except Exception as e:
        print(f"❌ PAGE: Erreur dans company_profile_page: {e}")
        import traceback
        traceback.print_exc()
        return templates.TemplateResponse("HR-dep/auth/hr-login.html", {"request": request})

@app.get("/employee-profile", response_class=HTMLResponse)
def employee_profile_page(request: Request):
    return templates.TemplateResponse("HR-dep/employee-profile.html", {"request": request})

@app.get("/job-details", response_class=HTMLResponse)
def job_details_page(request: Request):
    return templates.TemplateResponse("HR-dep/job-details.html", {"request": request})

# API Routes
@app.post("/api/hr-login")
async def hr_login(login_data: LoginRequest):
    """API pour la connexion HR"""
    try:
        print(f"🔐 LOGIN API: Tentative de connexion pour {login_data.email}")
        
        # Authentifier l'utilisateur
        user = authenticate_user(login_data.email, login_data.password)
        
        if not user:
            print(f"❌ LOGIN API: Authentification échouée")
            return LoginResponse(
                success=False,
                message="Email ou mot de passe incorrect"
            )
        
        print(f"✅ LOGIN API: Utilisateur authentifié - ID: {user['id']}")
        
        # Sauvegarder la session utilisateur
        current_user_session['user_id'] = user['id']
        current_user_session['email'] = user['email']
        print(f"✅ LOGIN API: Session sauvegardée")
        
        # Mettre à jour la dernière connexion
        db = SessionLocal()
        try:
            db_user = db.query(models.HRAdmin).filter(models.HRAdmin.email == login_data.email).first()
            if db_user:
                db_user.last_login = datetime.now()
                db.commit()
        except Exception as e:
            print(f"⚠️ LOGIN API: Erreur mise à jour last_login: {e}")
        finally:
            db.close()
        
        # Vérifier le statut de l'entreprise
        company = get_user_company(user['id'])
        
        if not company:
            redirect_url = "/company-setup"
            message = "Configuration de l'entreprise requise"
        elif not company.setup_completed:
            redirect_url = "/company-setup"
            message = "Finalisation de la configuration requise"
        else:
            redirect_url = "/dashboard"
            message = "Connexion réussie"
        
        print(f"🎯 LOGIN API: Redirection vers {redirect_url}")
        
        return LoginResponse(
            success=True,
            message=message,
            redirect_url=redirect_url,
            user=user
        )
        
    except Exception as e:
        print(f"❌ LOGIN API: Erreur critique: {e}")
        import traceback
        traceback.print_exc()
        return LoginResponse(
            success=False,
            message="Erreur interne du serveur"
        )

@app.post("/api/company-setup")
async def setup_company(company_data: CompanySetupRequest):
    """API pour configurer l'entreprise"""
    try:
        print(f"🏢 SETUP API: Début configuration entreprise")
        
        # Vérifier la session utilisateur
        user_id = current_user_session.get('user_id')
        if not user_id:
            print(f"❌ SETUP API: Utilisateur non connecté")
            return {"success": False, "message": "Utilisateur non connecté"}
        
        print(f"✅ SETUP API: User connecté - ID: {user_id}")
        
        # Vérifier si l'utilisateur a déjà une entreprise
        existing_company = get_user_company(user_id)
        company_dict = company_data.dict()
        
        if existing_company:
            print(f"📝 SETUP API: Mise à jour entreprise existante ID: {existing_company.id}")
            success = update_company(existing_company.id, company_dict)
            action = "mise à jour"
        else:
            print(f"➕ SETUP API: Création nouvelle entreprise")
            company_id = create_company(user_id, company_dict)
            success = company_id is not None
            action = "création"
        
        if success:
            print(f"✅ SETUP API: {action.capitalize()} réussie")
            return {
                "success": True,
                "message": f"Entreprise {action} avec succès",
                "redirect_url": "/dashboard"
            }
        else:
            print(f"❌ SETUP API: Erreur lors de la {action}")
            return {
                "success": False,
                "message": f"Erreur lors de la {action} de l'entreprise"
            }
        
    except Exception as e:
        print(f"❌ SETUP API: Erreur critique: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "message": "Erreur interne du serveur"}

@app.post("/api/create-department")
async def create_department(department_data: DepartmentRequest):
    """API pour créer un nouveau département"""
    try:
        print(f"🏢 DEPT API: Début création département")
        print(f"📋 DEPT API: Données reçues: {department_data.dict()}")
        
        # Vérifier la session utilisateur
        user_id = current_user_session.get('user_id')
        if not user_id:
            print(f"❌ DEPT API: Utilisateur non connecté")
            return {"success": False, "message": "Utilisateur non connecté"}
        
        print(f"✅ DEPT API: User connecté - ID: {user_id}")
        
        # Récupérer l'entreprise de l'utilisateur
        company = get_user_company(user_id)
        if not company:
            print(f"❌ DEPT API: Aucune entreprise trouvée")
            return {"success": False, "message": "Aucune entreprise associée"}
        
        print(f"✅ DEPT API: Entreprise trouvée - ID: {company.id}")
        
        # Créer le département en base
        db = SessionLocal()
        try:
            # Vérifier si un département avec le même nom existe déjà
            existing_dept = db.query(models.Department).filter(
                models.Department.company_id == company.id,
                models.Department.name == department_data.name,
                models.Department.is_active == True
            ).first()
            
            if existing_dept:
                print(f"❌ DEPT API: Département '{department_data.name}' existe déjà")
                return {"success": False, "message": f"Un département nommé '{department_data.name}' existe déjà"}
            
            # Traiter les valeurs pour éviter les null
            description = department_data.description if department_data.description else ""
            manager_name = department_data.manager_name if department_data.manager_name else ""
            budget = department_data.budget if department_data.budget is not None else 0.0

            new_department = models.Department(
                company_id=company.id,
                name=department_data.name,
                description=description,
                manager_name=manager_name,
                color=department_data.color,
                budget=budget,
                is_active=True
            )
            
            db.add(new_department)
            db.commit()
            db.refresh(new_department)
            
            print(f"✅ DEPT API: Département créé avec ID: {new_department.id}")
            
            # Enregistrer l'activité
            try:
                log_activity(
                    company_id=company.id,
                    admin_id=user_id,
                    action_type='create',
                    entity_type='department',
                    entity_id=new_department.id,
                    description=f"Création du département '{department_data.name}'",
                    details={"department_name": department_data.name, "manager": department_data.manager_name}
                )
                print(f"✅ DEPT API: Activité enregistrée pour département {new_department.id}")
            except Exception as e:
                print(f"⚠️ DEPT API: Erreur enregistrement activité: {e}")
            
            # Retourner les données du département créé
            department_info = {
                "id": new_department.id,
                "name": new_department.name,
                "description": new_department.description,
                "manager_name": new_department.manager_name,
                "color": new_department.color,
                "budget": float(new_department.budget) if new_department.budget else None,
                "is_active": new_department.is_active,
                "employee_count": 0,
                "job_count": 0,
                "created_at": new_department.created_at.isoformat() if new_department.created_at else None
            }
            
            return {
                "success": True,
                "message": f"Département '{department_data.name}' créé avec succès",
                "department": department_info
            }
            
        except Exception as e:
            db.rollback()
            print(f"❌ DEPT API: Erreur création département: {e}")
            import traceback
            traceback.print_exc()
            return {"success": False, "message": f"Erreur lors de la création du département: {str(e)}"}
        finally:
            db.close()
        
    except Exception as e:
        print(f"❌ DEPT API: Erreur critique: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "message": f"Erreur interne du serveur: {str(e)}"}

@app.get("/api/departments")
async def get_departments():
    """API pour récupérer les départements de l'entreprise"""
    try:
        print(f"🔍 DEPT LIST API: Récupération départements")
        
        # Vérifier la session utilisateur
        user_id = current_user_session.get('user_id')
        if not user_id:
            print(f"❌ DEPT LIST API: Utilisateur non connecté")
            return {"success": False, "message": "Utilisateur non connecté"}
        
        # Récupérer l'entreprise de l'utilisateur
        company = get_user_company(user_id)
        if not company:
            print(f"❌ DEPT LIST API: Aucune entreprise trouvée")
            return {"success": False, "message": "Aucune entreprise associée"}
        
        # Récupérer les départements
        db = SessionLocal()
        try:
            departments = db.query(models.Department).filter(
                models.Department.company_id == company.id,
                models.Department.is_active == True
            ).all()
            
            departments_list = []
            for dept in departments:
                # Compter les employés et postes si les tables existent
                employee_count = 0
                job_count = 0
                
                try:
                    employee_count = db.query(models.Employee).filter(
                        models.Employee.department_id == dept.id,
                        models.Employee.status == 'active'
                    ).count()
                except:
                    pass
                
                try:
                    job_count = db.query(models.Job).filter(
                        models.Job.department_id == dept.id,
                        models.Job.status.in_(['draft', 'active'])
                    ).count()
                except:
                    pass
                
                departments_list.append({
                    "id": dept.id,
                    "name": dept.name,
                    "description": dept.description,
                    "manager_name": dept.manager_name,
                    "color": dept.color,
                    "budget": float(dept.budget) if dept.budget else None,
                    "employee_count": employee_count,
                    "job_count": job_count,
                    "is_active": dept.is_active,
                    "created_at": dept.created_at.isoformat() if dept.created_at else None
                })
            
            print(f"✅ DEPT LIST API: {len(departments_list)} départements trouvés")
            
            return {
                "success": True,
                "departments": departments_list
            }
            
        except Exception as e:
            print(f"❌ DEPT LIST API: Erreur récupération départements: {e}")
            import traceback
            traceback.print_exc()
            return {"success": False, "message": f"Erreur lors de la récupération des départements: {str(e)}"}
        finally:
            db.close()
        
    except Exception as e:
        print(f"❌ DEPT LIST API: Erreur critique: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "message": f"Erreur interne du serveur: {str(e)}"}

@app.post("/api/create-employee")
async def create_employee(employee_data: EmployeeRequest):
    """API pour créer un nouvel employé"""
    try:
        print(f"👤 EMP API: Début création employé")
        print(f"📋 EMP API: Données reçues: {employee_data.dict()}")
        
        # Vérifier la session utilisateur
        user_id = current_user_session.get('user_id')
        if not user_id:
            print(f"❌ EMP API: Utilisateur non connecté")
            return {"success": False, "message": "Utilisateur non connecté"}
        
        # Récupérer l'entreprise de l'utilisateur
        company = get_user_company(user_id)
        if not company:
            print(f"❌ EMP API: Aucune entreprise trouvée")
            return {"success": False, "message": "Aucune entreprise associée"}
        
        print(f"✅ EMP API: Entreprise trouvée - ID: {company.id}")
        
        # Créer l'employé en base
        db = SessionLocal()
        try:
            # Vérifier si un employé avec le même email existe déjà
            existing_employee = db.query(models.Employee).filter(
                models.Employee.company_id == company.id,
                models.Employee.email == employee_data.email
            ).first()
            
            if existing_employee:
                print(f"❌ EMP API: Employé avec email '{employee_data.email}' existe déjà")
                return {"success": False, "message": f"Un employé avec l'email '{employee_data.email}' existe déjà"}
            
            # Vérifier que le département existe
            department = db.query(models.Department).filter(
                models.Department.id == employee_data.department_id,
                models.Department.company_id == company.id,
                models.Department.is_active == True
            ).first()
            
            if not department:
                print(f"❌ EMP API: Département {employee_data.department_id} non trouvé")
                return {"success": False, "message": "Département non trouvé"}
            
            # Traiter la date d'embauche
            hire_date_obj = None
            if employee_data.hire_date:
                try:
                    hire_date_obj = datetime.strptime(employee_data.hire_date, "%Y-%m-%d").date()
                except ValueError:
                    print(f"⚠️ EMP API: Format de date invalide: {employee_data.hire_date}")
            
            # Générer un ID employé si non fourni
            employee_id = employee_data.employee_id if employee_data.employee_id else f"EMP{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            new_employee = models.Employee(
                company_id=company.id,
                department_id=employee_data.department_id,
                employee_id=employee_id,
                first_name=employee_data.first_name,
                last_name=employee_data.last_name,
                email=employee_data.email,
                phone=employee_data.phone if employee_data.phone else None,
                position=employee_data.position,
                hire_date=hire_date_obj,
                salary=employee_data.salary,
                employment_type=employee_data.employment_type,
                status='active'
            )
            
            db.add(new_employee)
            db.commit()
            db.refresh(new_employee)
            
            print(f"✅ EMP API: Employé créé avec ID: {new_employee.id}")
            
            # Enregistrer l'activité
            try:
                log_activity(
                    company_id=company.id,
                    admin_id=user_id,
                    action_type='create',
                    entity_type='employee',
                    entity_id=new_employee.id,
                    description=f"Ajout de l'employé '{employee_data.first_name} {employee_data.last_name}'",
                    details={"employee_name": f"{employee_data.first_name} {employee_data.last_name}", "position": employee_data.position, "department": department.name}
                )
                print(f"✅ EMP API: Activité enregistrée pour employé {new_employee.id}")
            except Exception as e:
                print(f"⚠️ EMP API: Erreur enregistrement activité: {e}")
            
            # Retourner les données de l'employé créé
            employee_info = {
                "id": new_employee.id,
                "employee_id": new_employee.employee_id,
                "first_name": new_employee.first_name,
                "last_name": new_employee.last_name,
                "email": new_employee.email,
                "phone": new_employee.phone,
                "position": new_employee.position,
                "department_id": new_employee.department_id,
                "department_name": department.name,
                "hire_date": new_employee.hire_date.isoformat() if new_employee.hire_date else None,
                "salary": float(new_employee.salary) if new_employee.salary else None,
                "employment_type": new_employee.employment_type,
                "status": new_employee.status,
                "created_at": new_employee.created_at.isoformat() if new_employee.created_at else None
            }
            
            return {
                "success": True,
                "message": f"Employé '{employee_data.first_name} {employee_data.last_name}' créé avec succès",
                "employee": employee_info
            }
            
        except Exception as e:
            db.rollback()
            print(f"❌ EMP API: Erreur création employé: {e}")
            import traceback
            traceback.print_exc()
            return {"success": False, "message": f"Erreur lors de la création de l'employé: {str(e)}"}
        finally:
            db.close()
        
    except Exception as e:
        print(f"❌ EMP API: Erreur critique: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "message": f"Erreur interne du serveur: {str(e)}"}

@app.post("/api/create-job")
async def create_job(job_data: JobRequest):
    """API pour créer un nouveau poste"""
    try:
        print(f"💼 JOB API: Début création poste")
        print(f"📋 JOB API: Données reçues: {job_data.dict()}")
        
        # Vérifier la session utilisateur
        user_id = current_user_session.get('user_id')
        if not user_id:
            print(f"❌ JOB API: Utilisateur non connecté")
            return {"success": False, "message": "Utilisateur non connecté"}
        
        # Récupérer l'entreprise de l'utilisateur
        company = get_user_company(user_id)
        if not company:
            print(f"❌ JOB API: Aucune entreprise trouvée")
            return {"success": False, "message": "Aucune entreprise associée"}
        
        print(f"✅ JOB API: Entreprise trouvée - ID: {company.id}")
        
        # Créer le poste en base
        db = SessionLocal()
        try:
            # Vérifier que le département existe
            department = db.query(models.Department).filter(
                models.Department.id == job_data.department_id,
                models.Department.company_id == company.id,
                models.Department.is_active == True
            ).first()
            
            if not department:
                print(f"❌ JOB API: Département {job_data.department_id} non trouvé")
                return {"success": False, "message": "Département non trouvé"}
            
            # Traiter la date limite
            deadline_obj = None
            if job_data.deadline:
                try:
                    deadline_obj = datetime.strptime(job_data.deadline, "%Y-%m-%d").date()
                except ValueError:
                    print(f"⚠️ JOB API: Format de date invalide: {job_data.deadline}")
            
            # Vérifier l'employé assigné si spécifié
            assigned_employee = None
            if job_data.assigned_employee_id:
                assigned_employee = db.query(models.Employee).filter(
                    models.Employee.id == job_data.assigned_employee_id,
                    models.Employee.company_id == company.id,
                    models.Employee.status == 'active'
                ).first()
                
                if not assigned_employee:
                    print(f"⚠️ JOB API: Employé assigné {job_data.assigned_employee_id} non trouvé")
                    job_data.assigned_employee_id = None
            
            new_job = models.Job(
                company_id=company.id,
                department_id=job_data.department_id,
                title=job_data.title,
                description=job_data.description,
                requirements=job_data.requirements if job_data.requirements else "",
                responsibilities=job_data.responsibilities if job_data.responsibilities else "",
                employment_type=job_data.employment_type,
                salary_min=job_data.salary_min,
                salary_max=job_data.salary_max,
                currency='EUR',
                priority=job_data.priority,
                status='active',
                assigned_employee_id=job_data.assigned_employee_id,
                deadline=deadline_obj,
                views_count=0,
                applications_count=0
            )
            
            db.add(new_job)
            db.commit()
            db.refresh(new_job)
            
            print(f"✅ JOB API: Poste créé avec ID: {new_job.id}")
            
            # Enregistrer l'activité
            try:
                log_activity(
                    company_id=company.id,
                    admin_id=user_id,
                    action_type='create',
                    entity_type='job',
                    entity_id=new_job.id,
                    description=f"Création du poste '{job_data.title}'",
                    details={"job_title": job_data.title, "department": department.name, "priority": job_data.priority}
                )
                print(f"✅ JOB API: Activité enregistrée pour poste {new_job.id}")
            except Exception as e:
                print(f"⚠️ JOB API: Erreur enregistrement activité: {e}")
            
            # Retourner les données du poste créé
            job_info = {
                "id": new_job.id,
                "title": new_job.title,
                "description": new_job.description,
                "requirements": new_job.requirements,
                "responsibilities": new_job.responsibilities,
                "employment_type": new_job.employment_type,
                "salary_min": float(new_job.salary_min) if new_job.salary_min else None,
                "salary_max": float(new_job.salary_max) if new_job.salary_max else None,
                "currency": new_job.currency,
                "priority": new_job.priority,
                "status": new_job.status,
                "department_id": new_job.department_id,
                "department_name": department.name,
                "assigned_employee_id": new_job.assigned_employee_id,
                "assigned_employee_name": f"{assigned_employee.first_name} {assigned_employee.last_name}" if assigned_employee else None,
                "deadline": new_job.deadline.isoformat() if new_job.deadline else None,
                "views_count": new_job.views_count,
                "applications_count": new_job.applications_count,
                "created_at": new_job.created_at.isoformat() if new_job.created_at else None
            }
            
            return {
                "success": True,
                "message": f"Poste '{job_data.title}' créé avec succès",
                "job": job_info
            }
            
        except Exception as e:
            db.rollback()
            print(f"❌ JOB API: Erreur création poste: {e}")
            import traceback
            traceback.print_exc()
            return {"success": False, "message": f"Erreur lors de la création du poste: {str(e)}"}
        finally:
            db.close()
        
    except Exception as e:
        print(f"❌ JOB API: Erreur critique: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "message": f"Erreur interne du serveur: {str(e)}"}

@app.get("/api/employees")
async def get_employees():
    """API pour récupérer les employés de l'entreprise"""
    try:
        print(f"🔍 EMP LIST API: Récupération employés")
        
        # Vérifier la session utilisateur
        user_id = current_user_session.get('user_id')
        if not user_id:
            return {"success": False, "message": "Utilisateur non connecté"}
        
        # Récupérer l'entreprise de l'utilisateur
        company = get_user_company(user_id)
        if not company:
            return {"success": False, "message": "Aucune entreprise associée"}
        
        # Récupérer les employés
        db = SessionLocal()
        try:
            employees = db.query(models.Employee).filter(
                models.Employee.company_id == company.id,
                models.Employee.status == 'active'
            ).all()
            
            employees_list = []
            for emp in employees:
                # Récupérer le département
                department = db.query(models.Department).filter(
                    models.Department.id == emp.department_id
                ).first()
                
                employees_list.append({
                    "id": emp.id,
                    "employee_id": emp.employee_id,
                    "first_name": emp.first_name,
                    "last_name": emp.last_name,
                    "email": emp.email,
                    "phone": emp.phone,
                    "position": emp.position,
                    "department_id": emp.department_id,
                    "department_name": department.name if department else "N/A",
                    "hire_date": emp.hire_date.isoformat() if emp.hire_date else None,
                    "salary": float(emp.salary) if emp.salary else None,
                    "employment_type": emp.employment_type,
                    "status": emp.status,
                    "created_at": emp.created_at.isoformat() if emp.created_at else None
                })
            
            print(f"✅ EMP LIST API: {len(employees_list)} employés trouvés")
            
            return {
                "success": True,
                "employees": employees_list
            }
            
        except Exception as e:
            print(f"❌ EMP LIST API: Erreur récupération employés: {e}")
            return {"success": False, "message": f"Erreur lors de la récupération des employés: {str(e)}"}
        finally:
            db.close()
        
    except Exception as e:
        print(f"❌ EMP LIST API: Erreur critique: {e}")
        return {"success": False, "message": f"Erreur interne du serveur: {str(e)}"}

@app.get("/api/jobs")
async def get_jobs():
    """API pour récupérer les postes de l'entreprise"""
    try:
        print(f"🔍 JOB LIST API: Récupération postes")
        
        # Vérifier la session utilisateur
        user_id = current_user_session.get('user_id')
        if not user_id:
            return {"success": False, "message": "Utilisateur non connecté"}
        
        # Récupérer l'entreprise de l'utilisateur
        company = get_user_company(user_id)
        if not company:
            return {"success": False, "message": "Aucune entreprise associée"}
        
        # Récupérer les postes
        db = SessionLocal()
        try:
            jobs = db.query(models.Job).filter(
                models.Job.company_id == company.id,
                models.Job.status.in_(['draft', 'active', 'paused'])
            ).all()
            
            jobs_list = []
            for job in jobs:
                # Récupérer le département
                department = db.query(models.Department).filter(
                    models.Department.id == job.department_id
                ).first()
                
                # Récupérer l'employé assigné
                assigned_employee = None
                if job.assigned_employee_id:
                    assigned_employee = db.query(models.Employee).filter(
                        models.Employee.id == job.assigned_employee_id
                    ).first()
                
                jobs_list.append({
                    "id": job.id,
                    "title": job.title,
                    "description": job.description,
                    "requirements": job.requirements,
                    "responsibilities": job.responsibilities,
                    "employment_type": job.employment_type,
                    "salary_min": float(job.salary_min) if job.salary_min else None,
                    "salary_max": float(job.salary_max) if job.salary_max else None,
                    "currency": job.currency,
                    "priority": job.priority,
                    "status": job.status,
                    "department_id": job.department_id,
                    "department_name": department.name if department else "N/A",
                    "assigned_employee_id": job.assigned_employee_id,
                    "assigned_employee_name": f"{assigned_employee.first_name} {assigned_employee.last_name}" if assigned_employee else None,
                    "deadline": job.deadline.isoformat() if job.deadline else None,
                    "views_count": job.views_count,
                    "applications_count": job.applications_count,
                    "created_at": job.created_at.isoformat() if job.created_at else None
                })
            
            print(f"✅ JOB LIST API: {len(jobs_list)} postes trouvés")
            
            return {
                "success": True,
                "jobs": jobs_list
            }
            
        except Exception as e:
            print(f"❌ JOB LIST API: Erreur récupération postes: {e}")
            return {"success": False, "message": f"Erreur lors de la récupération des postes: {str(e)}"}
        finally:
            db.close()
        
    except Exception as e:
        print(f"❌ JOB LIST API: Erreur critique: {e}")
        return {"success": False, "message": f"Erreur interne du serveur: {str(e)}"}

@app.post("/api/create-user")
async def create_user(user_data: CreateUserRequest):
    """API pour créer un nouvel utilisateur"""
    try:
        current_user_id = current_user_session.get('user_id')
        if not current_user_id:
            return {"success": False, "message": "Utilisateur non connecté"}
        
        print(f"👤 USER API: Création utilisateur: {user_data.email}")
        
        # Créer l'utilisateur
        new_user_id = create_admin_user(
            email=user_data.email,
            password=user_data.password,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            role=user_data.role
        )
        
        if not new_user_id:
            return {"success": False, "message": "Erreur lors de la création de l'utilisateur"}
        
        # Si une entreprise est spécifiée, ajouter l'utilisateur à l'entreprise
        if user_data.company_id:
            success, message = add_user_to_company(
                company_id=user_data.company_id,
                admin_id=new_user_id,
                access_level=user_data.access_level,
                granted_by=current_user_id
            )
            
            if not success:
                return {"success": False, "message": f"Utilisateur créé mais erreur d'ajout à l'entreprise: {message}"}
        
        return {
            "success": True,
            "message": f"Utilisateur {user_data.email} créé avec succès",
            "user_id": new_user_id
        }
        
    except Exception as e:
        print(f"❌ USER API: Erreur création utilisateur: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "message": "Erreur interne du serveur"}

@app.get("/api/company-info")
async def get_company_info():
    """API pour récupérer les informations de l'entreprise"""
    try:
        user_id = current_user_session.get('user_id')
        if not user_id:
            return {"success": False, "message": "Utilisateur non connecté"}
        
        company = get_user_company(user_id)
        
        if not company:
            return {"success": False, "message": "Aucune entreprise trouvée"}
        
        company_data = {
            "id": company.id,
            "company_name": company.company_name,
            "industry": company.industry,
            "company_size": company.company_size,
            "founded_year": company.founded_year,
            "description": company.description,
            "address": company.address,
            "phone": company.phone,
            "email": company.email,
            "website": company.website,
            "linkedin_url": company.linkedin_url,
            "twitter_url": company.twitter_url,
            "facebook_url": company.facebook_url,
            "logo_url": company.logo_url,
            "setup_completed": company.setup_completed,
            "created_at": company.created_at.isoformat() if company.created_at else None,
            "updated_at": company.updated_at.isoformat() if company.updated_at else None
        }
        
        return {"success": True, "company": company_data}
        
    except Exception as e:
        print(f"❌ COMPANY INFO API: Erreur récupération entreprise: {e}")
        return {"success": False, "message": "Erreur interne du serveur"}

@app.get("/api/company-users")
async def get_company_users():
    """API pour récupérer les utilisateurs de l'entreprise"""
    try:
        user_id = current_user_session.get('user_id')
        if not user_id:
            return {"success": False, "message": "Utilisateur non connecté"}
        
        company = get_user_company(user_id)
        
        if not company:
            return {"success": False, "message": "Aucune entreprise trouvée"}
        
        admins = get_company_admins(company.id)
        
        return {"success": True, "users": admins}
        
    except Exception as e:
        print(f"❌ COMPANY USERS API: Erreur récupération utilisateurs: {e}")
        return {"success": False, "message": "Erreur interne du serveur"}

@app.get("/api/current-user")
async def get_current_user():
    """API pour récupérer les informations de l'utilisateur connecté"""
    try:
        user_id = current_user_session.get('user_id')
        if not user_id:
            return {"success": False, "message": "Utilisateur non connecté"}
        
        db = SessionLocal()
        try:
            user = db.query(models.HRAdmin).filter(models.HRAdmin.id == user_id).first()
            if not user:
                return {"success": False, "message": "Utilisateur non trouvé"}
            
            user_data = {
                "id": user.id,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "role": user.role,
                "is_active": user.is_active,
                "last_login": user.last_login.isoformat() if user.last_login else None,
                "created_at": user.created_at.isoformat() if user.created_at else None
            }
            
            return {"success": True, "user": user_data}
            
        except Exception as e:
            print(f"❌ USER INFO API: Erreur récupération utilisateur: {e}")
            return {"success": False, "message": f"Erreur lors de la récupération de l'utilisateur: {str(e)}"}
        finally:
            db.close()
        
    except Exception as e:
        print(f"❌ USER INFO API: Erreur critique: {e}")
        return {"success": False, "message": f"Erreur interne du serveur: {str(e)}"}

@app.get("/api/dashboard-stats")
async def get_dashboard_stats():
    """API pour récupérer les statistiques du dashboard"""
    try:
        user_id = current_user_session.get('user_id')
        if not user_id:
            return {"success": False, "message": "Utilisateur non connecté"}
        
        # Récupérer l'entreprise de l'utilisateur
        company = get_user_company(user_id)
        if not company:
            return {"success": False, "message": "Aucune entreprise associée"}
        
        db = SessionLocal()
        try:
            # Compter les départements actifs
            total_departments = db.query(models.Department).filter(
                models.Department.company_id == company.id,
                models.Department.is_active == True
            ).count()
            
            # Compter les employés actifs
            total_employees = db.query(models.Employee).filter(
                models.Employee.company_id == company.id,
                models.Employee.status == 'active'
            ).count()
            
            # Compter les postes ouverts
            total_jobs = db.query(models.Job).filter(
                models.Job.company_id == company.id,
                models.Job.status.in_(['draft', 'active'])
            ).count()
            
            # Compter les postes urgents
            urgent_jobs = db.query(models.Job).filter(
                models.Job.company_id == company.id,
                models.Job.status.in_(['draft', 'active']),
                models.Job.priority == 'urgent'
            ).count()
            
            # Compter les candidatures (si la table existe)
            total_applications = 0
            try:
                total_applications = db.query(models.Application).join(
                    models.Job, models.Application.job_id == models.Job.id
                ).filter(
                    models.Job.company_id == company.id,
                    models.Application.status.in_(['pending', 'reviewed'])
                ).count()
            except:
                pass
            
            # Calculer les pourcentages de changement (simulation pour le moment)
            dept_change = "+12%" if total_departments > 0 else "0%"
            job_change = "+8%" if total_jobs > 0 else "0%"
            emp_change = "+15%" if total_employees > 0 else "0%"
            
            stats = {
                "total_departments": total_departments,
                "total_employees": total_employees,
                "total_jobs": total_jobs,
                "urgent_jobs": urgent_jobs,
                "total_applications": total_applications,
                "dept_change": dept_change,
                "job_change": job_change,
                "emp_change": emp_change
            }
            
            print(f"✅ STATS API: Statistiques calculées: {stats}")
            
            return {"success": True, "stats": stats}
            
        except Exception as e:
            print(f"❌ STATS API: Erreur calcul statistiques: {e}")
            import traceback
            traceback.print_exc()
            return {"success": False, "message": f"Erreur lors du calcul des statistiques: {str(e)}"}
        finally:
            db.close()
        
    except Exception as e:
        print(f"❌ STATS API: Erreur critique: {e}")
        return {"success": False, "message": f"Erreur interne du serveur: {str(e)}"}

@app.get("/api/recent-activity")
async def get_recent_activity():
    """API pour récupérer l'activité récente"""
    try:
        print(f"🔍 ACTIVITY API: Début récupération activité récente")
        
        user_id = current_user_session.get('user_id')
        if not user_id:
            print(f"❌ ACTIVITY API: Utilisateur non connecté")
            return {"success": False, "message": "Utilisateur non connecté"}
        
        print(f"✅ ACTIVITY API: User ID: {user_id}")
        
        # Récupérer l'entreprise de l'utilisateur
        company = get_user_company(user_id)
        if not company:
            print(f"❌ ACTIVITY API: Aucune entreprise trouvée")
            return {"success": False, "message": "Aucune entreprise associée"}
        
        print(f"✅ ACTIVITY API: Company ID: {company.id}")
        
        db = SessionLocal()
        try:
            # Compter d'abord le nombre total d'activités
            total_activities = db.query(models.ActivityLog).filter(
                models.ActivityLog.company_id == company.id
            ).count()
            
            print(f"📊 ACTIVITY API: {total_activities} activités totales trouvées")
            
            # Récupérer les 10 dernières activités
            activities = db.query(models.ActivityLog).filter(
                models.ActivityLog.company_id == company.id
            ).order_by(models.ActivityLog.created_at.desc()).limit(10).all()
            
            print(f"📋 ACTIVITY API: {len(activities)} activités récupérées")
            
            activities_list = []
            for activity in activities:
                print(f"🔍 ACTIVITY API: Traitement activité ID {activity.id}")
                
                # Récupérer l'admin qui a fait l'action
                admin = None
                admin_name = "Utilisateur inconnu"
                
                if activity.admin_id:
                    admin = db.query(models.HRAdmin).filter(
                        models.HRAdmin.id == activity.admin_id
                    ).first()
                    
                    if admin:
                        admin_name = f"{admin.first_name} {admin.last_name}"
                        print(f"👤 ACTIVITY API: Admin trouvé: {admin_name}")
                    else:
                        print(f"⚠️ ACTIVITY API: Admin ID {activity.admin_id} non trouvé")
                
                activity_data = {
                    "id": activity.id,
                    "action_type": activity.action_type,
                    "entity_type": activity.entity_type,
                    "entity_id": activity.entity_id,
                    "description": activity.description,
                    "admin_name": admin_name,
                    "created_at": activity.created_at.isoformat() if activity.created_at else None,
                    "details": activity.details
                }
                
                activities_list.append(activity_data)
                print(f"✅ ACTIVITY API: Activité ajoutée: {activity.description}")
            
            print(f"✅ ACTIVITY API: {len(activities_list)} activités préparées pour envoi")
            
            return {"success": True, "activities": activities_list}
            
        except Exception as e:
            print(f"❌ ACTIVITY API: Erreur récupération activités: {e}")
            import traceback
            traceback.print_exc()
            return {"success": False, "message": f"Erreur lors de la récupération des activités: {str(e)}"}
        finally:
            db.close()
        
    except Exception as e:
        print(f"❌ ACTIVITY API: Erreur critique: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "message": f"Erreur interne du serveur: {str(e)}"}

def log_activity(company_id: int, admin_id: int, action_type: str, entity_type: str, entity_id: int, description: str, details: dict = None):
    """Fonction pour enregistrer une activité"""
    try:
        print(f"📝 ACTIVITY LOG: Tentative d'enregistrement - {description}")
        db = SessionLocal()
        try:
            activity = models.ActivityLog(
                company_id=company_id,
                admin_id=admin_id,
                action_type=action_type,
                entity_type=entity_type,
                entity_id=entity_id,
                description=description,
                details=details,
                created_at=datetime.now()
            )
            
            db.add(activity)
            db.commit()
            db.refresh(activity)
            print(f"✅ ACTIVITY LOG: Activité enregistrée avec ID {activity.id} - {description}")
            
        except Exception as e:
            db.rollback()
            print(f"❌ ACTIVITY LOG: Erreur enregistrement: {e}")
            import traceback
            traceback.print_exc()
        finally:
            db.close()
            
    except Exception as e:
        print(f"❌ ACTIVITY LOG: Erreur critique: {e}")
        import traceback
        traceback.print_exc()

# Autres routes existantes...
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
                "Maîtrise excellente des technologies modernes",
                "Formation universitaire pertinente en informatique"
            ],
            "weak_points": [
                "Manque de certifications professionnelles récentes",
                "Peu d'expérience avec les technologies cloud"
            ],
            "improvements": [
                "Obtenir des certifications AWS ou Azure",
                "Contribuer à des projets open source"
            ]
        }
        
    except Exception as e:
        print(f"Error in create_detailed_analysis: {str(e)}")
        return {"success": False, "error": str(e)}
