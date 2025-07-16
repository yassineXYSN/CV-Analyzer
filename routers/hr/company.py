from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from databasehr.database import SessionLocal
from company_utils import create_company, update_company, get_user_company, get_company_admins,get_company_departments
from utils import add_user_to_company

from databasehr.session_manager import current_user_session
from auth_utils import create_admin_user
from typing import Optional 
import os 
from fastapi.templating import Jinja2Templates  # Import ajouté
import databasehr.models as models



current_dir = os.path.dirname(os.path.abspath(__file__))
templates_dir = os.path.join(current_dir, '../../templates')  # Ajustez ce chemin selon votre structure
templates = Jinja2Templates(directory=templates_dir)  # Initialisation

router = APIRouter()


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

@router.get("/company-setup", response_class=HTMLResponse)
def company_setup_page(request: Request):
    return templates.TemplateResponse("HR-dep/company-setup.html", {"request": request})

@router.get("/company-profile", response_class=HTMLResponse)
def company_profile_page(request: Request):
    try:
        # Vérification de la session utilisateur
        user_id = current_user_session.get('user_id')
        if not user_id:
            return templates.TemplateResponse("HR-dep/auth/hr-login.html", {"request": request})
        
        # Récupération des données de l'entreprise
        company = get_user_company(user_id)
        company_admins = []
        departments = []  # Initialisation de la nouvelle variable
        
        if company:
            company_admins = get_company_admins(company.id)
            departments = get_company_departments(company.id)  # Nouveau: récupération des départements
        
        # Rendu du template avec toutes les données
        return templates.TemplateResponse("HR-dep/company-profile.html", {
            "request": request,
            "company": company,
            "company_admins": company_admins,
            "departments": departments  # Nouveau paramètre ajouté
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return templates.TemplateResponse("HR-dep/auth/hr-login.html", {"request": request})

@router.post("/api/company-setup")
async def setup_company(company_data: CompanySetupRequest):
    try:
        user_id = current_user_session.get('user_id')
        if not user_id:
            return {"success": False, "message": "Utilisateur non connecté"}
        
        existing_company = get_user_company(user_id)
        company_dict = company_data.dict()
        
        if existing_company:
            success = update_company(existing_company.id, company_dict)
            action = "mise à jour"
        else:
            company_id = create_company(user_id, company_dict)
            success = company_id is not None
            action = "création"
        
        if success:
            return {
                "success": True,
                "message": f"Entreprise {action} avec succès",
                "redirect_url": "/dashboard"
            }
        else:
            return {
                "success": False,
                "message": f"Erreur lors de la {action} de l'entreprise"
            }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"success": False, "message": "Erreur interne du serveur"}

@router.post("/api/create-user")
async def create_user(user_data: dict):
    try:
        current_user_id = current_user_session.get('user_id')
        if not current_user_id:
            return {"success": False, "message": "Utilisateur non connecté"}
        
        # Création de l'utilisateur
        new_user_id = create_admin_user(
            email=user_data['email'],
            password=user_data['password'],
            first_name=user_data['first_name'],
            last_name=user_data['last_name'],
            role=user_data.get('role', 'super_admin')
        )
        
        if not new_user_id:
            return {"success": False, "message": "Erreur lors de la création de l'utilisateur"}
        
        db = SessionLocal()
        try:
            # Création des permissions
            permissions_data = user_data.get('permissions', {})
            permissions = models.AdminPermissions(
                admin_id=new_user_id,
                can_add_department=permissions_data.get('can_add_department', False),
                can_manage_applications=permissions_data.get('can_manage_applications', False),
                can_recommend_candidates=permissions_data.get('can_recommend_candidates', False)
            )
            db.add(permissions)
            
            # Gestion des départements
            for dept_id in user_data.get('departments', []):
                assignment = models.AdminDepartments(
                    admin_id=new_user_id,
                    department_id=dept_id
                )
                db.add(assignment)
            
            # Récupérer l'entreprise de l'utilisateur actuel
            current_user_company = get_user_company(current_user_id)
            if current_user_company:
                # Ajouter l'accès à l'entreprise
                company_access = models.AdminCompanyAccess(
                    admin_id=new_user_id,
                    company_id=current_user_company.id,
                    access_level='admin',  # ou user_data.get('access_level', 'admin')
                    granted_by=current_user_id
                )
                db.add(company_access)
            
            db.commit()
            
            return {"success": True, "message": "Utilisateur créé avec succès"}
            
        except Exception as e:
            db.rollback()
            return {"success": False, "message": f"Erreur création permissions: {str(e)}"}
        finally:
            db.close()
            
    except Exception as e:
        return {"success": False, "message": f"Erreur: {str(e)}"}

@router.get("/api/company-info")
async def get_company_info():
    try:
        user_id = current_user_session.get('user_id')
        if not user_id:
            return {"success": False, "message": "Utilisateur non connecté"}
        
        company = get_user_company(user_id)
        if not company:
            return {"success": False, "message": "Aucune entreprise trouvée"}
        
        return {"success": True, "company": company}
    except Exception as e:
        return {"success": False, "message": "Erreur interne du serveur"}

@router.get("/api/company-users")
async def get_company_users():
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
        return {"success": False, "message": "Erreur interne du serveur"}