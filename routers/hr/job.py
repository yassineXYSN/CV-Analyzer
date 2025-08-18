from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from databasehr.database import SessionLocal
from databasehr.models import Job, Department, Employee, Application, ProfileCandidat, Contact, HRAdmin, JobSkill
from databasehr.session_manager import current_user_session
from company_utils import get_user_company
from datetime import datetime, date
from typing import Optional, List

class SkillRequest(BaseModel):
    skill_name: str
    skill_level: str = "intermediate"
    is_required: bool = True

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
    skills: Optional[List[SkillRequest]] = []

router = APIRouter()

@router.post("/api/create-job")
async def create_job(job_data: JobRequest):
    try:
        user_id = current_user_session.get('user_id')
        if not user_id:
            raise HTTPException(status_code=401, detail="Utilisateur non connecté")
        
        company = get_user_company(user_id)
        if not company:
            raise HTTPException(status_code=404, detail="Aucune entreprise associée")
        
        db = SessionLocal()
        try:
            # Créer le job
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
                deadline=datetime.strptime(job_data.deadline, "%Y-%m-%d").date() if job_data.deadline else None,
                applications_count=0
            )
            
            db.add(new_job)
            db.commit()
            db.refresh(new_job)

            # Ajouter les compétences via JobSkill
            skills_added = 0
            skills_errors = []

            if job_data.skills:
                print(f"🔧 BACKEND: Tentative d'ajout de {len(job_data.skills)} compétences pour le poste {new_job.id}")
                
                for i, skill_data in enumerate(job_data.skills):
                    try:
                        # Valider les données de compétence
                        if not skill_data.skill_name or not skill_data.skill_name.strip():
                            skills_errors.append(f"Compétence {i+1}: Nom manquant")
                            continue
                            
                        if skill_data.skill_level not in ['beginner', 'intermediate', 'advanced', 'expert']:
                            skills_errors.append(f"Compétence {skill_data.skill_name}: Niveau invalide")
                            continue
                        
                        # Vérifier les doublons
                        existing_skill = db.query(JobSkill).filter(
                            JobSkill.job_id == new_job.id,
                            JobSkill.skill_name.ilike(skill_data.skill_name.strip())
                        ).first()
                        
                        if existing_skill:
                            skills_errors.append(f"Compétence {skill_data.skill_name}: Déjà ajoutée")
                            continue
                        
                        job_skill = JobSkill(
                            job_id=new_job.id,
                            skill_name=skill_data.skill_name.strip(),
                            skill_level=skill_data.skill_level,
                            is_required=skill_data.is_required
                        )
                        
                        db.add(job_skill)
                        skills_added += 1
                        print(f"✅ BACKEND: Compétence ajoutée: {skill_data.skill_name} ({skill_data.skill_level}, {'Requis' if skill_data.is_required else 'Optionnel'})")
                        
                    except Exception as skill_error:
                        error_msg = f"Erreur ajout compétence {skill_data.skill_name}: {str(skill_error)}"
                        skills_errors.append(error_msg)
                        print(f"❌ BACKEND: {error_msg}")

            # Commit toutes les modifications
            db.commit()

            # Préparer le message de réponse
            message = f"Poste '{job_data.title}' créé avec succès"
            if skills_added > 0:
                message += f" avec {skills_added} compétence(s)"
            if skills_errors:
                message += f". Erreurs: {'; '.join(skills_errors[:3])}"

            return {
                "success": True,
                "message": message,
                "job_id": new_job.id,
                "skills_added": skills_added,
                "skills_errors": skills_errors
            }
        except Exception as e:
            db.rollback()
            print(f"❌ BACKEND: Erreur création poste: {str(e)}")
            return {"success": False, "message": f"Erreur lors de la création du poste: {str(e)}"}
        finally:
            db.close()
    except Exception as e:
        print(f"❌ BACKEND: Erreur interne: {str(e)}")
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
                
                # Get job skills
                job_skills = db.query(JobSkill).filter(
                    JobSkill.job_id == job.id
                ).all()
                
                skills_list = []
                for skill in job_skills:
                    skills_list.append({
                        "skill_name": skill.skill_name,
                        "skill_level": skill.skill_level,
                        "is_required": skill.is_required
                    })
                
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
                    "created_at": job.created_at.isoformat() if job.created_at else None,
                    "skills": skills_list
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
            
            # CORRECTION: Récupérer les compétences du job via JobSkill
            job_skills = db.query(JobSkill).filter(
                JobSkill.job_id == job.id
            ).all()
            
            skills_list = []
            for skill in job_skills:
                skills_list.append({
                    "skill_name": skill.skill_name,
                    "skill_level": skill.skill_level,
                    "is_required": skill.is_required
                })
            
            # Récupérer les candidatures avec les informations de recommandation
            applications = db.query(Application).filter(
                Application.job_id == job_id
            ).all()
            
            applications_list = []
            for app in applications:
                candidate = db.query(ProfileCandidat).filter(
                    ProfileCandidat.id == app.candidate_profile_id
                ).first()
                
                # Récupérer les informations de l'admin qui a recommandé
                recommended_by_admin = None
                if app.recommended_by_admin_id:
                    recommended_by_admin = db.query(HRAdmin).filter(
                        HRAdmin.id == app.recommended_by_admin_id
                    ).first()
                
                if candidate:
                    # Initialize quiz assignment status
                    quiz_assignment_status = None
                    
                    # Fetch quiz assignment status for this application
                    from models import JobQuizAssignment
                    quiz_assignment = db.query(JobQuizAssignment).filter(
                        JobQuizAssignment.job_id == job.id,
                        JobQuizAssignment.candidate_id == candidate.id
                    ).first()
                    
                    if quiz_assignment:
                        quiz_assignment_status = {
                            "assignment_id": quiz_assignment.id,
                            "status": quiz_assignment.status,
                            "quiz_attempt_id": quiz_assignment.quiz_attempt_id
                        }
                    
                    applications_list.append({
                        "id": app.id,
                        "name": candidate.name,
                        "title": candidate.title,
                        "status": app.status,
                        "application_date": app.application_date.isoformat() if app.application_date else None,
                        "hr_rating": float(app.hr_rating) if app.hr_rating else None,
                        "hr_notes": app.hr_notes,
                        "candidate_id": candidate.id,
                        # Informations de recommandation
                        "is_recommended": app.is_recommended or False,
                        "recommendation_priority": app.recommendation_priority,
                        "recommendation_comment": app.recommendation_comment,
                        "recommended_by": f"{recommended_by_admin.first_name} {recommended_by_admin.last_name}" if recommended_by_admin else None,
                        "recommendation_date": app.recommendation_date.isoformat() if app.recommendation_date else None,
                        "quiz_assignment_status": quiz_assignment_status
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
                "created_at": job.created_at.isoformat() if job.created_at else None,
                "skills": skills_list,  # Utiliser la liste des compétences récupérées
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
