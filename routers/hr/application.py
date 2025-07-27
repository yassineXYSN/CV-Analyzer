from fastapi import APIRouter, Query, Depends
from databasehr.database import SessionLocal
from databasehr.models import Application, Job, ProfileCandidat, Contact, Department, JobSkill, Company
from databasehr.session_manager import current_user_session
from company_utils import get_user_company
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, and_
from datetime import datetime, date
import json
from typing import Optional

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
        
        print(f"🔍 BACKEND: Loading applications for company {company.id}")
        
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
            joinedload(Application.candidate_profile).joinedload(ProfileCandidat.contact)
        )
        
        # Apply status filter
        if status_filter and status_filter != "all":
            query = query.filter(Application.status == status_filter)
        
        applications = query.order_by(Application.application_date.desc()).all()
        print(f"📊 BACKEND: Found {len(applications)} applications")
        
        applications_list = []
        for app in applications:
            # Get job skills for compatibility calculation
            job_skills = db.query(JobSkill).filter(JobSkill.job_id == app.job_id).all()
            print(f"🎯 BACKEND: Job {app.job_id} has {len(job_skills)} skills: {[s.skill_name for s in job_skills]}")
            
            # Calculate compatibility
            candidate_skills = app.candidate_profile.skills if app.candidate_profile else None
            print(f"👤 BACKEND: Candidate skills: {candidate_skills}")
            
            compatibility_percentage = calculate_skill_compatibility(candidate_skills, job_skills)
            print(f"📈 BACKEND: Compatibility calculated: {compatibility_percentage}%")
            
            # Calculate days since application
            days_since = 0
            if app.application_date:
                days_since = (datetime.now().date() - app.application_date.date()).days
            
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
            
            app_data = {
                "id": app.id,
                "candidate_id": app.candidate_profile_id,
                "candidate_name": app.candidate_profile.name if app.candidate_profile else "N/A",
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
                "total_job_skills": len(job_skills)
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
            
            print(f"🔍 BACKEND: Compatibility filter '{compatibility_filter}' reduced {original_count} to {len(applications_list)} applications")
        
        print(f"✅ BACKEND: Returning {len(applications_list)} applications with compatibility data")
        return {
            "success": True,
            "applications": applications_list,
            "total_count": len(applications_list)
        }
        
    except Exception as e:
        print(f"❌ BACKEND: Erreur lors de la récupération des candidatures: {str(e)}")
        import traceback
        traceback.print_exc()
        return {"success": False, "message": f"Erreur lors de la récupération des candidatures: {str(e)}"}

@router.get("/api/application/{application_id}/compatibility")
async def get_application_compatibility_details(application_id: int, db: Session = Depends(get_db)):
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
        print(f"❌ BACKEND: Erreur lors de la récupération des détails de compatibilité: {str(e)}")
        return {"success": False, "message": f"Erreur: {str(e)}"}

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
            application = db.query(Application).join(
                Job, Application.job_id == Job.id
            ).filter(
                Application.id == application_id,
                Job.company_id == company.id
            ).first()
            
            if not application:
                return {"success": False, "message": "Candidature non trouvée"}
            
            new_status = status_data.get('status')
            if not new_status:
                return {"success": False, "message": "Statut manquant"}
            
            # Store old status for comparison
            old_status = application.status
            
            # Update application status
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
            jobs = db.query(Job).filter(
                Job.company_id == company.id,
                Job.status.in_(['active', 'draft'])
            ).limit(3).all()
            
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
                            source="Site web"
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
        
        application = db.query(Application).filter(Application.id == application_id).first()
        if not application:
            return {"success": False, "message": "Candidature non trouvée"}
        
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