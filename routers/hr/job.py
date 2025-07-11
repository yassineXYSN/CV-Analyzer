from fastapi import APIRouter
from pydantic import BaseModel
from databasehr.database import SessionLocal
# Ajout de l'import de Company
from databasehr.models import Job, Department, Employee, Application, ProfileCandidat, Contact, Company
from databasehr.session_manager import current_user_session
from company_utils import get_user_company
from datetime import datetime, date
from typing import Optional 

router = APIRouter()

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

@router.post("/api/create-job")
async def create_job(job_data: JobRequest):
    try:
        user_id = current_user_session.get('user_id')
        if not user_id:
            return {"success": False, "message": "Utilisateur non connecté"}
        
        company = get_user_company(user_id)
        if not company:
            return {"success": False, "message": "Aucune entreprise associée"}
        
        db = SessionLocal()
        try:
            department = db.query(Department).filter(
                Department.id == job_data.department_id,
                Department.company_id == company.id,
                Department.is_active == True
            ).first()
            
            if not department:
                return {"success": False, "message": "Département non trouvé"}
            
            deadline_obj = None
            if job_data.deadline:
                try:
                    deadline_obj = datetime.strptime(job_data.deadline, "%Y-%m-%d").date()
                except ValueError:
                    pass
            
            assigned_employee = None
            if job_data.assigned_employee_id:
                assigned_employee = db.query(Employee).filter(
                    Employee.id == job_data.assigned_employee_id,
                    Employee.company_id == company.id,
                    Employee.status == 'active'
                ).first()
                if not assigned_employee:
                    job_data.assigned_employee_id = None
            
            new_job = Job(
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
                applications_count=0
            )
            
            db.add(new_job)
            db.commit()
            db.refresh(new_job)
            
            return {
                "success": True,
                "message": f"Poste '{job_data.title}' créé avec succès",
                "job": new_job
            }
        except Exception as e:
            db.rollback()
            return {"success": False, "message": f"Erreur lors de la création du poste: {str(e)}"}
        finally:
            db.close()
    except Exception as e:
        return {"success": False, "message": f"Erreur interne du serveur: {str(e)}"}

@router.get("/api/jobs")
async def get_jobs():
    try:
        user_id = current_user_session.get('user_id')
        if not user_id:
            return {"success": False, "message": "Utilisateur non connecté"}
        
        company = get_user_company(user_id)
        if not company:
            return {"success": False, "message": "Aucune entreprise associée"}
        
        db = SessionLocal()
        try:
            jobs = db.query(Job).filter(
                Job.company_id == company.id,
                Job.status.in_(['draft', 'active', 'paused'])
            ).all()
            
            jobs_list = []
            for job in jobs:
                department = db.query(Department).filter(
                    Department.id == job.department_id
                ).first()
                
                assigned_employee = None
                if job.assigned_employee_id:
                    assigned_employee = db.query(Employee).filter(
                        Employee.id == job.assigned_employee_id
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
                    "applications_count": job.applications_count,
                    "created_at": job.created_at.isoformat() if job.created_at else None
                })
            
            return {
                "success": True,
                "jobs": jobs_list
            }
        except Exception as e:
            return {"success": False, "message": f"Erreur lors de la récupération des postes: {str(e)}"}
        finally:
            db.close()
    except Exception as e:
        return {"success": False, "message": f"Erreur interne du serveur: {str(e)}"}

@router.get("/api/job/{job_id}")
async def get_job_details(job_id: int):
    try:
        user_id = current_user_session.get('user_id')
        if not user_id:
            return {"success": False, "message": "Utilisateur non connecté"}
        
        company = get_user_company(user_id)
        if not company:
            return {"success": False, "message": "Aucune entreprise associée"}
        
        db = SessionLocal()
        try:
            job = db.query(Job).filter(
                Job.id == job_id,
                Job.company_id == company.id
            ).first()
            
            if not job:
                return {"success": False, "message": "Poste non trouvé"}
            
            department = db.query(Department).filter(
                Department.id == job.department_id
            ).first()
            
            assigned_employee = None
            if job.assigned_employee_id:
                assigned_employee = db.query(Employee).filter(
                    Employee.id == job.assigned_employee_id
                ).first()
            
            applications = db.query(Application).filter(
                Application.job_id == job_id
            ).all()
            
            applications_list = []
            for app in applications:
                candidate = db.query(ProfileCandidat).filter(
                    ProfileCandidat.id == app.candidate_profile_id
                ).first()
                
                if candidate:
                    applications_list.append({
                        "id": app.id,
                        "name": candidate.name,
                        "title": candidate.title,
                        "status": app.status,
                        "application_date": app.application_date.isoformat() if app.application_date else None,
                        "hr_rating": float(app.hr_rating) if app.hr_rating else None,
                        "hr_notes": app.hr_notes,
                        "candidate_id": candidate.id
                    })
            
            days_remaining = None
            if job.deadline:
                today = date.today()
                days_remaining = (job.deadline - today).days
                days_remaining = max(0, days_remaining)
            
            job_data = {
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
                "days_remaining": days_remaining,
                "applications_count": len(applications_list),
                "applications": applications_list,
                "created_at": job.created_at.isoformat() if job.created_at else None
            }
            
            return {
                "success": True,
                "job": job_data
            }
        except Exception as e:
            return {"success": False, "message": f"Erreur lors de la récupération du poste: {str(e)}"}
        finally:
            db.close()
    except Exception as e:
        return {"success": False, "message": f"Erreur interne du serveur: {str(e)}"}