from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse
from databasehr.database import SessionLocal
from databasehr.models import Department, Employee, Job, Application, HRAdmin, ProfileCandidat, Contact
from databasehr.session_manager import current_user_session
from company_utils import get_user_company
from datetime import date
from fastapi.templating import Jinja2Templates
import os

# Configuration des templates
current_dir = os.path.dirname(os.path.abspath(__file__))
templates_dir = os.path.join(current_dir, '../../templates')
templates = Jinja2Templates(directory=templates_dir)

router = APIRouter()

@router.get("/dashboard", response_class=HTMLResponse)
def dashboard_page(request: Request):
    return templates.TemplateResponse("HR-dep/hr-dashboard.html", {"request": request})

@router.get("/hr-reports", response_class=HTMLResponse)
def hr_reports_page(request: Request):
    return templates.TemplateResponse("HR-dep/hr-reports.html", {"request": request})

@router.get("/employee-profile", response_class=HTMLResponse)
def employee_profile_page(request: Request):
    return templates.TemplateResponse("HR-dep/employee-profile.html", {"request": request})

@router.get("/job-details", response_class=HTMLResponse)
def job_details_page(request: Request):
    return templates.TemplateResponse("HR-dep/job-details.html", {"request": request})

@router.get("/api/dashboard-stats")
async def get_dashboard_stats():
    try:
        user_id = current_user_session.get('user_id')
        if not user_id:
            return JSONResponse(
                status_code=401,
                content={"success": False, "message": "Utilisateur non connecté"}
            )
        
        company = get_user_company(user_id)
        if not company:
            return JSONResponse(
                status_code=404,
                content={"success": False, "message": "Aucune entreprise associée"}
            )
        
        db = SessionLocal()
        try:
            # Statistiques des départements
            total_departments = db.query(Department).filter(
                Department.company_id == company.id,
                Department.is_active == True
            ).count()
            
            # Statistiques des employés
            total_employees = db.query(Employee).filter(
                Employee.company_id == company.id,
                Employee.status == 'active'
            ).count()
            
            # Statistiques des postes
            total_jobs = db.query(Job).filter(
                Job.company_id == company.id,
                Job.status.in_(['draft', 'active'])
            ).count()
            
            urgent_jobs = db.query(Job).filter(
                Job.company_id == company.id,
                Job.status.in_(['draft', 'active']),
                Job.priority == 'urgent'
            ).count()
            
            # Statistiques des candidatures
            total_applications = db.query(Application).join(
                Job, Application.job_id == Job.id
            ).filter(
                Job.company_id == company.id,
                Application.status.in_(['pending', 'reviewed'])
            ).count()
            
            # Récupération des dernières candidatures pour le tableau
            recent_applications = db.query(
                Application.id,
                ProfileCandidat.name.label("candidate_name"),  # Récupéré de ProfileCandidat
                Contact.email.label("candidate_email"),       # Récupéré de Contact
                Application.status,
                Job.title.label("job_title"),
                Application.application_date
            ).join(
                Job, Application.job_id == Job.id
            ).join(
                ProfileCandidat, Application.candidate_profile_id == ProfileCandidat.id  # Jointure ajoutée
            ).join(
                Contact, ProfileCandidat.contact_id == Contact.id  # Jointure ajoutée pour l'email
            ).filter(
                Job.company_id == company.id
            ).order_by(
                Application.application_date.desc()
            ).limit(5).all()
            
            # Conversion des résultats en dictionnaires
            recent_applications_list = []
            for app in recent_applications:
                recent_applications_list.append({
                    "id": app.id,
                    "name": app.candidate_name,  # Maintenant disponible
                    "email": app.candidate_email,  # Maintenant disponible
                    "status": app.status,
                    "job": app.job_title,
                    "date": app.application_date.strftime("%d/%m/%Y") if app.application_date else None
                })
            
            # ... (le reste du code inchangé) ...
            
            stats = {
                "total_departments": total_departments,
                "total_employees": total_employees,
                "total_jobs": total_jobs,
                "urgent_jobs": urgent_jobs,
                "total_applications": total_applications,
                "recent_applications": recent_applications_list,  # Liste corrigée

                
            }
            
            return JSONResponse(
                status_code=200,
                content={"success": True, "stats": stats}
            )
            
        except Exception as e:
            return JSONResponse(
                status_code=500,
                content={"success": False, "message": f"Erreur lors du calcul des statistiques: {str(e)}"}
            )
        finally:
            db.close()
            
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"Erreur interne du serveur: {str(e)}"}
        )


@router.get("/api/current-user")
async def get_current_user():
    try:
        user_id = current_user_session.get('user_id')
        if not user_id:
            return JSONResponse(
                status_code=401,
                content={"success": False, "message": "Utilisateur non connecté"}
            )
        
        db = SessionLocal()
        try:
            user = db.query(HRAdmin).filter(HRAdmin.id == user_id).first()
            if not user:
                return JSONResponse(
                    status_code=404,
                    content={"success": False, "message": "Utilisateur non trouvé"}
                )
            
            # Conversion de l'objet ORM en dictionnaire
            user_data = {
                "id": user.id,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "company_id": user.company_id,
                "last_login": user.last_login.strftime("%d/%m/%Y %H:%M") if user.last_login else None
            }
            
            return JSONResponse(
                status_code=200,
                content={"success": True, "user": user_data}
            )
            
        except Exception as e:
            return JSONResponse(
                status_code=500,
                content={"success": False, "message": f"Erreur lors de la récupération de l'utilisateur: {str(e)}"}
            )
        finally:
            db.close()
            
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"Erreur interne du serveur: {str(e)}"}
        )