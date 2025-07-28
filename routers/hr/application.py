from fastapi import APIRouter, Query, Depends
from databasehr.database import SessionLocal
from databasehr.models import Application, Job, ProfileCandidat, Contact, Employee, Department, Company, HRAdmin, AdminDepartments, JobSkill
from databasehr.session_manager import current_user_session
from company_utils import get_user_company
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, and_
from datetime import datetime, date
import json
from typing import Optional
from pydantic import BaseModel

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def calculate_skill_compatibility(candidate_skills, job_skills):
    """Calculate compatibility percentage between candidate and job skills"""
    if not job_skills:
        return 0
        
    # Parse candidate skills if they're stored as JSON string
    candidate_skills_list = []
    if candidate_skills:
        try:
            if isinstance(candidate_skills, str):
                parsed_skills = json.loads(candidate_skills)
            else:
                parsed_skills = candidate_skills
                
            if isinstance(parsed_skills, list):
                for skill in parsed_skills:
                    if isinstance(skill, str) and skill:
                        # Handle "Skill: Percentage" format
                        if ':' in skill:
                            candidate_skills_list.append(skill.split(':')[0].strip().lower())
                        else:
                            candidate_skills_list.append(skill.strip().lower())
        except (json.JSONDecodeError, Exception):
            candidate_skills_list = []
    
    # Count matching skills
    matched_skills = 0
    total_job_skills = len(job_skills)
    
    for job_skill in job_skills:
        job_skill_name = job_skill.skill_name.lower().strip()
        if job_skill_name in candidate_skills_list:
            matched_skills += 1
    
    # Calculate percentage
    compatibility_percentage = (matched_skills / total_job_skills) * 100 if total_job_skills > 0 else 0
    
    return round(compatibility_percentage)

class RecommendationRequest(BaseModel):
    comment: Optional[str] = ""
    priority: str = "normal"

@router.get("/api/applications")
async def get_applications(
    status_filter: Optional[str] = Query("all"),
    compatibility_filter: Optional[str] = Query("all"),
    db: Session = Depends(get_db)
):
    try:
        user_id = current_user_session.get('user_id')
        if not user_id:
            return {"success": False, "message": "Utilisateur non connecté"}
        
        company = get_user_company(user_id)
        if not company:
            return {"success": False, "message": "Aucune entreprise associée"}
        
        # Récupérer l'utilisateur actuel pour vérifier son rôle
        current_admin = db.query(HRAdmin).filter(HRAdmin.id == user_id).first()
        if not current_admin:
            return {"success": False, "message": "Utilisateur non trouvé"}
        
        # Base query with all necessary joins
        query = db.query(Application).join(
            Job, Application.job_id == Job.id
        ).join(
            ProfileCandidat, Application.candidate_profile_id == ProfileCandidat.id
        ).join(
            Contact, ProfileCandidat.contact_id == Contact.id
        ).join(
            Department, Job.department_id == Department.id
        ).filter(
            Job.company_id == company.id
        ).options(
            joinedload(Application.job).joinedload(Job.department),
            joinedload(Application.candidate_profile).joinedload(ProfileCandidat.contact),
            joinedload(Application.recommended_by_admin)
        )
        
        # Si c'est un chef de département, filtrer par ses départements assignés
        if current_admin.role == 'department_head':
            # Récupérer les départements assignés à ce chef
            assigned_dept_ids = db.query(AdminDepartments.department_id).filter(
                AdminDepartments.admin_id == user_id
            ).subquery()
            
            query = query.filter(Department.id.in_(assigned_dept_ids))
        
        # Apply status filter
        if status_filter and status_filter != "all":
            query = query.filter(Application.status == status_filter)
        
        applications = query.order_by(Application.application_date.desc()).all()
        
        applications_list = []
        for app in applications:
            # Get job skills for compatibility calculation
            job_skills = db.query(JobSkill).filter(JobSkill.job_id == app.job_id).all()
            
            # Calculate compatibility
            candidate_skills = app.candidate_profile.skills if app.candidate_profile else None
            compatibility_percentage = calculate_skill_compatibility(candidate_skills, job_skills)
            
            # Calculate days since application
            days_since = (datetime.now().date() - app.application_date.date()).days if app.application_date else 0
            
            # Count matched skills for detailed info
            matched_skills_count = 0
            if candidate_skills and job_skills:
                try:
                    if isinstance(candidate_skills, str):
                        parsed_skills = json.loads(candidate_skills)
                    else:
                        parsed_skills = candidate_skills
                    
                    if isinstance(parsed_skills, list):
                        candidate_skills_lower = []
                        for skill in parsed_skills:
                            if isinstance(skill, str) and skill:
                                if ':' in skill:
                                    candidate_skills_lower.append(skill.split(':')[0].strip().lower())
                                else:
                                    candidate_skills_lower.append(skill.strip().lower())
                        
                        for job_skill in job_skills:
                            if job_skill.skill_name.lower().strip() in candidate_skills_lower:
                                matched_skills_count += 1
                except:
                    matched_skills_count = 0
            
            # Build application data
            app_data = {
                "id": app.id,
                "candidate_id": app.candidate_profile_id,
                "candidate_name": app.candidate_profile.name if app.candidate_profile else "N/A",
                "candidate_title": app.candidate_profile.title if app.candidate_profile else "N/A",
                "candidate_email": app.candidate_profile.contact.email if app.candidate_profile and app.candidate_profile.contact else "N/A",
                "job_id": app.job_id,
                "job_title": app.job.title if app.job else "N/A",
                "department_name": app.job.department.name if app.job and app.job.department else "N/A",
                "status": app.status,
                "priority": app.job.priority if app.job else "normal",
                "application_date": app.application_date.isoformat() if app.application_date else None,
                "days_since_application": days_since,
                "hr_rating": float(app.hr_rating) if app.hr_rating else None,
                "hr_notes": app.hr_notes,
                "compatibility_percentage": compatibility_percentage,
                "matched_skills_count": matched_skills_count,
                "total_job_skills": len(job_skills),
                # Recommendation fields
                "is_recommended": app.is_recommended or False,
                "recommendation_priority": app.recommendation_priority,
                "recommendation_comment": app.recommendation_comment,
                "recommended_by": f"{app.recommended_by_admin.first_name} {app.recommended_by_admin.last_name}" if app.recommended_by_admin else None,
                "recommendation_date": app.recommendation_date.isoformat() if app.recommendation_date else None,
                "reviewed_by": app.reviewed_by,
                "reviewed_at": app.reviewed_at.isoformat() if app.reviewed_at else None
            }
            
            applications_list.append(app_data)
        
        # Apply compatibility filter
        if compatibility_filter and compatibility_filter != "all":
            original_count = len(applications_list)
            if compatibility_filter == "high":  # 75%+
                applications_list = [app for app in applications_list if app["compatibility_percentage"] >= 75]
            elif compatibility_filter == "medium":  # 50-74%
                applications_list = [app for app in applications_list if 50 <= app["compatibility_percentage"] < 75]
            elif compatibility_filter == "low":  # 25-49%
                applications_list = [app for app in applications_list if 25 <= app["compatibility_percentage"] < 50]
            elif compatibility_filter == "very_low":  # 0-24%
                applications_list = [app for app in applications_list if app["compatibility_percentage"] < 25]
        
        return {
            "success": True,
            "applications": applications_list,
            "total_count": len(applications_list)
        }
            
    except Exception as e:
        print(f"❌ Erreur lors de la récupération des candidatures: {str(e)}")
        import traceback
        traceback.print_exc()
        return {"success": False, "message": f"Erreur lors de la récupération des candidatures: {str(e)}"}

@router.post("/api/applications/{application_id}/recommend")
async def recommend_application(
    application_id: int, 
    recommendation_data: RecommendationRequest,
    db: Session = Depends(get_db)
):
    try:
        user_id = current_user_session.get('user_id')
        if not user_id:
            return {"success": False, "message": "Utilisateur non connecté"}
        
        # Vérifier que l'utilisateur est chef de département
        current_admin = db.query(HRAdmin).filter(HRAdmin.id == user_id).first()
        if not current_admin or current_admin.role != 'department_head':
            return {"success": False, "message": "Seuls les chefs de département peuvent recommander des candidatures"}
        
        company = get_user_company(user_id)
        if not company:
            return {"success": False, "message": "Aucune entreprise associée"}
        
        # Vérifier que la candidature appartient à un département géré par ce chef
        application = db.query(Application).join(
            Job, Application.job_id == Job.id
        ).join(
            Department, Job.department_id == Department.id
        ).filter(
            Application.id == application_id,
            Job.company_id == company.id
        ).first()
        
        if not application:
            return {"success": False, "message": "Candidature non trouvée"}
        
        # Vérifier que le chef a accès à ce département
        assigned_dept_ids = [dept.department_id for dept in db.query(AdminDepartments.department_id).filter(
            AdminDepartments.admin_id == user_id
        ).all()]
        
        job = db.query(Job).filter(Job.id == application.job_id).first()
        if job.department_id not in assigned_dept_ids:
            return {"success": False, "message": "Vous n'avez pas accès à ce département"}
        
        # Récupérer le candidat pour le nom
        candidate = db.query(ProfileCandidat).filter(
            ProfileCandidat.id == application.candidate_profile_id
        ).first()
        
        if not candidate:
            return {"success": False, "message": "Candidat non trouvé"}
        
        # Mettre à jour la candidature avec la recommandation
        application.is_recommended = True
        application.recommended_by_admin_id = user_id
        application.recommendation_comment = recommendation_data.comment
        application.recommendation_priority = recommendation_data.priority
        application.recommendation_date = datetime.now()
        
        # Mettre à jour les notes HR avec les informations de recommandation
        recommendation_note = f"RECOMMANDÉ par {current_admin.first_name} {current_admin.last_name} (Chef de département)\n"
        recommendation_note += f"Priorité: {recommendation_data.priority.upper()}\n"
        if recommendation_data.comment:
            recommendation_note += f"Commentaire: {recommendation_data.comment}\n"
        recommendation_note += f"Date de recommandation: {datetime.now().strftime('%d/%m/%Y %H:%M')}"
        
        application.hr_notes = recommendation_note
        
        db.commit()
        
        return {
            "success": True,
            "message": f"Candidature de {candidate.name} recommandée avec succès aux recruteurs et super admins"
        }
            
    except Exception as e:
        db.rollback()
        return {"success": False, "message": f"Erreur lors de la recommandation: {str(e)}"}

@router.get("/api/application/{application_id}/compatibility")
async def get_application_compatibility_details(
    application_id: int, 
    db: Session = Depends(get_db)
):
    try:
        user_id = current_user_session.get('user_id')
        if not user_id:
            return {"success": False, "message": "Utilisateur non connecté"}
        
        company = get_user_company(user_id)
        if not company:
            return {"success": False, "message": "Aucune entreprise associée"}
        
        # Get application with related data
        application = db.query(Application).join(
            Job, Application.job_id == Job.id
        ).filter(
            Application.id == application_id,
            Job.company_id == company.id
        ).first()
        
        if not application:
            return {"success": False, "message": "Candidature non trouvée"}
        
        # Get job skills
        job_skills = db.query(JobSkill).filter(JobSkill.job_id == application.job_id).all()
        
        # Get candidate skills
        candidate = db.query(ProfileCandidat).filter(
            ProfileCandidat.id == application.candidate_profile_id
        ).first()
        
        if not candidate:
            return {"success": False, "message": "Candidat non trouvé"}
        
        # Parse candidate skills
        candidate_skills_list = []
        if candidate.skills:
            try:
                if isinstance(candidate.skills, str):
                    parsed_skills = json.loads(candidate.skills)
                else:
                    parsed_skills = candidate.skills
                
                if isinstance(parsed_skills, list):
                    for skill in parsed_skills:
                        if isinstance(skill, str) and skill:
                            if ':' in skill:
                                candidate_skills_list.append(skill.split(':')[0].strip())
                            else:
                                candidate_skills_list.append(skill.strip())
            except (json.JSONDecodeError, Exception):
                candidate_skills_list = []
        
        # Categorize skills
        matched_skills = []
        missing_skills = []
        
        for job_skill in job_skills:
            skill_match = {
                "skill_name": job_skill.skill_name,
                "skill_level": job_skill.skill_level,
                "is_required": job_skill.is_required
            }
            
            if job_skill.skill_name.lower().strip() in [s.lower() for s in candidate_skills_list]:
                matched_skills.append(skill_match)
            else:
                missing_skills.append(skill_match)
        
        compatibility_percentage = calculate_skill_compatibility(candidate.skills, job_skills)
        
        return {
            "success": True,
            "compatibility_percentage": compatibility_percentage,
            "matched_skills": matched_skills,
            "missing_skills": missing_skills,
            "candidate_skills": candidate_skills_list,
            "total_job_skills": len(job_skills),
            "matched_count": len(matched_skills),
            "missing_count": len(missing_skills)
        }
            
    except Exception as e:
        print(f"❌ Erreur lors de la récupération des détails de compatibilité: {str(e)}")
        return {"success": False, "message": f"Erreur: {str(e)}"}

@router.post("/api/applications/{application_id}/update-status")
async def update_application_status(
    application_id: int, 
    status_data: dict,
    db: Session = Depends(get_db)
):
    try:
        user_id = current_user_session.get('user_id')
        if not user_id:
            return {"success": False, "message": "Utilisateur non connecté"}
        
        company = get_user_company(user_id)
        if not company:
            return {"success": False, "message": "Aucune entreprise associée"}
        
        # Récupérer l'utilisateur actuel pour vérifier son rôle
        current_admin = db.query(HRAdmin).filter(HRAdmin.id == user_id).first()
        if not current_admin:
            return {"success": False, "message": "Utilisateur non trouvé"}
        
        # RESTRICTION: Les chefs de département ne peuvent que recommander
        if current_admin.role == 'department_head':
            return {"success": False, "message": "Les chefs de département utilisent la fonction 'Recommander' et ne peuvent pas changer le statut directement"}
        
        # Construire la requête avec vérification des permissions
        query = db.query(Application).join(
            Job, Application.job_id == Job.id
        ).join(
            Department, Job.department_id == Department.id
        ).filter(
            Application.id == application_id,
            Job.company_id == company.id
        )
        
        # Si c'est un chef de département, vérifier qu'il a accès à cette candidature
        if current_admin.role == 'department_head':
            assigned_dept_ids = db.query(AdminDepartments.department_id).filter(
                AdminDepartments.admin_id == user_id
            ).subquery()
            
            query = query.filter(Department.id.in_(assigned_dept_ids))
        
        application = query.first()
        
        if not application:
            return {"success": False, "message": "Candidature non trouvée ou accès non autorisé"}
        
        new_status = status_data.get('status')
        if not new_status:
            return {"success": False, "message": "Statut manquant"}
        
        job = db.query(Job).filter(Job.id == application.job_id).first()
        candidate = db.query(ProfileCandidat).filter(
            ProfileCandidat.id == application.candidate_profile_id
        ).first()
        contact = db.query(Contact).filter(
            Contact.id == candidate.contact_id
        ).first() if candidate and candidate.contact_id else None
        
        # Logique d'acceptation (seulement pour recruteurs et super admins)
        if new_status == 'accepted' and current_admin.role in ['recruiter', 'super_admin'] and job and candidate and contact:
            try:
                # Create new employee
                employee_id = f"EMP{datetime.now().strftime('%Y%m%d%H%M%S')}"
                salary = None
                if job.salary_min and job.salary_max:
                    salary = (job.salary_min + job.salary_max) / 2
                elif job.salary_min:
                    salary = job.salary_min
                elif job.salary_max:
                    salary = job.salary_max
                
                new_employee = Employee(
                    first_name=candidate.first_name,
                    last_name=candidate.last_name,
                    email=contact.email,
                    department_id=job.department_id,
                    company_id=job.company_id,
                    position=job.title,
                    employment_type=job.employment_type,
                    hire_date=datetime.utcnow().date(),
                    status="active",
                    candidate_profile_id=candidate.id
                )
                
                db.add(new_employee)
                db.flush()
                
                # Update job status
                job.status = 'filled'
                job.assigned_employee_id = new_employee.id
                
                # Update application
                application.status = new_status
                application.reviewed_by = user_id
                application.reviewed_at = datetime.now()
                application.decision_date = datetime.now()
                application.decision_reason = f"Candidature acceptée - Embauché comme {job.title}"
                
                if status_data.get('hr_notes'):
                    application.hr_notes = status_data['hr_notes']
                if status_data.get('hr_rating'):
                    application.hr_rating = float(status_data['hr_rating'])
                
                # Reject other applications for the same job
                other_applications = db.query(Application).filter(
                    Application.job_id == job.id,
                    Application.id != application_id,
                    Application.status.in_(['pending', 'reviewed', 'interview_scheduled'])
                ).all()
                
                for other_app in other_applications:
                    other_app.status = 'rejected'
                    other_app.decision_reason = f"Poste pourvu par {candidate.name}"
                    other_app.decision_date = datetime.now()
                    other_app.reviewed_by = user_id
                    other_app.reviewed_at = datetime.now()
                
                db.commit()
                
                return {
                    "success": True,
                    "message": f"Candidature acceptée ! {candidate.name} a été automatiquement ajouté comme employé.",
                    "application": {
                        "id": application.id,
                        "status": application.status,
                        "reviewed_at": application.reviewed_at.isoformat() if application.reviewed_at else None
                    },
                    "employee_created": {
                        "id": new_employee.id,
                        "employee_id": new_employee.employee_id,
                        "name": f"{new_employee.first_name} {new_employee.last_name}",
                        "position": new_employee.position,
                        "department_id": new_employee.department_id
                    }
                }
            except Exception as e:
                db.rollback()
                # Fallback to simple status update if employee creation fails
                application.status = new_status
                application.reviewed_by = user_id
                application.reviewed_at = datetime.now()
                db.commit()
                return {
                    "success": True,
                    "message": f"Candidature mise à jour vers '{new_status}' (création employé échouée: {str(e)})",
                    "application": {
                        "id": application.id,
                        "status": application.status,
                        "reviewed_at": application.reviewed_at.isoformat() if application.reviewed_at else None
                    }
                }
        else:
            # For other status updates
            application.status = new_status
            application.reviewed_by = user_id
            application.reviewed_at = datetime.now()
            
            if status_data.get('hr_notes'):
                application.hr_notes = status_data['hr_notes']
            if status_data.get('hr_rating'):
                application.hr_rating = float(status_data['hr_rating'])
            
            db.commit()
            
            return {
                "success": True,
                "message": f"Candidature mise à jour vers '{new_status}'",
                "application": {
                    "id": application.id,
                    "status": application.status,
                    "reviewed_at": application.reviewed_at.isoformat() if application.reviewed_at else None
                }
            }
    except Exception as e:
        db.rollback()
        return {"success": False, "message": f"Erreur lors de la mise à jour: {str(e)}"}

@router.post("/api/applications/create-demo")
async def create_demo_applications(db: Session = Depends(get_db)):
    try:
        user_id = current_user_session.get('user_id')
        if not user_id:
            return {"success": False, "message": "Utilisateur non connecté"}
        
        company = get_user_company(user_id)
        if not company:
            return {"success": False, "message": "Aucune entreprise associée"}
        
        # Récupérer l'utilisateur actuel pour vérifier son rôle
        current_admin = db.query(HRAdmin).filter(HRAdmin.id == user_id).first()
        if not current_admin:
            return {"success": False, "message": "Utilisateur non trouvé"}
        
        # Construire la requête pour les jobs selon le rôle
        jobs_query = db.query(Job).join(
            Department, Job.department_id == Department.id
        ).filter(
            Job.company_id == company.id,
            Job.status.in_(['active', 'draft'])
        )
        
        # Si c'est un chef de département, filtrer par ses départements assignés
        if current_admin.role == 'department_head':
            assigned_dept_ids = db.query(AdminDepartments.department_id).filter(
                AdminDepartments.admin_id == user_id
            ).subquery()
            
            jobs_query = jobs_query.filter(Department.id.in_(assigned_dept_ids))
        
        jobs = jobs_query.limit(3).all()
        
        if not jobs:
            return {"success": False, "message": "Aucun poste disponible"}
        
        candidates = db.query(ProfileCandidat).limit(5).all()
        
        if not candidates:
            return {"success": False, "message": "Aucun profil candidat disponible"}
        
        demo_applications = []
        statuses = ['pending', 'reviewed', 'interview_scheduled', 'pending', 'reviewed']
        
        for i, job in enumerate(jobs):
            for j in range(min(2, len(candidates))):
                candidate = candidates[j + i]
                status = statuses[(i + j) % len(statuses)]
                
                existing = db.query(Application).filter(
                    Application.job_id == job.id,
                    Application.candidate_profile_id == candidate.id
                ).first()
                
                if not existing:
                    new_application = Application(
                        job_id=job.id,
                        candidate_profile_id=candidate.id,
                        status=status,
                        application_date=datetime.now(),
                        hr_rating=4.2 if status == 'reviewed' else None,
                        hr_notes=f"Candidature intéressante pour le poste de {job.title}" if status == 'reviewed' else None,
                        source="Site web",
                        is_recommended=False
                    )
                    
                    db.add(new_application)
                    demo_applications.append({
                        "job_title": job.title,
                        "candidate_name": candidate.name,
                        "status": status
                    })
        
        db.commit()
        
        return {
            "success": True,
            "message": f"{len(demo_applications)} candidatures de démonstration créées",
            "applications": demo_applications
        }
    except Exception as e:
        db.rollback()
        return {"success": False, "message": f"Erreur lors de la création: {str(e)}"}