from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from databasehr.database import SessionLocal
from company_utils import create_company, update_company, get_user_company, get_company_admins, get_company_departments
from utils import add_user_to_company

from databasehr.session_manager import current_user_session
from auth_utils import create_admin_user
from .email_service import EmailService, generate_verification_token, save_verification_token, verify_token
from typing import Optional 
import os 
from fastapi.templating import Jinja2Templates
import databasehr.models as models
from datetime import datetime
from .admin_router import publish_event

current_dir = os.path.dirname(os.path.abspath(__file__))
templates_dir = os.path.join(current_dir, '../../templates')
templates = Jinja2Templates(directory=templates_dir)

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
    facebook_url: Optional[str] = None

class CreateUserRequest(BaseModel):
    email: str
    password: str
    first_name: str
    last_name: str
    role: str = "hr_admin"
    company_id: Optional[int] = None
    access_level: str = "admin"

class UpdateUserRequest(BaseModel):
    email: Optional[str] = None
    password: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: Optional[str] = None  # 'recruiter' | 'department_head'
    is_active: Optional[bool] = None
    permissions: Optional[dict] = None
    departments: Optional[list[int]] = None

def check_super_admin_permission(user_id: int) -> bool:
    """
    Vérifie si l'utilisateur actuel est un super admin
    """
    db = SessionLocal()
    try:
        user = db.query(models.HRAdmin).filter(models.HRAdmin.id == user_id).first()
        if not user:
            return False
        return user.role == "super_admin"
    except Exception as e:
        print(f"Erreur lors de la vérification des permissions: {e}")
        return False
    finally:
        db.close()

@router.get("/company-setup", response_class=HTMLResponse)
def company_setup_page(request: Request):
    # Check authentication
    user_id = current_user_session.get('user_id')
    if not user_id:
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/hr-login", status_code=302)
    
    response = templates.TemplateResponse("HR-dep/company-setup.html", {"request": request})
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

@router.get("/company-profile", response_class=HTMLResponse)
def company_profile_page(request: Request):
    try:
        # Vérification de la session utilisateur
        user_id = current_user_session.get('user_id')
        if not user_id:
            return templates.TemplateResponse("HR-dep/auth/hr-login.html", {"request": request})
        
        # Vérification des permissions super admin
        is_super_admin = check_super_admin_permission(user_id)
        
        # Récupération des données de l'entreprise
        company = get_user_company(user_id)
        company_admins = []
        departments = []
        
        if company:
            company_admins = get_company_admins(company.id)
            departments = get_company_departments(company.id)
        
        # Rendu du template avec toutes les données incluant les permissions
        response = templates.TemplateResponse("HR-dep/company-profile.html", {
            "request": request,
            "company": company,
            "company_admins": company_admins,
            "departments": departments,
            "is_super_admin": is_super_admin  # Nouveau paramètre pour les permissions
        })
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response
        
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
        
        # NOUVELLE VÉRIFICATION: Seuls les super admins peuvent créer des utilisateurs
        if not check_super_admin_permission(current_user_id):
            return {
                "success": False, 
                "message": "Accès refusé. Seuls les super administrateurs peuvent créer des comptes recruteur et chef de département."
            }
        
        # Vérification supplémentaire du rôle demandé
        requested_role = user_data.get('role', '')
        if requested_role not in ['recruiter', 'department_head']:
            return {
                "success": False,
                "message": "Rôle non autorisé. Seuls les rôles 'recruiter' et 'department_head' peuvent être créés."
            }
        
        db = SessionLocal()
        try:
            existing_user = db.query(models.HRAdmin).filter(models.HRAdmin.email == user_data.get("email")).first()
            if existing_user:
                return {"success": False, "message": "Un utilisateur avec cet email existe déjà"}
            
            from auth_utils import hash_password
            password_hash = hash_password(user_data.get("password"))
            
            db_admin = models.HRAdmin(
                first_name=user_data.get("first_name"),
                last_name=user_data.get("last_name"),
                email=user_data.get("email"),
                password_hash=password_hash,
                role=requested_role,
                is_active=False,  # Compte désactivé jusqu'à vérification
                is_verified=False,
                last_login=datetime.now()
            )
            
            db.add(db_admin)
            db.commit()

            # Diffuser l'évènement temps réel vers l'interface admin
            try:
                await publish_event({
                    "type": "user_created",
                    "user": {
                        "id": db_admin.id,
                        "name": f"{db_admin.first_name} {db_admin.last_name}",
                        "first_name": db_admin.first_name,
                        "last_name": db_admin.last_name,
                        "email": db_admin.email,
                        "position": db_admin.role,
                        "user_type": "admin",
                        "is_active": db_admin.is_active,
                        "is_verified": db_admin.is_verified,
                        "created_at": db_admin.created_at.isoformat() if db_admin.created_at else None
                    },
                    "timestamp": datetime.now().isoformat()
                })
            except Exception:
                pass
            db.refresh(db_admin)
            new_user_id = db_admin.id
            
            if not new_user_id:
                return {"success": False, "message": "Erreur lors de la création de l'utilisateur"}
            
            # Création des permissions
            permissions_data = user_data.get('permissions', {})
            # Pour les chefs de département, forcer can_manage_applications à False
            can_manage_applications = False if user_data.get('role') == 'department_head' else permissions_data.get('can_manage_applications', False)
            
            permissions = models.AdminPermissions(
                admin_id=new_user_id,
                can_add_department=permissions_data.get('can_add_department', False),
                can_manage_applications=can_manage_applications,
                can_recommend_candidates=permissions_data.get('can_recommend_candidates', False)
            )
            db.add(permissions)
            
            # Gestion des départements (seulement pour les chefs de département)
            if requested_role == 'department_head':
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
                    access_level='admin',
                    granted_by=current_user_id
                )
                db.add(company_access)
            
            token = generate_verification_token()
            save_verification_token(db, new_user_id, token)
            
            email_service = EmailService()
            email_sent = email_service.send_verification_email(db_admin.email, token)
            
            if not email_sent:
                # Rollback si l'email n'a pas pu être envoyé
                db.rollback()
                return {"success": False, "message": "Erreur lors de l'envoi de l'email de vérification"}
            
            db.commit()
            
            role_names = {
                'recruiter': 'Recruteur',
                'department_head': 'Chef de Département'
            }
            
            return {
                "success": True, 
                "message": f"{role_names.get(requested_role, 'Utilisateur')} créé avec succès. Un email de vérification a été envoyé à {db_admin.email}."
            }
            
        except Exception as e:
            db.rollback()
            return {"success": False, "message": f"Erreur création utilisateur: {str(e)}"}
        finally:
            db.close()
            
    except Exception as e:
        return {"success": False, "message": f"Erreur: {str(e)}"}

@router.get("/api/users/{admin_id}")
async def get_user_details(admin_id: int):
    try:
        current_user_id = current_user_session.get('user_id')
        if not current_user_id:
            return {"success": False, "message": "Utilisateur non connecté"}

        if not check_super_admin_permission(current_user_id):
            return {"success": False, "message": "Accès refusé"}

        db = SessionLocal()
        try:
            admin = db.query(models.HRAdmin).filter(models.HRAdmin.id == admin_id).first()
            if not admin:
                return {"success": False, "message": "Utilisateur non trouvé"}

            permissions = db.query(models.AdminPermissions).filter(models.AdminPermissions.admin_id == admin.id).first()
            assigned_depts = db.query(models.AdminDepartments).filter(models.AdminDepartments.admin_id == admin.id).all()
            departments = [d.department_id for d in assigned_depts]

            return {
                "success": True,
                "user": {
                    "id": admin.id,
                    "email": admin.email,
                    "first_name": admin.first_name,
                    "last_name": admin.last_name,
                    "role": admin.role,
                    "is_active": admin.is_active,
                    "permissions": {
                        "can_add_department": bool(getattr(permissions, 'can_add_department', False)),
                        "can_manage_applications": False if admin.role == 'department_head' else bool(getattr(permissions, 'can_manage_applications', False)),
                        "can_recommend_candidates": bool(getattr(permissions, 'can_recommend_candidates', False)),
                    },
                    "departments": departments,
                }
            }
        except Exception as e:
            return {"success": False, "message": f"Erreur: {str(e)}"}
        finally:
            db.close()
    except Exception as e:
        return {"success": False, "message": f"Erreur interne: {str(e)}"}

@router.post("/api/users/{admin_id}/update")
async def update_user(admin_id: int, update: UpdateUserRequest):
    try:
        current_user_id = current_user_session.get('user_id')
        if not current_user_id:
            return {"success": False, "message": "Utilisateur non connecté"}

        if not check_super_admin_permission(current_user_id):
            return {"success": False, "message": "Accès refusé"}

        db = SessionLocal()
        try:
            admin = db.query(models.HRAdmin).filter(models.HRAdmin.id == admin_id).first()
            if not admin:
                return {"success": False, "message": "Utilisateur non trouvé"}

            # Basic fields
            if update.email is not None:
                admin.email = update.email
            if update.first_name is not None:
                admin.first_name = update.first_name
            if update.last_name is not None:
                admin.last_name = update.last_name
            if update.is_active is not None:
                admin.is_active = update.is_active

            # Role update (restrict to allowed roles)
            if update.role in ['recruiter', 'department_head']:
                admin.role = update.role

            # Password update (if provided)
            if update.password:
                # Reuse create_admin_user hashing util indirectly if available, else store plaintext not recommended.
                # Here we assume models.HRAdmin has password_hash and auth utility is separate; skipping if not supported.
                try:
                    from auth_utils import hash_password
                    admin.password_hash = hash_password(update.password)
                except Exception:
                    pass

            # Permissions
            perms = db.query(models.AdminPermissions).filter(models.AdminPermissions.admin_id == admin.id).first()
            if not perms:
                perms = models.AdminPermissions(admin_id=admin.id)
                db.add(perms)

            if update.permissions is not None:
                perms.can_add_department = bool(update.permissions.get('can_add_department', getattr(perms, 'can_add_department', False)))
                # Pour les chefs de département, forcer can_manage_applications à False
                if admin.role == 'department_head':
                    perms.can_manage_applications = False
                else:
                    perms.can_manage_applications = bool(update.permissions.get('can_manage_applications', getattr(perms, 'can_manage_applications', False)))
                perms.can_recommend_candidates = bool(update.permissions.get('can_recommend_candidates', getattr(perms, 'can_recommend_candidates', False)))

            # Departments (only for department_head)
            if update.departments is not None:
                # Clear existing
                db.query(models.AdminDepartments).filter(models.AdminDepartments.admin_id == admin.id).delete()
                # Insert new
                for dept_id in update.departments:
                    db.add(models.AdminDepartments(admin_id=admin.id, department_id=dept_id))

            db.commit()
            return {"success": True, "message": "Utilisateur mis à jour avec succès"}
        except Exception as e:
            db.rollback()
            return {"success": False, "message": f"Erreur lors de la mise à jour: {str(e)}"}
        finally:
            db.close()
    except Exception as e:
        return {"success": False, "message": f"Erreur interne: {str(e)}"}

@router.delete("/api/users/{admin_id}")
async def delete_user(admin_id: int):
    try:
        current_user_id = current_user_session.get('user_id')
        if not current_user_id:
            return {"success": False, "message": "Utilisateur non connecté"}

        if not check_super_admin_permission(current_user_id):
            return {"success": False, "message": "Accès refusé"}

        db = SessionLocal()
        try:
            admin = db.query(models.HRAdmin).filter(models.HRAdmin.id == admin_id).first()
            if not admin:
                return {"success": False, "message": "Utilisateur non trouvé"}

            # Prevent deleting last super_admin or self if desired; here allow deleting non-super_admin
            if admin.role == 'super_admin':
                return {"success": False, "message": "Impossible de supprimer un super administrateur"}

            # Delete relations
            db.query(models.AdminCompanyAccess).filter(models.AdminCompanyAccess.admin_id == admin.id).delete()
            db.query(models.AdminDepartments).filter(models.AdminDepartments.admin_id == admin.id).delete()
            db.query(models.AdminPermissions).filter(models.AdminPermissions.admin_id == admin.id).delete()

            db.delete(admin)
            db.commit()
            return {"success": True, "message": "Utilisateur supprimé avec succès"}
        except Exception as e:
            db.rollback()
            return {"success": False, "message": f"Erreur lors de la suppression: {str(e)}"}
        finally:
            db.close()
    except Exception as e:
        return {"success": False, "message": f"Erreur interne: {str(e)}"}

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

@router.get("/api/check-permissions")
async def check_user_permissions():
    """
    Endpoint pour vérifier les permissions de l'utilisateur actuel
    """
    try:
        user_id = current_user_session.get('user_id')
        if not user_id:
            return {"success": False, "message": "Utilisateur non connecté"}
        
        is_super_admin = check_super_admin_permission(user_id)
        
        return {
            "success": True,
            "permissions": {
                "is_super_admin": is_super_admin,
                "can_create_users": is_super_admin
            }
        }
    except Exception as e:
        return {"success": False, "message": f"Erreur: {str(e)}"}
