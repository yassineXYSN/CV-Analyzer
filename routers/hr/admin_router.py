from fastapi import APIRouter, HTTPException, Depends, Request
from routers.hr.schemas import CompanyCreate, EmployeeCreate
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import List
import os
from databasehr.database import get_db
from databasehr.models import Company, Employee, AdminCompanyAccess, HRAdmin

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
            "email": company.email,
            "phone": company.phone,
            "address": company.address,
            "created_at": company.created_at.isoformat() if company.created_at else None
        }
        for company in companies
    ]

@router.post("/api/companies")
async def create_company(company: CompanyCreate, db: Session = Depends(get_db)):
    """Créer une nouvelle entreprise"""
    db_company = Company(**company.dict())
    db.add(db_company)
    db.commit()
    db.refresh(db_company)
    return {"message": "Entreprise créée avec succès", "id": db_company.id}

@router.delete("/api/companies/{company_id}")
async def delete_company(company_id: int, db: Session = Depends(get_db)):
    """Supprimer une entreprise"""
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Entreprise non trouvée")
    
    db.delete(company)
    db.commit()
    return {"message": "Entreprise supprimée avec succès"}

# API Routes pour les utilisateurs/employés
@router.get("/api/users")
async def get_users(db: Session = Depends(get_db)):
    """Récupérer tous les utilisateurs"""
    users = db.query(Employee).all()
    return [
        {
            "id": user.id,
            "name": f"{user.first_name} {user.last_name}",
            "email": user.email,
            "phone": user.phone,
            "position": user.position,
            "company_id": user.company_id,
            "company_name": user.company.company_name if user.company else None,
            "created_at": user.created_at.isoformat() if user.created_at else None
        }
        for user in users
    ]

@router.post("/api/users")
async def create_user(user: EmployeeCreate, db: Session = Depends(get_db)):
    """Créer un nouveau utilisateur"""
    # Vérifier que l'entreprise existe
    company = db.query(Company).filter(Company.id == user.company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Entreprise non trouvée")
    
    db_user = Employee(**user.dict())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return {"message": "Utilisateur créé avec succès", "id": db_user.id}

@router.delete("/api/users/{user_id}")
async def delete_user(user_id: int, db: Session = Depends(get_db)):
    """Supprimer un utilisateur"""
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
    total_users = db.query(Employee).count()
    
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
