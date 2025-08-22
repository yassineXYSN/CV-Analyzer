from fastapi import APIRouter, HTTPException, Depends, Request
from .email_service import EmailService, generate_verification_token, save_verification_token, verify_token
from routers.hr.schemas import CompanyCreate, EmployeeCreate
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import List
import os
from datetime import datetime
from auth_utils import hash_password, create_admin_user, authenticate_user
from databasehr.database import get_db
from databasehr.models import Company, Employee, AdminCompanyAccess, HRAdmin
from datetime import datetime

router = APIRouter(prefix="/admin", tags=["admin"])

templates = Jinja2Templates(directory="templates")

@router.get("/", response_class=HTMLResponse)
async def admin_dashboard(request: Request):
    """Page principale de l'interface d'administration"""
    try:
        return templates.TemplateResponse("HR-dep/super_admin_page.html", {"request": request})
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Interface d'administration non trouvée: {str(e)}")

@router.get("/styles/{file_name}")
async def get_admin_styles(file_name: str):
    """Servir les fichiers CSS"""
    file_path = f"templates/HR-dep/styles/{file_name}"
    if os.path.exists(file_path):
        return FileResponse(file_path)
    raise HTTPException(status_code=404, detail="Fichier CSS non trouvé")

@router.get("/scripts/{file_name}")
async def get_admin_scripts(file_name: str):
    """Servir les fichiers JavaScript"""
    file_path = f"templates/HR-dep/scripts/{file_name}"
    if os.path.exists(file_path):
        return FileResponse(file_path)
    raise HTTPException(status_code=404, detail="Fichier JS non trouvé")


# API Routes pour les entreprises
@router.get("/api/companies")
async def get_companies(db: Session = Depends(get_db)):
    """Récupérer toutes les entreprises"""
    companies = db.query(Company).all()
    return [
        {
            "id": company.id,
            "name": company.company_name,
            "company_size": company.company_size,
            "founded_year": company.founded_year,
            "industry": company.industry,
            "description": company.description,
            "logo_url": company.logo_url,
            "website": company.website,
            "setup_completed": bool(company.setup_completed),
            "email": company.email,
            "phone": company.phone,
            "address": company.address,
            "created_at": company.created_at.isoformat() if company.created_at else None
        }
        for company in companies
    ]
@router.post("/api/companies")
async def create_company(company_data: dict, db: Session = Depends(get_db)):
    """Créer une nouvelle entreprise"""
    try:
        # Créer directement l'objet Company sans schema
        db_company = Company(
            company_name=company_data.get('company_name'),
            industry=company_data.get('industry'),
            company_size=company_data.get('company_size'),
            founded_year=company_data.get('founded_year'),
            description=company_data.get('description'),
            website=company_data.get('website'),
            address=company_data.get('address'),
            phone=company_data.get('phone'),
            email=company_data.get('email'),
            setup_completed=1
        )
        
        db.add(db_company)
        db.commit()
        db.refresh(db_company)
        
        return {
            "message": "Entreprise créée avec succès", 
            "id": db_company.id,
            "company_name": db_company.company_name
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=400, 
            detail=f"Erreur lors de la création de l'entreprise: {str(e)}"
        )

    try:
        # Convert Pydantic model to dict and handle the founded_year conversion
        company_data = company.dict()
        
        # Create the company instance
        db_company = Company(**company_data)
        db.add(db_company)
        db.commit()
        db.refresh(db_company)
        
        return {
            "message": "Entreprise créée avec succès", 
            "id": db_company.id,
            "company_name": db_company.company_name
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=400, 
            detail=f"Erreur lors de la création de l'entreprise: {str(e)}"
        )

@router.delete("/api/users/{user_id}")
async def delete_user(user_id: int, db: Session = Depends(get_db)):
    try:
        print(f"Tentative de suppression de l'utilisateur ID: {user_id}")
        
        # Vérifiez d'abord dans HRAdmin
        user = db.query(HRAdmin).filter(HRAdmin.id == user_id).first()
        if user:
            print(f"Utilisateur trouvé dans HRAdmin: {user.email}")
            db.delete(user)
            db.commit()
            return {"message": "Utilisateur supprimé avec succès"}
        
        # Vérifiez ensuite dans Employee
        user = db.query(Employee).filter(Employee.id == user_id).first()
        if user:
            print(f"Utilisateur trouvé dans Employee: {user.email}")
            db.delete(user)
            db.commit()
            return {"message": "Utilisateur supprimé avec succès"}
        
        print("Utilisateur non trouvé dans aucune table")
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
        
    except Exception as e:
        print(f"Erreur lors de la suppression: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur interne: {str(e)}")

# API Routes pour les utilisateurs/employés
@router.get("/api/users")
async def get_users(db: Session = Depends(get_db)):
    """Récupérer tous les utilisateurs (HRAdmin et Employee)"""
    hr_admins = db.query(HRAdmin).all()
    employees = db.query(Employee).all()
    
    # Combiner les deux types d'utilisateurs
    users = []
    
    # Ajouter les HRAdmin
    for admin in hr_admins:
        users.append({
            "id": admin.id,
            "name": f"{admin.first_name} {admin.last_name}",
            "first_name": admin.first_name,
            "last_name": admin.last_name,
            "email": admin.email,
            "phone": None,  # HRAdmin n'a pas de téléphone
            "position": admin.role,
            "company_id": None,  # Les admins ne sont pas liés directement à une entreprise
            "company_name": None,
            "user_type": "admin",
            "is_active": admin.is_active,
            "created_at": admin.created_at.isoformat() if admin.created_at else None
        })
    
    # Ajouter les Employee
    for employee in employees:
        company_name = None
        if employee.company_id:
            company = db.query(Company).filter(Company.id == employee.company_id).first()
            company_name = company.company_name if company else None
            
        users.append({
            "id": f"emp_{employee.id}",  # Préfixe pour éviter les conflits d'ID
            "name": f"{employee.first_name} {employee.last_name}",
            "first_name": employee.first_name,
            "last_name": employee.last_name,
            "email": employee.email,
            "phone": employee.phone,
            "position": employee.position,
            "company_id": employee.company_id,
            "company_name": company_name,
            "user_type": "employee",
            "is_active": employee.status == "active",
            "created_at": employee.created_at.isoformat() if employee.created_at else None
        })
    
    return users

@router.post("/api/users")
async def create_user(user_data: dict, db: Session = Depends(get_db)):
    """Créer un nouveau utilisateur avec vérification d'email"""
    try:
        # Validation des données requises
        required_fields = ["first_name", "last_name", "email", "password"]
        for field in required_fields:
            if not user_data.get(field):
                raise HTTPException(status_code=400, detail=f"Le champ {field} est requis")
        
        # Vérifier si l'utilisateur existe déjà
        existing_user = db.query(HRAdmin).filter(HRAdmin.email == user_data.get("email")).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Un utilisateur avec cet email existe déjà")
        
        password_hash = hash_password(user_data.get("password"))
        
        valid_roles = ["super_admin", "recruiter", "department_head"]
        role = user_data.get("role", "recruiter")
        if role not in valid_roles:
            role = "recruiter"
        
        # Créer l'utilisateur avec is_active=False par défaut
        db_admin = HRAdmin(
            first_name=user_data.get("first_name"),
            last_name=user_data.get("last_name"),
            email=user_data.get("email"),
            password_hash=password_hash,
            role=role,
            is_active=False,  # Compte désactivé jusqu'à vérification
            is_verified=False,
            last_login=datetime.now()
        )
        
        db.add(db_admin)
        db.commit()
        db.refresh(db_admin)
        
        # Générer et sauvegarder le token de vérification
        token = generate_verification_token()
        save_verification_token(db, db_admin.id, token)
        
        # Envoyer l'email de vérification
        email_service = EmailService()
        email_sent = email_service.send_verification_email(db_admin.email, token)
        
        if not email_sent:
            # Rollback si l'email n'a pas pu être envoyé
            db.delete(db_admin)
            db.commit()
            raise HTTPException(status_code=500, detail="Erreur lors de l'envoi de l'email de vérification")
        
        return {
            "message": "Utilisateur créé avec succès. Un email de vérification a été envoyé.", 
            "id": db_admin.id,
            "email": db_admin.email,
            "role": db_admin.role
        }
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Erreur lors de la création: {str(e)}")

@router.post("/api/users/{user_id}/login")
async def update_last_login(user_id: int, db: Session = Depends(get_db)):
    """Met à jour la date de dernière connexion d'un utilisateur"""
    try:
        user = db.query(HRAdmin).filter(HRAdmin.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
        
        user.last_login = datetime.now()
        db.commit()
        
        return {"message": "Date de dernière connexion mise à jour"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Erreur lors de la mise à jour: {str(e)}")
    
    
from fastapi.responses import RedirectResponse

@router.get("/hr-login", response_class=HTMLResponse)
def hr_login_page(request: Request):
    return templates.TemplateResponse("HR-dep/auth/hr-login.html?message=email_verified", {"request": request})

@router.get("/verify-email")
async def verify_email(token: str, db: Session = Depends(get_db)):
    """Vérifier l'email d'un utilisateur et rediriger vers la page de connexion"""
    user = verify_token(db, token)
    if user:
        # Rediriger vers la page de connexion HR avec un message de confirmation
        return RedirectResponse(url="/hr-login?message=email_verified")
    else:
        raise HTTPException(status_code=400, detail="Token invalide ou expiré")

@router.post("/api/users/{user_id}/resend-verification")
async def resend_verification(user_id: int, db: Session = Depends(get_db)):
    """Renvoyer l'email de vérification"""
    user = db.query(HRAdmin).filter(HRAdmin.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    
    if user.is_verified:
        raise HTTPException(status_code=400, detail="L'utilisateur est déjà vérifié")
    
    # Générer un nouveau token
    token = generate_verification_token()
    save_verification_token(db, user.id, token)
    
    # Renvoyer l'email
    email_service = EmailService()
    email_sent = email_service.send_verification_email(user.email, token)
    
    if email_sent:
        return {"message": "Email de vérification renvoyé avec succès"}
    else:
        raise HTTPException(status_code=500, detail="Erreur lors de l'envoi de l'email")

@router.post("/api/users/secure")
async def create_user_secure(user_data: dict, db: Session = Depends(get_db)):
    """Créer un nouveau utilisateur en utilisant directement auth_utils.create_admin_user"""
    try:
        # Validation des données requises
        required_fields = ["first_name", "last_name", "email", "password"]
        for field in required_fields:
            if not user_data.get(field):
                raise HTTPException(status_code=400, detail=f"Le champ {field} est requis")
        
        # Validation du rôle
        valid_roles = ["super_admin", "recruiter", "department_head"]
        role = user_data.get("role", "recruiter")
        if role not in valid_roles:
            role = "recruiter"
        
        user_id = create_admin_user(
            email=user_data.get("email"),
            password=user_data.get("password"),
            first_name=user_data.get("first_name"),
            last_name=user_data.get("last_name"),
            role=role
        )
        
        if not user_id:
            raise HTTPException(status_code=400, detail="Erreur lors de la création de l'utilisateur")
        
        user = db.query(HRAdmin).filter(HRAdmin.id == user_id).first()
        if user:
            user.last_login = datetime.now()
            db.commit()
        
        # Gestion de l'accès entreprise si spécifié
        company_id = user_data.get("company_id")
        if company_id:
            company = db.query(Company).filter(Company.id == company_id).first()
            if company:
                access = AdminCompanyAccess(
                    admin_id=user_id,
                    company_id=company_id,
                    access_level="admin"
                )
                db.add(access)
                db.commit()
        
        return {
            "message": "Utilisateur créé avec succès via auth_utils", 
            "id": user_id,
            "role": role,
            "last_login": user.last_login.isoformat() if user else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erreur lors de la création: {str(e)}")

@router.delete("/api/users/{user_id}")
async def delete_user(user_id: int, db: Session = Depends(get_db)):
    """Supprimer un utilisateur"""
    # Vérifiez d'abord dans la table HRAdmin
    user = db.query(HRAdmin).filter(HRAdmin.id == user_id).first()
    if not user:
        # Si non trouvé, vérifiez dans la table Employee
        user = db.query(Employee).filter(Employee.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    
    db.delete(user)
    db.commit()
    return {"message": "Utilisateur supprimé avec succès"}

# Route pour les statistiques
@router.get("/api/stats")
async def get_admin_stats(db: Session = Depends(get_db)):
    """Récupérer les statistiques pour le dashboard"""
    total_companies = db.query(Company).count()
    total_users = db.query(Employee).count() + db.query(HRAdmin).count()
    
    return {
        "total_companies": total_companies,
        "total_users": total_users,
        "active_companies": total_companies,
        "recent_registrations": 0
    }

@router.get("/api/companies/{company_id}/admins")
async def get_company_admins(company_id: int, db: Session = Depends(get_db)):
    """Récupérer les administrateurs d'une entreprise spécifique"""
    # Vérifier que l'entreprise existe
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Entreprise non trouvée")
    
    # Récupérer les admins via la table de relation admin_company_access
    admins = db.query(HRAdmin).join(
        AdminCompanyAccess, HRAdmin.id == AdminCompanyAccess.admin_id
    ).filter(AdminCompanyAccess.company_id == company_id).all()
    
    return [
        {
            "id": admin.id,
            "name": f"{admin.first_name} {admin.last_name}",
            "email": admin.email,
            "phone": None,  # HRAdmin model doesn't have phone field
            "position": admin.role,  # Using role field from HRAdmin
            "company_id": company_id,
            "company_name": company.company_name,
            "created_at": admin.created_at.isoformat() if admin.created_at else None
        }
        for admin in admins
    ]

@router.post("/api/login")
async def login_user(login_data: dict, db: Session = Depends(get_db)):
    """Authentifier un utilisateur et mettre à jour last_login"""
    try:
        email = login_data.get("email")
        password = login_data.get("password")
        
        if not email or not password:
            raise HTTPException(status_code=400, detail="Email et mot de passe requis")
        
        # Utiliser authenticate_user qui met automatiquement à jour last_login
        user_info = authenticate_user(email, password)
        
        if not user_info:
            raise HTTPException(status_code=401, detail="Email ou mot de passe incorrect")
        
        return {
            "message": "Connexion réussie",
            "user": user_info
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erreur lors de la connexion: {str(e)}")
