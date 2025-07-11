from fastapi import APIRouter, HTTPException, Depends
from databasehr.database import SessionLocal
# AJOUT DE L'IMPORT DE COMPANY CORRECTEMENT
from databasehr.models import Employee, Department, ProfileCandidat, Contact,AnalyseCandidat  
from databasehr.session_manager import current_user_session
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
            company_id=company.id, 
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
        
@router.get("/api/candidate/{candidate_id}")
def get_candidate(candidate_id: int, db: Session = Depends(get_db)):
    try:
        # Récupérer le candidat avec ses relations
        candidate = db.query(ProfileCandidat).filter(ProfileCandidat.id == candidate_id).first()
        if not candidate:
            raise HTTPException(status_code=404, detail="Candidat non trouvé")
        
        # Récupérer les données liées
        contact = db.query(Contact).filter(Contact.id == candidate.contact_id).first() if candidate.contact_id else None
        analyse = db.query(AnalyseCandidat).filter(AnalyseCandidat.id == candidate.analyse_id).first() if candidate.analyse_id else None
        
        # Formater la réponse
        candidate_data = {
            "id": candidate.id,
            "name": candidate.name,
            "first_name": candidate.name.split()[0] if candidate.name else "",
            "last_name": " ".join(candidate.name.split()[1:]) if candidate.name else "",
            "title": candidate.title,
            "profile": candidate.profile,
            "education": candidate.education,
            "languages": candidate.languages,
            "certificates": candidate.certificates,
            "skills": candidate.skills,
            "email": contact.email if contact else None,
            "phone": contact.phone if contact else None,
            "linkedin": contact.linkedin if contact else None,
            "address": contact.address if contact else None,
            "analyse": analyse.analyse if analyse else None
        }
        
        return {"success": True, "candidate": candidate_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération du candidat: {str(e)}")