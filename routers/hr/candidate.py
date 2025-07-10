from fastapi import APIRouter, HTTPException, Depends
from database import SessionLocal
# AJOUT DE L'IMPORT DE COMPANY CORRECTEMENT
from models import Employee, Company, Department, ProfileCandidat, Contact
from session_manager import current_user_session
from company_utils import get_user_company  # Ajout de cet import
from sqlalchemy.orm import Session
from datetime import datetime

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# candidate.py
# ... (imports existants)

@router.post("/candidates/{candidate_id}/accept")
async def accept_candidate(
    candidate_id: int,
    position: str,
    salary: float,
    start_date: datetime,
    db: Session = Depends(get_db)
):
    try:
        # Récupérer le candidat
        candidate = db.query(ProfileCandidat).filter(ProfileCandidat.id == candidate_id).first()
        if not candidate:
            raise HTTPException(status_code=404, detail="Candidat non trouvé")
        
        # Récupérer l'utilisateur connecté
        user_id = current_user_session.get('user_id')
        if not user_id:
            raise HTTPException(status_code=401, detail="Utilisateur non connecté")
        
        # Récupérer l'entreprise de l'utilisateur via admin_company_access
        company = get_user_company(user_id)
        if not company:
            raise HTTPException(status_code=404, detail="Aucune entreprise associée à cet administrateur")
        
        # Récupérer un département par défaut (ex: "Recrutement")
        department = db.query(Department).filter(
            Department.company_id == company.id
        ).first()
        
        # Créer un département par défaut si nécessaire
        if not department:
            department = Department(
                name="Nouveaux Employés",
                company_id=company.id
            )
            db.add(department)
            db.commit()
            db.refresh(department)
        
        # Créer le nouvel employé
        new_employee = Employee(
            first_name=candidate.name.split()[0] if candidate.name else "",
            last_name=" ".join(candidate.name.split()[1:]) if candidate.name else "",
            email=candidate.contact.email if candidate.contact else "",
            phone=candidate.contact.phone if candidate.contact else "",
            position=position,
            salary=salary,
            hire_date=start_date,
            department_id=department.id,
            company_id=company.id,  # Utiliser l'ID de l'entreprise trouvée
            status="active",
            candidate_profile_id=candidate.id
        )
        
        db.add(new_employee)
        db.commit()
        
        return {
            "success": True,
            "message": "Candidat accepté avec succès",
            "employee_id": new_employee.id
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de l'acceptation du candidat: {str(e)}"
        )