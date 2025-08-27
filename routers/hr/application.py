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


router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def calculate_skill_compatibility(candidate_skills, job_skills):
    """Calculate compatibility percentage between candidate and job skills"""
    
    print(f"🔍 [v0] COMPATIBILITY CALC: Starting calculation")
    print(f"🔍 [v0] COMPATIBILITY CALC: Job skills input: {job_skills}")
    print(f"🔍 [v0] COMPATIBILITY CALC: Candidate skills input: {candidate_skills}")
    
    if not job_skills:
        print("⚠️ [v0] COMPATIBILITY CALC: No job skills found, returning 0%")
        return 0, 0, len(job_skills) if job_skills else 0
    
    # Parse candidate skills if they're stored as JSON string
    candidate_skills_list = []
    if candidate_skills:
        try:
            print(f"🔍 [v0] COMPATIBILITY CALC: Parsing candidate skills...")
            if isinstance(candidate_skills, str):
                parsed_skills = json.loads(candidate_skills)
            else:
                parsed_skills = candidate_skills
                
            print(f"🔍 [v0] COMPATIBILITY CALC: Parsed skills: {parsed_skills}")
                
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
            print(f"❌ [v0] COMPATIBILITY CALC: Error parsing candidate skills: {e}")
            candidate_skills_list = []
    
    print(f"🔍 [v0] COMPATIBILITY CALC: Final candidate skills list: {candidate_skills_list}")
    
    # Count matching skills
    matched_skills = 0
    total_job_skills = len(job_skills)
    matched_skill_names = []
    
    print(f"🔍 [v0] COMPATIBILITY CALC: Starting skill matching...")
    for job_skill in job_skills:
        job_skill_name = job_skill.skill_name.lower().strip()
        print(f"🔍 [v0] COMPATIBILITY CALC: Checking job skill: '{job_skill_name}'")
        
        if job_skill_name in candidate_skills_list:
            matched_skills += 1
            matched_skill_names.append(job_skill.skill_name)
            print(f"✅ [v0] COMPATIBILITY CALC: MATCH found for: '{job_skill_name}'")
        else:
            print(f"❌ [v0] COMPATIBILITY CALC: NO MATCH for: '{job_skill_name}'")
    
    # Calculate percentage
    compatibility_percentage = (matched_skills / total_job_skills) * 100 if total_job_skills > 0 else 0
    
    print(f"🔍 [v0] COMPATIBILITY CALC: Final results:")
    print(f"   - Matched skills: {matched_skills}")
    print(f"   - Total job skills: {total_job_skills}")
    print(f"   - Compatibility percentage: {compatibility_percentage}%")
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
        print(f"🚀 [v0] API APPLICATIONS: Starting request")
        print(f"🔍 [v0] API APPLICATIONS: Filters - status: {status_filter}, compatibility: {compatibility_filter}")
        
        user_id = current_user_session.get('user_id')
        if not user_id:
            print(f"❌ [v0] API APPLICATIONS: No user_id in session")
            return {"success": False, "message": "Utilisateur non connecté"}

        print(f"🔍 [v0] API APPLICATIONS: User ID: {user_id}")

        company = get_user_company(user_id)
        if not company:
            print(f"❌ [v0] API APPLICATIONS: No company found for user {user_id}")
            return {"success": False, "message": "Aucune entreprise associée"}

        print(f"🔍 [v0] API APPLICATIONS: Company ID: {company.id}")

        # Récupérer l'utilisateur actuel pour vérifier son rôle
        current_admin = db.query(HRAdmin).filter(HRAdmin.id == user_id).first()
        if not current_admin:
            print(f"❌ [v0] API APPLICATIONS: Admin not found for user {user_id}")
            return {"success": False, "message": "Utilisateur non trouvé"}

        print(f"🔍 [v0] API APPLICATIONS: Current admin: {current_admin.first_name} {current_admin.last_name} ({current_admin.role})")

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
            print(f"🔒 [v0] API APPLICATIONS: Department head filtering for: {current_admin.first_name} {current_admin.last_name}")

            assigned_dept_ids = db.query(AdminDepartments.department_id).filter(
                AdminDepartments.admin_id == user_id
            ).subquery()

            query = query.filter(Department.id.in_(assigned_dept_ids))
            print("📋 [v0] API APPLICATIONS: Department filtering applied")
        else:
            print(f"👑 [v0] API APPLICATIONS: Admin/Recruiter access: {current_admin.role}")

        # Appliquer le filtre de statut
        if status_filter and status_filter != "all":
            query = query.filter(Application.status == status_filter)
            print(f"🔍 [v0] API APPLICATIONS: Status filter applied: {status_filter}")

        applications = query.order_by(Application.application_date.desc()).all()
        print(f"📊 [v0] API APPLICATIONS: Found {len(applications)} applications")

        applications_list = []
        for app in applications:
            print(f"\n🔍 [v0] API APPLICATIONS: Processing application {app.id}")
            
            job = app.job
            department = job.department if job else None
            candidate = app.candidate_profile
            contact = candidate.contact if candidate else None

            print(f"   - Job: {job.title if job else 'N/A'}")
            print(f"   - Candidate: {candidate.name if candidate else 'N/A'}")
            print(f"   - Department: {department.name if department else 'N/A'}")

            has_ai_compatibility = app.compatibility_score is not None and app.compatibility_reason is not None
            print(f"   - Has AI compatibility data: {has_ai_compatibility}")
            
            if has_ai_compatibility:
                print(f"   - AI compatibility score: {app.compatibility_score}")
                compatibility_percentage = float(app.compatibility_score)
                matched_skills_count = 0  # AI data doesn't provide this breakdown
                total_job_skills = 0      # AI data doesn't provide this breakdown
                compatibility_source = "ai"
                compatibility_reason = app.compatibility_reason
                print(f"✅ [v0] API APPLICATIONS: Using AI compatibility data: {compatibility_percentage}%")
            else:
                print(f"   - No AI data, calculating compatibility...")
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
                compatibility_source = "calculated"
                compatibility_reason = None
                print(f"✅ [v0] API APPLICATIONS: Calculated compatibility: {compatibility_percentage}% ({matched_skills_count}/{total_job_skills})")

            # Appliquer filtre de compatibilité si précisé
            if compatibility_filter != "all":
                print(f"🔍 [v0] API APPLICATIONS: Applying compatibility filter: {compatibility_filter}")
                try:
                    if compatibility_filter == "high" and compatibility_percentage < 75:
                        print(f"   - Filtered out: {compatibility_percentage}% < 75% (high)")
                        continue
                    elif compatibility_filter == "medium" and not (50 <= compatibility_percentage < 75):
                        print(f"   - Filtered out: {compatibility_percentage}% not in 50-75% range (medium)")
                        continue
                    elif compatibility_filter == "low" and not (25 <= compatibility_percentage < 50):
                        print(f"   - Filtered out: {compatibility_percentage}% not in 25-50% range (low)")
                        continue
                    elif compatibility_filter == "very_low" and compatibility_percentage >= 25:
                        print(f"   - Filtered out: {compatibility_percentage}% >= 25% (very_low)")
                        continue
                    print(f"   - Passed compatibility filter")
                except ValueError:
                    print(f"   - Invalid compatibility filter value, ignoring")
                    pass  # Ignore invalid threshold input

            # Récupérer les informations de recommandation
            recommended_by_admin = None
            if app.recommended_by_admin_id:
                recommended_by_admin = db.query(HRAdmin).filter(
                    HRAdmin.id == app.recommended_by_admin_id
                ).first()

            days_since_application = (datetime.now() - app.application_date).days if app.application_date else 0

            app_data = {
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
                "compatibility_percentage": compatibility_percentage,
                "matched_skills_count": matched_skills_count,
                "total_job_skills": total_job_skills,
                "compatibility_source": compatibility_source,
                "compatibility_reason": compatibility_reason
            }
            
            applications_list.append(app_data)
            print(f"✅ [v0] API APPLICATIONS: Added application {app.id} to results")

        print(f"✅ [v0] API APPLICATIONS: {len(applications_list)} applications processed for user {current_admin.role}")
        
        # Log des scores de compatibilité pour debug
        for app in applications_list:
            print(f"📊 [v0] API APPLICATIONS: App {app['id']}: {app['compatibility_percentage']}% (source: {app['compatibility_source']})")
        
        return {
            "success": True,
            "applications": applications_list,
            "total": len(applications_list)
        }

    except Exception as e:
        import traceback
        print(f"❌ [v0] API APPLICATIONS: Internal error: {str(e)}")
        print(f"❌ [v0] API APPLICATIONS: Traceback: {traceback.format_exc()}")
        return {"success": False, "message": f"Erreur interne du serveur: {str(e)}"}

@router.get("/api/application/{application_id}/compatibility")
async def get_application_compatibility_details(application_id: int, db: Session = Depends(get_db)):
    try:
        print(f"🚀 [v0] COMPATIBILITY DETAILS: Starting for application {application_id}")
        
        user_id = current_user_session.get('user_id')
        if not user_id:
            print(f"❌ [v0] COMPATIBILITY DETAILS: No user_id in session")
            return {"success": False, "message": "Utilisateur non connecté"}

        # Vérifier l'utilisateur et ses rôles
        current_admin = db.query(HRAdmin).filter(HRAdmin.id == user_id).first()
        if not current_admin:
            print(f"❌ [v0] COMPATIBILITY DETAILS: Admin not found for user {user_id}")
            return {"success": False, "message": "Utilisateur non trouvé"}

        company = get_user_company(user_id)
        if not company:
            print(f"❌ [v0] COMPATIBILITY DETAILS: No company found for user {user_id}")
            return {"success": False, "message": "Aucune entreprise associée"}

        print(f"🔍 [v0] COMPATIBILITY DETAILS: User: {current_admin.first_name} {current_admin.last_name} ({current_admin.role})")
        print(f"🔍 [v0] COMPATIBILITY DETAILS: Company ID: {company.id}")

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
            print(f"❌ [v0] COMPATIBILITY DETAILS: Application {application_id} not found or no access")
            return {"success": False, "message": "Candidature non trouvée"}

        print(f"🔍 [v0] COMPATIBILITY DETAILS: Found application {application.id}")

        # Si chef de département, vérifier l'accès au département
        if current_admin.role == 'department_head':
            assigned_dept_ids = db.query(AdminDepartments.department_id).filter(
                AdminDepartments.admin_id == user_id
            ).all()
            dept_ids = [d.department_id for d in assigned_dept_ids]
            job = db.query(Job).filter(Job.id == application.job_id).first()
            if job.department_id not in dept_ids:
                print(f"❌ [v0] COMPATIBILITY DETAILS: Department access denied for job {job.id}")
                return {"success": False, "message": "Vous n'avez pas accès à ce département"}

        has_ai_compatibility = application.compatibility_score is not None and application.compatibility_reason is not None
        print(f"🔍 [v0] COMPATIBILITY DETAILS: Has AI compatibility data: {has_ai_compatibility}")
        
        if has_ai_compatibility:
            print(f"✅ [v0] COMPATIBILITY DETAILS: Using AI compatibility data")
            return {
                "success": True,
                "compatibility_percentage": float(application.compatibility_score),
                "compatibility_source": "ai",
                "compatibility_reason": application.compatibility_reason,
                "matched_skills": [],  # AI data doesn't provide detailed breakdown
                "missing_skills": [],  # AI data doesn't provide detailed breakdown
                "candidate_skills": [],
                "total_job_skills": 0,
                "matched_count": 0,
                "missing_count": 0
            }

        # CORRECTION: Récupérer les compétences du poste via JobSkill
        job_skills = db.query(JobSkill).filter(JobSkill.job_id == application.job_id).all()
        print(f"🔍 [v0] COMPATIBILITY DETAILS: Found {len(job_skills)} job skills")

        # Récupérer le candidat
        candidate = db.query(ProfileCandidat).filter(
            ProfileCandidat.id == application.candidate_profile_id
        ).first()

        if not candidate:
            print(f"❌ [v0] COMPATIBILITY DETAILS: Candidate not found")
            return {"success": False, "message": "Candidat non trouvé"}

        print(f"🔍 [v0] COMPATIBILITY DETAILS: Candidate: {candidate.name}")
        print(f"🔍 [v0] COMPATIBILITY DETAILS: Candidate skills raw: {candidate.skills}")

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
            except (json.JSONDecodeError, Exception) as e:
                print(f"❌ [v0] COMPATIBILITY DETAILS: Error parsing candidate skills: {e}")
                candidate_skills_list = []

        print(f"🔍 [v0] COMPATIBILITY DETAILS: Parsed candidate skills: {candidate_skills_list}")

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
                print(f"✅ [v0] COMPATIBILITY DETAILS: MATCH - {job_skill.skill_name}")
            else:
                missing_skills.append(skill_match)
                print(f"❌ [v0] COMPATIBILITY DETAILS: MISSING - {job_skill.skill_name}")

        compatibility_percentage, matched_count, total_skills = calculate_skill_compatibility(candidate.skills, job_skills)

        print(f"✅ [v0] COMPATIBILITY DETAILS: Final results - {compatibility_percentage}% compatibility")

        return {
            "success": True,
            "compatibility_percentage": compatibility_percentage,
            "compatibility_source": "calculated",
            "compatibility_reason": None,
            "matched_skills": matched_skills,
            "missing_skills": missing_skills,
            "candidate_skills": candidate_skills_list,
            "total_job_skills": len(job_skills),
            "matched_count": len(matched_skills),
            "missing_count": len(missing_skills)
        }

    except Exception as e:
        print(f"❌ [v0] COMPATIBILITY DETAILS: Error: {str(e)}")
        import traceback
        print(f"❌ [v0] COMPATIBILITY DETAILS: Traceback: {traceback.format_exc()}")
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

@router.get("/api/job/{job_id}")
async def get_job_with_applications(job_id: int, db: Session = Depends(get_db)):
    try:
        print(f"🚀 [v0] API JOB: Starting request for job {job_id}")
        
        user_id = current_user_session.get('user_id')
        if not user_id:
            print(f"❌ [v0] API JOB: No user_id in session")
            return {"success": False, "message": "Utilisateur non connecté"}

        print(f"🔍 [v0] API JOB: User ID: {user_id}")

        company = get_user_company(user_id)
        if not company:
            print(f"❌ [v0] API JOB: No company found for user {user_id}")
            return {"success": False, "message": "Aucune entreprise associée"}

        print(f"🔍 [v0] API JOB: Company ID: {company.id}")

        # Récupérer l'utilisateur actuel pour vérifier son rôle
        current_admin = db.query(HRAdmin).filter(HRAdmin.id == user_id).first()
        if not current_admin:
            print(f"❌ [v0] API JOB: Admin not found for user {user_id}")
            return {"success": False, "message": "Utilisateur non trouvé"}

        print(f"🔍 [v0] API JOB: Current admin: {current_admin.first_name} {current_admin.last_name} ({current_admin.role})")

        # Récupérer le job avec ses informations
        job_query = db.query(Job).join(
            Department, Job.department_id == Department.id
        ).filter(
            Job.id == job_id,
            Job.company_id == company.id
        ).options(
            joinedload(Job.department)
        )

        # Si c'est un chef de département, filtrer par ses départements assignés
        if current_admin.role == 'department_head':
            print(f"🔒 [v0] API JOB: Department head filtering for: {current_admin.first_name} {current_admin.last_name}")

            assigned_dept_ids = db.query(AdminDepartments.department_id).filter(
                AdminDepartments.admin_id == user_id
            ).subquery()

            job_query = job_query.filter(Department.id.in_(assigned_dept_ids))
            print("📋 [v0] API JOB: Department filtering applied")

        job = job_query.first()
        if not job:
            print(f"❌ [v0] API JOB: Job {job_id} not found or no access")
            return {"success": False, "message": "Poste non trouvé ou accès non autorisé"}

        print(f"✅ [v0] API JOB: Found job: {job.title}")

        # Récupérer toutes les candidatures pour ce poste avec debug logging
        print(f"🔍 [v0] API JOB: Querying applications for job_id {job_id}")
        applications_query = db.query(Application).filter(
            Application.job_id == job_id
        ).options(
            joinedload(Application.candidate_profile).joinedload(ProfileCandidat.contact)
        )

        applications = applications_query.order_by(Application.application_date.desc()).all()
        print(f"📊 [v0] API JOB: Raw query found {len(applications)} applications for job {job_id}")
        
        # Debug: Print all application IDs found
        for app in applications:
            print(f"   - Application ID: {app.id}, Candidate ID: {app.candidate_profile_id}, Status: {app.status}")

        # Traiter chaque candidature avec calcul de compatibilité
        applications_list = []
        for app in applications:
            print(f"\n🔍 [v0] API JOB: Processing application {app.id}")
            
            candidate = app.candidate_profile
            contact = candidate.contact if candidate else None

            print(f"   - Candidate: {candidate.name if candidate else 'N/A'}")

            # Vérifier si on a des données de compatibilité IA
            has_ai_compatibility = app.compatibility_score is not None and app.compatibility_reason is not None
            print(f"   - Has AI compatibility data: {has_ai_compatibility}")
            
            if has_ai_compatibility:
                print(f"   - AI compatibility score: {app.compatibility_score}")
                compatibility_percentage = float(app.compatibility_score)
                matched_skills_count = 0  # AI data doesn't provide this breakdown
                total_job_skills = 0      # AI data doesn't provide this breakdown
                compatibility_source = "ai"
                compatibility_reason = app.compatibility_reason
                print(f"✅ [v0] API JOB: Using AI compatibility data: {compatibility_percentage}%")
            else:
                print(f"   - No AI data, calculating compatibility...")
                # Récupérer les compétences du job via la relation JobSkill
                job_skills = db.query(JobSkill).filter(JobSkill.job_id == job.id).all()
                
                candidate_skills = candidate.skills if candidate else None
                print(f"   - Job skills found: {len(job_skills)}")
                print(f"   - Job skills: {[skill.skill_name for skill in job_skills]}")
                print(f"   - Candidate skills raw: {candidate_skills}")

                # Utiliser la fonction de calcul de compatibilité
                compatibility_percentage, matched_skills_count, total_job_skills = calculate_skill_compatibility(candidate_skills, job_skills)
                compatibility_source = "calculated"
                compatibility_reason = None
                print(f"✅ [v0] API JOB: Calculated compatibility: {compatibility_percentage}% ({matched_skills_count}/{total_job_skills})")

            # Récupérer les informations de recommandation
            recommended_by_admin = None
            if app.recommended_by_admin_id:
                recommended_by_admin = db.query(HRAdmin).filter(
                    HRAdmin.id == app.recommended_by_admin_id
                ).first()

            days_since_application = (datetime.now() - app.application_date).days if app.application_date else 0

            app_data = {
                "id": app.id,
                "name": candidate.name if candidate else "N/A",
                "email": contact.email if contact else "N/A",
                "status": app.status,
                "application_date": app.application_date.isoformat() if app.application_date else None,
                "days_since_application": days_since_application,
                "hr_rating": float(app.hr_rating) if app.hr_rating else None,
                "hr_notes": app.hr_notes,
                "reviewed_by": app.reviewed_by,
                "reviewed_at": app.reviewed_at.isoformat() if app.reviewed_at else None,
                "is_recommended": app.is_recommended or False,
                "recommendation_priority": app.recommendation_priority,
                "recommendation_comment": app.recommendation_comment,
                "recommended_by": f"{recommended_by_admin.first_name} {recommended_by_admin.last_name}" if recommended_by_admin else None,
                "recommendation_date": app.recommendation_date.isoformat() if app.recommendation_date else None,
                "compatibility_percentage": compatibility_percentage,
                "matched_skills_count": matched_skills_count,
                "total_job_skills": total_job_skills,
                "compatibility_source": compatibility_source,
                "compatibility_reason": compatibility_reason
            }
            
            applications_list.append(app_data)
            print(f"✅ [v0] API JOB: Added application {app.id} to results")

        # Récupérer les compétences du job pour l'affichage
        job_skills = db.query(JobSkill).filter(JobSkill.job_id == job.id).all()
        skills_data = []
        for skill in job_skills:
            skills_data.append({
                "name": skill.skill_name,
                "level": skill.skill_level,
                "required": skill.is_required
            })

        # Récupérer les informations de l'entreprise
        company_data = {
            "name": company.name,
            "industry": company.industry,
            "size": company.size
        }

        # Construire la réponse avec les informations du job
        job_data = {
            "id": job.id,
            "title": job.title,
            "company": company_data,
            "department": job.department.name if job.department else "N/A",
            "description": job.description,
            "requirements": job.requirements,
            "responsibilities": job.responsibilities,
            "skills": skills_data,
            "employment_type": job.employment_type,
            "salary_min": job.salary_min,
            "salary_max": job.salary_max,
            "priority": job.priority,
            "experience_level": job.experience_level,
            "status": job.status,
            "created_at": job.created_at.isoformat() if job.created_at else None,
            "applications": applications_list  # This is the key fix - applications are now included
        }

        print(f"By yassine {job_data}")
        
        return {
            "success": True,
            "job": job_data
        }

    except Exception as e:
        import traceback
        print(f"❌ [v0] API JOB: Internal error: {str(e)}")
        print(f"❌ [v0] API JOB: Traceback: {traceback.format_exc()}")
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
