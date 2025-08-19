from fastapi import APIRouter, Query, Depends
from databasehr.database import SessionLocal
from databasehr.models import Application, Job, ProfileCandidat, Contact, Employee, Department, Company, HRAdmin, AdminDepartments
from databasehr.models import Application, Job, ProfileCandidat, Contact, Department, JobSkill, Company
from databasehr.session_manager import current_user_session
from company_utils import get_user_company
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, and_
from datetime import datetime, date
import json
from typing import Optional
from pydantic import BaseModel
from quiz_service import QuizService


router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def calculate_skill_compatibility(candidate_skills, job_skills):
    """Calculate compatibility percentage between candidate and job skills"""
    print(f"🔍 BACKEND: Starting compatibility calculation")
    print(f"📊 BACKEND: Job skills count: {len(job_skills) if job_skills else 0}")
    print(f"📊 BACKEND: Candidate skills: {candidate_skills}")
    
    if not job_skills:
        print("⚠️ BACKEND: No job skills found, returning 0%")
        return 0, 0, len(job_skills) if job_skills else 0
    
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
                            skill_name = skill.split(':')[0].strip().lower()
                            candidate_skills_list.append(skill_name)
                        else:
                            candidate_skills_list.append(skill.strip().lower())
                    elif isinstance(skill, dict) and 'name' in skill:
                        # Handle object format
                        candidate_skills_list.append(skill['name'].strip().lower())
        except (json.JSONDecodeError, Exception) as e:
            print(f"❌ BACKEND: Error parsing candidate skills: {e}")
            candidate_skills_list = []
    
    print(f"📋 BACKEND: Parsed candidate skills: {candidate_skills_list}")
    
    # Count matching skills
    matched_skills = 0
    total_job_skills = len(job_skills)
    matched_skill_names = []
    
    for job_skill in job_skills:
        job_skill_name = job_skill.skill_name.lower().strip()
        print(f"🔍 BACKEND: Checking job skill: '{job_skill_name}'")
        
        if job_skill_name in candidate_skills_list:
            matched_skills += 1
            matched_skill_names.append(job_skill.skill_name)
            print(f"✅ BACKEND: Match found for: '{job_skill.skill_name}'")
        else:
            print(f"❌ BACKEND: No match for: '{job_skill.skill_name}'")
    
    # Calculate percentage
    compatibility_percentage = (matched_skills / total_job_skills) * 100 if total_job_skills > 0 else 0
    
    print(f"📊 BACKEND: Final calculation:")
    print(f"   - Matched skills: {matched_skills}")
    print(f"   - Total job skills: {total_job_skills}")
    print(f"   - Compatibility: {compatibility_percentage}%")
    print(f"   - Matched skill names: {matched_skill_names}")
    
    return round(compatibility_percentage), matched_skills, total_job_skills

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

        print(f"🔍 BACKEND: Loading applications for company {company.id}")
        print(f"👤 BACKEND: Current user: {current_admin.first_name} {current_admin.last_name} ({current_admin.role})")

        # Construire la requête de base avec eager loading
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
            joinedload(Application.candidate_profile).joinedload(ProfileCandidat.contact)
        )

        # Si c'est un chef de département, filtrer par ses départements assignés
        if current_admin.role == 'department_head':
            print(f"🔒 Chef de département - Filtrage des candidatures pour: {current_admin.first_name} {current_admin.last_name}")

            assigned_dept_ids = db.query(AdminDepartments.department_id).filter(
                AdminDepartments.admin_id == user_id
            ).subquery()

            query = query.filter(Department.id.in_(assigned_dept_ids))
            print("📋 Filtrage appliqué pour les départements assignés")
        else:
            print(f"👑 Admin/Recruteur - Accès à toutes les candidatures: {current_admin.role}")

        # Appliquer le filtre de statut
        if status_filter and status_filter != "all":
            query = query.filter(Application.status == status_filter)

        applications = query.order_by(Application.application_date.desc()).all()
        print(f"📊 BACKEND: Found {len(applications)} applications")

        applications_list = []
        for app in applications:
            job = app.job
            department = job.department if job else None
            candidate = app.candidate_profile
            contact = candidate.contact if candidate else None

            print(f"\n🔍 BACKEND: Processing application {app.id}")
            print(f"   - Job: {job.title if job else 'N/A'}")
            print(f"   - Candidate: {candidate.name if candidate else 'N/A'}")

            # CORRECTION: Récupérer les compétences du job via la relation JobSkill
            job_skills = []
            if job:
                job_skills = db.query(JobSkill).filter(JobSkill.job_id == job.id).all()
            
            candidate_skills = candidate.skills if candidate else None
            
            print(f"   - Job skills found: {len(job_skills)}")
            print(f"   - Job skills: {[skill.skill_name for skill in job_skills]}")
            print(f"   - Candidate skills raw: {candidate_skills}")
            
            # Utiliser la fonction de calcul de compatibilité
            compatibility_percentage, matched_skills_count, total_job_skills = calculate_skill_compatibility(candidate_skills, job_skills)
            
            print(f"   - Compatibility result: {compatibility_percentage}% ({matched_skills_count}/{total_job_skills})")

            # Appliquer filtre de compatibilité si précisé
            if compatibility_filter != "all":
                try:
                    if compatibility_filter == "high" and compatibility_percentage < 75:
                        continue
                    elif compatibility_filter == "medium" and not (50 <= compatibility_percentage < 75):
                        continue
                    elif compatibility_filter == "low" and not (25 <= compatibility_percentage < 50):
                        continue
                    elif compatibility_filter == "very_low" and compatibility_percentage >= 25:
                        continue
                except ValueError:
                    pass  # Ignore invalid threshold input

            # Récupérer les informations de recommandation
            recommended_by_admin = None
            if app.recommended_by_admin_id:
                recommended_by_admin = db.query(HRAdmin).filter(
                    HRAdmin.id == app.recommended_by_admin_id
                ).first()

            days_since_application = (datetime.now() - app.application_date).days if app.application_date else 0

            applications_list.append({
                "id": app.id,
                "job_id": job.id,
                "job_title": job.title,
                "department_name": department.name if department else "N/A",
                "candidate_id": candidate.id if candidate else None,
                "candidate_name": candidate.name if candidate else "N/A",
                "candidate_title": candidate.title if candidate else "N/A",
                "candidate_email": contact.email if contact else "N/A",
                "status": app.status,
                "application_date": app.application_date.isoformat() if app.application_date else None,
                "days_since_application": days_since_application,
                "hr_rating": float(app.hr_rating) if app.hr_rating else None,
                "hr_notes": app.hr_notes,
                "priority": job.priority,
                "reviewed_by": app.reviewed_by,
                "reviewed_at": app.reviewed_at.isoformat() if app.reviewed_at else None,
                "is_recommended": app.is_recommended or False,
                "recommendation_priority": app.recommendation_priority,
                "recommendation_comment": app.recommendation_comment,
                "recommended_by": f"{recommended_by_admin.first_name} {recommended_by_admin.last_name}" if recommended_by_admin else None,
                "recommendation_date": app.recommendation_date.isoformat() if app.recommendation_date else None,
                # Utiliser les valeurs calculées correctement
                "compatibility_percentage": compatibility_percentage,
                "matched_skills_count": matched_skills_count,
                "total_job_skills": total_job_skills
            })

        print(f"✅ BACKEND: {len(applications_list)} candidatures récupérées pour l'utilisateur {current_admin.role}")
        
        # Log des scores de compatibilité pour debug
        for app in applications_list:
            print(f"📊 BACKEND: App {app['id']}: {app['compatibility_percentage']}% ({app['matched_skills_count']}/{app['total_job_skills']})")
        
        return {
            "success": True,
            "applications": applications_list,
            "total": len(applications_list)
        }

    except Exception as e:
        import traceback
        print(f"❌ BACKEND: Erreur interne: {str(e)}")
        print(f"❌ BACKEND: Traceback: {traceback.format_exc()}")
        return {"success": False, "message": f"Erreur interne du serveur: {str(e)}"}

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

        print(f"🔍 BACKEND: Loading applications for company {company.id}")
        print(f"👤 BACKEND: Current user: {current_admin.first_name} {current_admin.last_name} ({current_admin.role})")

        # Construire la requête de base avec eager loading
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
            joinedload(Application.candidate_profile).joinedload(ProfileCandidat.contact)
        )

        # Si c'est un chef de département, filtrer par ses départements assignés
        if current_admin.role == 'department_head':
            print(f"🔒 Chef de département - Filtrage des candidatures pour: {current_admin.first_name} {current_admin.last_name}")

            assigned_dept_ids = db.query(AdminDepartments.department_id).filter(
                AdminDepartments.admin_id == user_id
            ).subquery()

            query = query.filter(Department.id.in_(assigned_dept_ids))
            print("📋 Filtrage appliqué pour les départements assignés")
        else:
            print(f"👑 Admin/Recruteur - Accès à toutes les candidatures: {current_admin.role}")

        # Appliquer le filtre de statut
        if status_filter and status_filter != "all":
            query = query.filter(Application.status == status_filter)

        applications = query.order_by(Application.application_date.desc()).all()
        print(f"📊 BACKEND: Found {len(applications)} applications")

        applications_list = []
        for app in applications:
            job = app.job
            department = job.department if job else None
            candidate = app.candidate_profile
            contact = candidate.contact if candidate else None

            print(f"\n🔍 BACKEND: Processing application {app.id}")
            print(f"   - Job: {job.title if job else 'N/A'}")
            print(f"   - Candidate: {candidate.name if candidate else 'N/A'}")

            # CORRECTION: Récupérer les compétences du job pour le calcul de compatibilité
            job_skills = db.query(JobSkill).filter(JobSkill.job_id == job.id).all() if job else []
            candidate_skills = candidate.skills if candidate else None
            
            print(f"   - Job skills found: {len(job_skills)}")
            print(f"   - Job skills: {[skill.skill_name for skill in job_skills]}")
            print(f"   - Candidate skills raw: {candidate_skills}")
            
            # CORRECTION: Utiliser la fonction améliorée qui retourne plus d'informations
            compatibility_percentage, matched_skills_count, total_job_skills = calculate_skill_compatibility(candidate_skills, job_skills)
            
            print(f"   - Compatibility result: {compatibility_percentage}% ({matched_skills_count}/{total_job_skills})")

            # Appliquer filtre de compatibilité si précisé
            if compatibility_filter != "all":
                try:
                    if compatibility_filter == "high" and compatibility_percentage < 75:
                        continue
                    elif compatibility_filter == "medium" and not (50 <= compatibility_percentage < 75):
                        continue
                    elif compatibility_filter == "low" and not (25 <= compatibility_percentage < 50):
                        continue
                    elif compatibility_filter == "very_low" and compatibility_percentage >= 25:
                        continue
                except ValueError:
                    pass  # Ignore invalid threshold input

            # Récupérer les informations de recommandation
            recommended_by_admin = None
            if app.recommended_by_admin_id:
                recommended_by_admin = db.query(HRAdmin).filter(
                    HRAdmin.id == app.recommended_by_admin_id
                ).first()

            days_since_application = (datetime.now() - app.application_date).days if app.application_date else 0

            applications_list.append({
                "id": app.id,
                "job_id": job.id,
                "job_title": job.title,
                "department_name": department.name if department else "N/A",
                "candidate_id": candidate.id if candidate else None,
                "candidate_name": candidate.name if candidate else "N/A",
                "candidate_title": candidate.title if candidate else "N/A",
                "candidate_email": contact.email if contact else "N/A",
                "status": app.status,
                "application_date": app.application_date.isoformat() if app.application_date else None,
                "days_since_application": days_since_application,
                "hr_rating": float(app.hr_rating) if app.hr_rating else None,
                "hr_notes": app.hr_notes,
                "priority": job.priority,
                "reviewed_by": app.reviewed_by,
                "reviewed_at": app.reviewed_at.isoformat() if app.reviewed_at else None,
                "is_recommended": app.is_recommended or False,
                "recommendation_priority": app.recommendation_priority,
                "recommendation_comment": app.recommendation_comment,
                "recommended_by": f"{recommended_by_admin.first_name} {recommended_by_admin.last_name}" if recommended_by_admin else None,
                "recommendation_date": app.recommendation_date.isoformat() if app.recommendation_date else None,
                # CORRECTION: Utiliser les valeurs calculées correctement
                "compatibility_percentage": compatibility_percentage,
                "matched_skills_count": matched_skills_count,
                "total_job_skills": total_job_skills
            })

        print(f"✅ BACKEND: {len(applications_list)} candidatures récupérées pour l'utilisateur {current_admin.role}")
        
        # Log des scores de compatibilité pour debug
        for app in applications_list:
            print(f"📊 BACKEND: App {app['id']}: {app['compatibility_percentage']}% ({app['matched_skills_count']}/{app['total_job_skills']})")
        
        return {
            "success": True,
            "applications": applications_list,
            "total": len(applications_list)
        }

    except Exception as e:
        import traceback
        print(f"❌ BACKEND: Erreur interne: {str(e)}")
        print(f"❌ BACKEND: Traceback: {traceback.format_exc()}")
        return {"success": False, "message": f"Erreur interne du serveur: {str(e)}"}

@router.get("/api/application/{application_id}/compatibility")
async def get_application_compatibility_details(application_id: int, db: Session = Depends(get_db)):
    try:
        user_id = current_user_session.get('user_id')
        if not user_id:
            return {"success": False, "message": "Utilisateur non connecté"}

        # Vérifier l'utilisateur et ses rôles
        current_admin = db.query(HRAdmin).filter(HRAdmin.id == user_id).first()
        if not current_admin:
            return {"success": False, "message": "Utilisateur non trouvé"}

        company = get_user_company(user_id)
        if not company:
            return {"success": False, "message": "Aucune entreprise associée"}

        # Vérifier que la candidature appartient à l'entreprise
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

        # Si chef de département, vérifier l'accès au département
        if current_admin.role == 'department_head':
            assigned_dept_ids = db.query(AdminDepartments.department_id).filter(
                AdminDepartments.admin_id == user_id
            ).all()
            dept_ids = [d.department_id for d in assigned_dept_ids]
            job = db.query(Job).filter(Job.id == application.job_id).first()
            if job.department_id not in dept_ids:
                return {"success": False, "message": "Vous n'avez pas accès à ce département"}

        # CORRECTION: Récupérer les compétences du poste via JobSkill
        job_skills = db.query(JobSkill).filter(JobSkill.job_id == application.job_id).all()

        # Récupérer le candidat
        candidate = db.query(ProfileCandidat).filter(
            ProfileCandidat.id == application.candidate_profile_id
        ).first()

        if not candidate:
            return {"success": False, "message": "Candidat non trouvé"}

        # Parser les compétences du candidat
        candidate_skills_list = []
        if candidate.skills:
            try:
                parsed_skills = json.loads(candidate.skills) if isinstance(candidate.skills, str) else candidate.skills
                if isinstance(parsed_skills, list):
                    for skill in parsed_skills:
                        if isinstance(skill, str) and skill:
                            if ':' in skill:
                                candidate_skills_list.append(skill.split(':')[0].strip())
                            else:
                                candidate_skills_list.append(skill.strip())
            except (json.JSONDecodeError, Exception):
                candidate_skills_list = []

        # Analyser les correspondances
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

        compatibility_percentage, matched_count, total_skills = calculate_skill_compatibility(candidate.skills, job_skills)

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
        print(f"❌ BACKEND: Erreur lors de la récupération des détails de compatibilité: {str(e)}")
        return {"success": False, "message": f"Erreur: {str(e)}"}

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

        # Vérifier que l'utilisateur est un chef de département
        current_admin = db.query(HRAdmin).filter(HRAdmin.id == user_id).first()
        if not current_admin or current_admin.role != 'department_head':
            return {"success": False, "message": "Seuls les chefs de département peuvent recommander des candidatures"}

        # Récupérer la candidature
        app = db.query(Application).filter(Application.id == application_id).first()
        if not app:
            return {"success": False, "message": "Candidature non trouvée"}

        # Vérifier que la candidature appartient à un département géré par ce chef
        company = get_user_company(user_id)
        if not company:
            return {"success": False, "message": "Aucune entreprise associée"}

        # Vérifier l'accès au département
        job = db.query(Job).filter(Job.id == app.job_id).first()
        if not job or job.company_id != company.id:
            return {"success": False, "message": "Candidature non trouvée dans votre entreprise"}

        assigned_dept_ids = db.query(AdminDepartments.department_id).filter(
            AdminDepartments.admin_id == user_id
        ).all()
        dept_ids = [d.department_id for d in assigned_dept_ids]
        
        if job.department_id not in dept_ids:
            return {"success": False, "message": "Vous n'avez pas accès à ce département"}

        # Mettre à jour la candidature avec la recommandation
        app.is_recommended = True
        app.recommended_by_admin_id = user_id
        app.recommendation_comment = recommendation_data.comment
        app.recommendation_priority = recommendation_data.priority
        app.recommendation_date = datetime.now()

        db.commit()

        return {
            "success": True,
            "message": f"Candidature recommandée avec succès (priorité: {recommendation_data.priority})"
        }

    except Exception as e:
        db.rollback()
        import traceback
        print(f"❌ BACKEND: Erreur recommandation: {str(e)}")
        print(f"❌ BACKEND: Traceback: {traceback.format_exc()}")
        return {"success": False, "message": f"Erreur lors de la recommandation: {str(e)}"}
@router.post("/api/applications/{application_id}/update-status")
async def update_application_status(application_id: int, status_data: dict):
    try:
        user_id = current_user_session.get('user_id')
        if not user_id:
            return {"success": False, "message": "Utilisateur non connecté"}

        company = get_user_company(user_id)
        if not company:
            return {"success": False, "message": "Aucune entreprise associée"}

        db = SessionLocal()
        try:
            current_admin = db.query(HRAdmin).filter(HRAdmin.id == user_id).first()
            if not current_admin:
                return {"success": False, "message": "Utilisateur non trouvé"}

            if current_admin.role == 'department_head':
                return {
                    "success": False,
                    "message": "Les chefs de département utilisent la fonction 'Recommander' et ne peuvent pas changer le statut directement"
                }

            query = db.query(Application).join(
                Job, Application.job_id == Job.id
            ).join(
                Department, Job.department_id == Department.id
            ).filter(
                Application.id == application_id,
                Job.company_id == company.id
            )

            application = query.first()
            if not application:
                return {"success": False, "message": "Candidature non trouvée ou accès non autorisé"}

            new_status = status_data.get('status')
            if not new_status:
                return {"success": False, "message": "Statut manquant"}

            # Accepté → créer employé, mettre à jour le poste et rejeter les autres
            if new_status == 'accepted' and current_admin.role in ['recruiter', 'super_admin']:
                candidate = db.query(ProfileCandidat).filter(ProfileCandidat.id == application.candidate_profile_id).first()
                job = db.query(Job).filter(Job.id == application.job_id).first()
                contact = db.query(Contact).filter(Contact.id == candidate.contact_id).first() if candidate else None

                if candidate and job and contact:
                    try:
                        employee_id = f"EMP{datetime.now().strftime('%Y%m%d%H%M%S')}"
                        salary = (
                            (job.salary_min + job.salary_max) / 2
                            if job.salary_min and job.salary_max else
                            job.salary_min or job.salary_max or 0
                        )

                        new_employee = Employee(
                            employee_id=employee_id,
                            first_name=candidate.first_name,
                            last_name=candidate.last_name,
                            email=candidate.email,
                            department_id=job.department_id,
                            company_id=job.company_id,
                            position=job.title,
                            employment_type=job.employment_type,
                            hire_date=datetime.utcnow().date(),
                            status="active",
                            candidate_profile_id=candidate.id,
                            salary=salary
                        )

                        db.add(new_employee)
                        db.flush()

                        # Mettre à jour le job
                        job.status = 'filled'
                        job.assigned_employee_id = new_employee.id

                        # Mettre à jour la candidature
                        application.status = new_status
                        application.reviewed_by = user_id
                        application.reviewed_at = datetime.now()
                        application.decision_date = datetime.now()
                        application.decision_reason = f"Candidature acceptée - Embauché comme {job.title}"

                        if status_data.get('hr_notes'):
                            application.hr_notes = status_data['hr_notes']
                        if status_data.get('hr_rating'):
                            application.hr_rating = float(status_data['hr_rating'])

                        # Rejeter les autres candidatures
                        other_applications = db.query(Application).filter(
                            Application.job_id == job.id,
                            Application.id != application.id,
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
                            "message": f"Candidature acceptée ! {candidate.name} a été ajouté comme employé.",
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
                        # fallback: mise à jour du statut uniquement
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

            # Autres statuts
            else:
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
        finally:
            db.close()

    except Exception as e:
        return {"success": False, "message": f"Erreur interne du serveur: {str(e)}"}


@router.post("/api/applications/create-demo")
async def create_demo_applications():
    try:
        user_id = current_user_session.get('user_id')
        if not user_id:
            return {"success": False, "message": "Utilisateur non connecté"}
        
        company = get_user_company(user_id)
        if not company:
            return {"success": False, "message": "Aucune entreprise associée"}
        
        db = SessionLocal()
        try:
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
        finally:
            db.close()
    except Exception as e:
        return {"success": False, "message": f"Erreur interne du serveur: {str(e)}"}

@router.post("/api/accept-application/{application_id}")
def accept_application(application_id: int):
    db = SessionLocal()
    try:
        user_id = current_user_session.get('user_id')
        if not user_id:
            return {"success": False, "message": "Utilisateur non connecté"}
        
        # Récupérer l'utilisateur actuel pour vérifier son rôle
        current_admin = db.query(HRAdmin).filter(HRAdmin.id == user_id).first()
        if not current_admin:
            return {"success": False, "message": "Utilisateur non trouvé"}
        
        # RESTRICTION: Les chefs de département ne peuvent pas accepter directement
        if current_admin.role == 'department_head':
            return {"success": False, "message": "Les chefs de département ne peuvent pas accepter directement les candidatures. Veuillez utiliser la fonction 'Recommander'."}
        
        # Construire la requête avec vérification des permissions
        application_query = db.query(Application).join(
            Job, Application.job_id == Job.id
        ).join(
            Department, Job.department_id == Department.id
        ).filter(Application.id == application_id)
        
        application = application_query.first()
        if not application:
            return {"success": False, "message": "Candidature non trouvée ou accès non autorisé"}
        
        application.status = "accepted"
        application.decision_date = datetime.now()
        db.commit()

        profile = db.query(ProfileCandidat).filter(ProfileCandidat.id == application.candidate_profile_id).first()
        job = db.query(Job).filter(Job.id == application.job_id).first()
        company = db.query(Company).filter(Company.id == job.company_id).first()
        
        if not profile or not job or not company:
            return {"success": False, "message": "Impossible de récupérer les informations"}
        
        existing_emp = db.query(Employee).filter(Employee.email == profile.contact.email).first()
        if existing_emp:
            return {"success": True, "message": "Candidat déjà employé"}
        
        new_emp = Employee(
            company_id=company.id,
            department_id=job.department_id,
            employee_id=f"EMP{datetime.now().strftime('%Y%m%d%H%M%S')}",
            first_name=profile.name.split(" ")[0],
            last_name=" ".join(profile.name.split(" ")[1:]),
            email=profile.contact.email,
            position=profile.title or job.title,
            hire_date=datetime.today().date(),
            employment_type=job.employment_type,
            status="active",
            candidate_profile_id=profile.id
        )

        db.add(new_emp)
        job.status = "filled"
        job.assigned_employee_id = new_emp.id

        other_apps = db.query(Application).filter(
            Application.job_id == job.id,
            Application.id != application.id
        ).all()
        for app in other_apps:
            app.status = "rejected"
        
        db.commit()
        return {"success": True, "message": "Candidat accepté et employé créé"}
    except Exception as e:
        db.rollback()
        return {"success": False, "message": f"Erreur: {str(e)}"}
    finally:
        db.close()

@router.post("/api/assign-quiz/{job_id}/{candidate_id}")
async def assign_quiz_to_candidate(job_id: int, candidate_id: int):
    """Assign a quiz to a candidate for a specific job. Does NOT generate the quiz."""
    try:
        user_id = current_user_session.get('user_id')
        if not user_id:
            return {"success": False, "message": "Utilisateur non connecté"}
        
        db = SessionLocal()
        try:
            current_admin = db.query(HRAdmin).filter(HRAdmin.id == user_id).first()
            if not current_admin:
                return {"success": False, "message": "Utilisateur non trouvé"}
            
            job = db.query(Job).filter(Job.id == job_id).first()
            if not job:
                return {"success": False, "message": "Poste non trouvé"}
            
            candidate = db.query(ProfileCandidat).filter(ProfileCandidat.id == candidate_id).first()
            if not candidate:
                return {"success": False, "message": "Candidat non trouvé"}
            
            application = db.query(Application).filter(
                Application.job_id == job_id,
                Application.candidate_profile_id == candidate_id
            ).first()
            if not application:
                return {"success": False, "message": "Candidature non trouvée"}
            
            quiz_service = QuizService()
            assignment = quiz_service.assign_quiz_to_candidate(
                job_id=job_id,
                candidate_id=candidate_id,
                assigned_by=user_id
            )
            
            # Ensure DB assignment record exists and status is assigned
            from models import JobQuizAssignment
            assignment_record = db.query(JobQuizAssignment).filter(
                JobQuizAssignment.id == assignment["assignment_id"]
            ).first()
            if assignment_record:
                assignment_record.status = "assigned"
                assignment_record.quiz_attempt_id = None
                db.commit()
            
            return {
                "success": True,
                "message": f"Quiz assigné avec succès au candidat {candidate.name}",
                "assignment": assignment
            }
        finally:
            db.close()
    except ValueError as e:
        return {"success": False, "message": str(e)}
    except Exception as e:
        return {"success": False, "message": f"Erreur lors de l'assignation: {str(e)}"}

@router.get("/api/job-quiz-assignments/{job_id}")
def get_job_quiz_assignments(job_id: int):
    """Get all quiz assignments for a specific job"""
    try:
        user_id = current_user_session.get('user_id')
        if not user_id:
            return {"success": False, "message": "Utilisateur non connecté"}
        
        db = SessionLocal()
        
        # Check if job exists
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            return {"success": False, "message": "Poste non trouvé"}
        
        # Get quiz assignments for this job
        from models import JobQuizAssignment
        assignments = db.query(JobQuizAssignment).filter(
            JobQuizAssignment.job_id == job_id
        ).all()
        
        result = []
        for assignment in assignments:
            candidate = db.query(ProfileCandidat).filter(ProfileCandidat.id == assignment.candidate_id).first()
            result.append({
                "assignment_id": assignment.id,
                "candidate_id": assignment.candidate_id,
                "candidate_name": candidate.name if candidate else "Unknown",
                "assigned_at": assignment.assigned_at,
                "due_date": assignment.due_date,
                "status": assignment.status,
                "quiz_attempt_id": assignment.quiz_attempt_id
            })
        
        return {
            "success": True,
            "assignments": result
        }
    except Exception as e:
        return {"success": False, "message": f"Erreur: {str(e)}"}
    finally:
        db.close()

@router.post("/api/generate-job-quiz/{job_id}/{candidate_id}")
def generate_job_quiz(job_id: int, candidate_id: int):
    """Generate a quiz based on job requirements for a candidate"""
    try:
        user_id = current_user_session.get('user_id')
        if not user_id:
            return {"success": False, "message": "Utilisateur non connecté"}
        
        # Generate quiz
        quiz_service = QuizService()
        quiz_data = quiz_service.generate_job_based_quiz(
            job_id=job_id,
            candidate_id=candidate_id
        )
        
        return {
            "success": True,
            "message": "Quiz généré avec succès",
            "quiz": quiz_data
        }
    except ValueError as e:
        return {"success": False, "message": str(e)}
    except Exception as e:
        return {"success": False, "message": f"Erreur lors de la génération: {str(e)}"}
