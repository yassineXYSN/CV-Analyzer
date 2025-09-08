from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from databasehr.database import SessionLocal
# AJOUT DE L'IMPORT DE COMPANY CORRECTEMENT
from databasehr.models import Employee, Department, ProfileCandidat, Contact, AnalyseCandidat, Application, Job, Company
from databasehr.session_manager import current_user_session
from company_utils import get_user_company  # Ajout de cet import
from sqlalchemy.orm import Session
from datetime import datetime

# Configuration des templates
templates = Jinja2Templates(directory="templates")

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
        
@router.get("/candidate-profile/{candidate_id}", response_class=HTMLResponse)
def candidate_profile_page(candidate_id: int, request: Request, db: Session = Depends(get_db)):
    """Page de profil candidat pour HR (rendu côté serveur)."""
    try:
        # Vérification de l'authentification
        user_id = current_user_session.get('user_id')
        if not user_id:
            return templates.TemplateResponse("HR-dep/auth/hr-login.html", {"request": request})

        # Charger le candidat et ses données liées
        candidate = db.query(ProfileCandidat).filter(ProfileCandidat.id == candidate_id).first()
        if not candidate:
            return templates.TemplateResponse("HR-dep/candidate-profile.html", {"request": request, "profile": None})

        contact = db.query(Contact).filter(Contact.id == candidate.contact_id).first() if candidate.contact_id else None

        # Parser les champs JSON qui peuvent être stockés en chaînes
        import json
        def parse_json(value):
            if value is None:
                return None
            if isinstance(value, (list, dict)):
                return value
            try:
                return json.loads(value)
            except Exception:
                return None

        education = parse_json(candidate.education) or []
        languages = parse_json(candidate.languages) or []
        certificates = parse_json(candidate.certificates) or []
        skills = parse_json(candidate.skills) or []

        years_of_experience = 0
        if isinstance(skills, list):
            years_of_experience = min(len(skills) // 3, 15)

        parsed_skills = [{"name": s if isinstance(s, str) else str(s)} for s in skills] if isinstance(skills, list) else []

        profile = {
            "id": candidate.id,
            "name": candidate.name,
            "title": candidate.title,
            "profile": candidate.profile,
            "education": education,
            "languages": languages,
            "certificates": certificates,
            "years_of_experience": years_of_experience,
        }

        context = {
            "request": request,
            "profile": profile,
            "contact": contact,
            "parsed_skills": parsed_skills,
            "current_user": None,
        }

        # Rendre le template client et injecter un override CSS léger pour les couleurs HR
        template = templates.get_template("client-dep/profile_detail.html")
        html = template.render(context)

        hr_override_css = (
            "<style>"
            "body{background:linear-gradient(135deg,#0b1220 0%,#0f172a 50%,#1e293b 100%)}"
            ".sidebar{background:linear-gradient(180deg,#0b1220 0%,#0f172a 100%);border-right:1px solid rgba(37,99,235,.25)}"
            ".back-btn{background:linear-gradient(135deg,#2563eb 0%,#1e40af 100%);color:#fff;box-shadow:0 4px 15px rgba(37,99,235,.35)}"
            ".back-btn:hover{box-shadow:0 8px 25px rgba(37,99,235,.55)}"
            ".profile-avatar-sidebar{border:3px solid rgba(37,99,235,.6);box-shadow:0 8px 25px rgba(37,99,235,.35)}"
            ".page-title{background:linear-gradient(135deg,#2563eb 0%,#1e40af 100%);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text}"
            ".stat-number{background:linear-gradient(135deg,#2563eb 0%,#1e40af 100%);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text}"
            ".info-card{border:1px solid rgba(37,99,235,.2)}.info-card:hover{border-color:rgba(37,99,235,.4)}"
            ".card-header{border-bottom:2px solid rgba(37,99,235,.25)}"
            ".skill-tag:hover{background:linear-gradient(135deg,#2563eb 0%,#1e40af 100%);color:#fff}"
            ".contact-card-main{border-left:4px solid #22c55e}.contact-icon-main{color:#22c55e;background:rgba(34,197,94,.2)}"
            ".education-timeline::before{background:linear-gradient(180deg,#2563eb 0%,#1e40af 100%)}"
            ".education-item-timeline::before{background:linear-gradient(135deg,#2563eb 0%,#1e40af 100%)}"
            ".education-year-timeline{background:linear-gradient(135deg,#fbbf24 0%,#f59e0b 100%);color:#111827}"
            "</style>"
        )

        if "</head>" in html:
            html = html.replace("</head>", hr_override_css + "</head>", 1)
        else:
            html = hr_override_css + html

        response = HTMLResponse(content=html)
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response

    except Exception:
        import traceback
        traceback.print_exc()
        return templates.TemplateResponse("HR-dep/auth/hr-login.html", {"request": request})

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
        
        # Récupérer les candidatures du candidat
        applications = db.query(Application).filter(Application.candidate_profile_id == candidate_id).all()
        
        # Calculer les statistiques
        total_applications = len(applications)
        accepted_applications = len([app for app in applications if app.status == 'accepted'])
        pending_applications = len([app for app in applications if app.status == 'pending'])
        
        # Calculer l'expérience en années (simulation basée sur les données disponibles)
        years_of_experience = 0
        if candidate.skills:
            # Estimation basée sur le nombre de compétences
            years_of_experience = min(len(candidate.skills) // 3, 15)
        
        # Formater la réponse
        candidate_data = {
            "id": candidate.id,
            "name": candidate.name,
            "first_name": candidate.name.split()[0] if candidate.name else "",
            "last_name": " ".join(candidate.name.split()[1:]) if candidate.name else "",
            "title": candidate.title,
            "profile": candidate.profile,
            "education": candidate.education or [],
            "languages": candidate.languages or [],
            "certificates": candidate.certificates or [],
            "skills": candidate.skills or [],
            "years_of_experience": years_of_experience,
            "email": contact.email if contact else None,
            "phone": contact.phone if contact else None,
            "linkedin": contact.linkedin if contact else None,
            "address": contact.address if contact else None,
            "analyse": analyse.analyse if analyse else None,
            "total_applications": total_applications,
            "accepted_applications": accepted_applications,
            "pending_applications": pending_applications,
            "created_at": None,  # Pas de champ created_at dans le modèle HR
            "updated_at": None   # Pas de champ updated_at dans le modèle HR
        }
        
        return {"success": True, "candidate": candidate_data}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération du candidat: {str(e)}")

@router.get("/api/candidate/{candidate_id}/applications")
def get_candidate_applications(candidate_id: int, db: Session = Depends(get_db)):
    """Récupère toutes les candidatures d'un candidat spécifique"""
    try:
        # Récupérer les candidatures du candidat avec les détails des postes
        applications = db.query(
            Application.id,
            Application.status,
            Application.application_date,
            Job.title.label("job_title"),
            Job.description.label("job_description"),
            Department.name.label("department_name"),
            Company.company_name.label("company_name")
        ).join(
            Job, Application.job_id == Job.id
        ).join(
            Department, Job.department_id == Department.id
        ).join(
            Company, Department.company_id == Company.id
        ).filter(
            Application.candidate_profile_id == candidate_id
        ).all()
        
        applications_list = []
        for app in applications:
            applications_list.append({
                "id": app.id,
                "status": app.status,
                "application_date": app.application_date.isoformat() if app.application_date else None,
                "compatibility_percentage": None,  # Pas de champ dans le modèle HR
                "compatibility_score": None,       # Pas de champ dans le modèle HR
                "job_title": app.job_title,
                "job_description": app.job_description,
                "department_name": app.department_name,
                "company_name": app.company_name
            })
        
        return {"success": True, "applications": applications_list}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération des candidatures: {str(e)}")