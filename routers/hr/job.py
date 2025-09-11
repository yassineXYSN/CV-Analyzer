from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from databasehr.database import SessionLocal
from databasehr.models import Job, Department, Employee, Application, ProfileCandidat, Contact, HRAdmin, JobSkill, Notification, User, Quiz, QuizAttempt
from databasehr.session_manager import current_user_session
from company_utils import get_user_company
from datetime import datetime, date, timedelta
from typing import Optional, List
from .admin_router import publish_event
from .websocket_manager import hr_websocket_manager

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
        
        # Validation de la date limite (ne doit pas dépasser 1 an)
        if job_data.deadline:
            try:
                deadline_date = datetime.strptime(job_data.deadline, "%Y-%m-%d").date()
                max_deadline = date.today() + timedelta(days=365)  # 1 an maximum
                
                if deadline_date > max_deadline:
                    raise HTTPException(
                        status_code=400, 
                        detail=f"La date limite ne peut pas dépasser 1 an. Date maximum autorisée: {max_deadline.strftime('%d/%m/%Y')}"
                    )
                
                if deadline_date < date.today():
                    raise HTTPException(
                        status_code=400, 
                        detail="La date limite ne peut pas être dans le passé"
                    )
                    
            except ValueError:
                raise HTTPException(
                    status_code=400, 
                    detail="Format de date invalide. Utilisez le format YYYY-MM-DD"
                )
        
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

            # Récupérer les informations du département
            department = db.query(Department).filter(Department.id == new_job.department_id).first()
            
            # Préparer les données du job pour la diffusion
            job_data_for_broadcast = {
                "id": new_job.id,
                "title": new_job.title,
                "description": new_job.description,
                "employment_type": new_job.employment_type,
                "priority": new_job.priority,
                "status": new_job.status,
                "department_id": new_job.department_id,
                "department_name": department.name if department else "N/A",
                "salary_min": float(new_job.salary_min) if new_job.salary_min else None,
                "salary_max": float(new_job.salary_max) if new_job.salary_max else None,
                "currency": new_job.currency,
                "deadline": new_job.deadline.isoformat() if new_job.deadline else None,
                "created_at": new_job.created_at.isoformat() if new_job.created_at else None,
                "company_id": company.id,
                "company_name": company.company_name,
                "skills_count": skills_added
            }
            
            # Diffuser l'événement de création de job en temps réel via WebSocket
            try:
                await hr_websocket_manager.broadcast_job_created(job_data_for_broadcast, company.id)
            except Exception as e:
                print(f"Erreur lors de la diffusion WebSocket job_created: {e}")
            
            # Diffuser aussi via SSE pour l'admin interface
            try:
                await publish_event({
                    "type": "job_created",
                    "job": job_data_for_broadcast,
                    "timestamp": datetime.now().isoformat()
                })
            except Exception as e:
                print(f"Erreur lors de la diffusion SSE job_created: {e}")

            # Préparer le message de réponse
            message = f"Poste '{new_job.title}' créé avec succès"
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

@router.get("/api/debug/quiz/{job_id}/{candidate_id}")
async def debug_quiz_data(job_id: int, candidate_id: int):
    """Debug endpoint to check quiz data for a specific job and candidate"""
    try:
        db = SessionLocal()
        try:
            # Check if quiz exists
            quiz = db.query(Quiz).filter(
                Quiz.job_id == job_id,
                Quiz.candidate_id == candidate_id
            ).first()
            
            if quiz:
                # Check for completed attempts
                quiz_attempt = db.query(QuizAttempt).filter(
                    QuizAttempt.quiz_id == quiz.id,
                    QuizAttempt.candidate_id == candidate_id,
                    QuizAttempt.status == 'completed'
                ).first()
                
                return {
                    "success": True,
                    "quiz_exists": True,
                    "quiz_id": quiz.id,
                    "quiz_status": quiz.status,
                    "has_completed_attempt": quiz_attempt is not None,
                    "attempt_data": {
                        "score": quiz_attempt.score if quiz_attempt else None,
                        "total_correct": quiz_attempt.total_correct if quiz_attempt else None,
                        "total_questions": quiz_attempt.total_questions if quiz_attempt else None,
                        "duration_seconds": int((quiz_attempt.end_time - quiz_attempt.start_time).total_seconds()) if quiz_attempt and quiz_attempt.start_time and quiz_attempt.end_time else None
                    } if quiz_attempt else None
                }
            else:
                return {
                    "success": True,
                    "quiz_exists": False,
                    "quiz_id": None
                }
        finally:
            db.close()
    except Exception as e:
        return {"success": False, "message": f"Error: {str(e)}"}

@router.get("/api/job-basic/{job_id}")
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
                    # Déterminer la compatibilité (IA vs calculée ultérieurement côté client)
                    has_ai = app.compatibility_score is not None and app.compatibility_reason is not None
                    compatibility_percentage = float(app.compatibility_score) if has_ai else None
                    compatibility_source = "ai" if has_ai else None
                    compatibility_reason = app.compatibility_reason if has_ai else None

                    # Récupérer les données de quiz pour ce candidat et ce job
                    quiz_data = None
                    quiz_attempt = None
                    quiz = None
                    
                    # D'abord, chercher si un quiz existe pour ce job et ce candidat
                    quiz = db.query(Quiz).filter(
                        Quiz.job_id == job_id,
                        Quiz.candidate_id == candidate.id
                    ).first()
                    
                    if quiz:
                        # Ensuite, chercher une tentative complétée pour ce quiz
                        quiz_attempt = db.query(QuizAttempt).filter(
                            QuizAttempt.quiz_id == quiz.id,
                            QuizAttempt.candidate_id == candidate.id,
                            QuizAttempt.status == 'completed'
                        ).order_by(QuizAttempt.created_at.desc()).first()
                        
                        if quiz_attempt:
                            # Calculer la durée du quiz
                            duration_seconds = None
                            if quiz_attempt.start_time and quiz_attempt.end_time:
                                duration_seconds = int((quiz_attempt.end_time - quiz_attempt.start_time).total_seconds())
                            
                            # Calculer le score en pourcentage
                            quiz_score_percentage = 0
                            if quiz_attempt.total_questions and quiz_attempt.total_questions > 0:
                                quiz_score_percentage = (quiz_attempt.total_correct / quiz_attempt.total_questions) * 100
                            
                            quiz_data = {
                                "quiz_score": round(quiz_score_percentage, 1),  # Score en pourcentage
                                "quiz_duration": duration_seconds,
                                "quiz_correct_answers": quiz_attempt.total_correct if quiz_attempt.total_correct else 0,
                                "quiz_total_questions": quiz_attempt.total_questions if quiz_attempt.total_questions else 0,
                                "quiz_attempt_id": quiz_attempt.id,
                                "quiz_id": quiz.id
                            }
                        else:
                            # Quiz existe mais pas encore de tentative complétée
                            quiz_data = {
                                "quiz_score": None,
                                "quiz_duration": None,
                                "quiz_correct_answers": None,
                                "quiz_total_questions": None,
                                "quiz_attempt_id": None,
                                "quiz_id": quiz.id
                            }

                    # Ajoutez ce champ dans la réponse des candidatures
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
                        # Champs de compatibilité pour le front
                        "compatibility_percentage": compatibility_percentage,
                        "compatibility_source": compatibility_source,
                        "compatibility_reason": compatibility_reason,
                        "skills_validated": app.skills_validated,
                        "skills_validated_by": app.skills_validated_by,
                        "skills_validated_at": app.skills_validated_at.isoformat() if app.skills_validated_at else None,
                        "skills_validated_notes": app.skills_validated_notes,
                        "quiz_validated": app.quiz_validated,
                        "quiz_validated_by": app.quiz_validated_by,
                        "quiz_validated_at": app.quiz_validated_at.isoformat() if app.quiz_validated_at else None,
                        "quiz_validated_notes": app.quiz_validated_notes,
                        # Données de quiz
                        "quiz_score": quiz_data["quiz_score"] if quiz_data else 0,
                        "quiz_duration": quiz_data["quiz_duration"] if quiz_data else None,
                        "quiz_correct_answers": quiz_data["quiz_correct_answers"] if quiz_data else 0,
                        "quiz_total_questions": quiz_data["quiz_total_questions"] if quiz_data else 0,
                        "quiz_attempt_id": quiz_data["quiz_attempt_id"] if quiz_data else None,
                        "quiz_id": quiz_data["quiz_id"] if quiz_data else None
                    })
                    
                    # Debug: Print quiz data
                    if quiz_data:
                        print(f"DEBUG: Quiz data for candidate {candidate.name}: quiz_id={quiz_data['quiz_id']}, score={quiz_data['quiz_score']}%, duration={quiz_data['quiz_duration']}s, correct={quiz_data['quiz_correct_answers']}/{quiz_data['quiz_total_questions']}")
                    else:
                        print(f"DEBUG: No quiz data for candidate {candidate.name}")
                    
                    # Debug: Print application data being sent
                    print(f"DEBUG: Application data for {candidate.name}: quiz_id={quiz_data['quiz_id'] if quiz_data else None}")
                    
                    # Debug: Print the final application object being sent
                    final_app_data = {
                        "quiz_score": quiz_data["quiz_score"] if quiz_data else 0,
                        "quiz_duration": quiz_data["quiz_duration"] if quiz_data else None,
                        "quiz_correct_answers": quiz_data["quiz_correct_answers"] if quiz_data else 0,
                        "quiz_total_questions": quiz_data["quiz_total_questions"] if quiz_data else None,
                        "quiz_attempt_id": quiz_data["quiz_attempt_id"] if quiz_data else None,
                        "quiz_id": quiz_data["quiz_id"] if quiz_data else None
                    }
                    print(f"DEBUG: Final quiz fields for {candidate.name}: {final_app_data}")
            
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
                "skills": skills_list  # Utiliser la liste des compétences récupérées
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

@router.post("/api/accept-application/{application_id}")
async def accept_application(application_id: int, status_data: dict):
    try:
        user_id = current_user_session.get('user_id')
        if not user_id:
            return {"success": False, "message": "Utilisateur non connecté"}
        
        company = get_user_company(user_id)
        if not company:
            return {"success": False, "message": "Aucune entreprise associée"}
        
        db = SessionLocal()
        try:
            application = db.query(Application).filter(
                Application.id == application_id,
                Application.job.has(company_id=company.id)
            ).first()
            
            if not application:
                return {"success": False, "message": "Candidature non trouvée"}
            
            # Vérifier les permissions
            admin = db.query(HRAdmin).filter(HRAdmin.id == user_id).first()
            if not admin:
                return {"success": False, "message": "Droits insuffisants"}
            
            status = status_data.get("status", "accepted_pending_validation")
            
            # Seuls les admins peuvent accepter définitivement
            if status == "accepted" and admin.role != "admin":
                return {"success": False, "message": "Seuls les administrateurs peuvent valider définitivement"}
            
            application.status = status
            application.decision_date = datetime.now()
            
            # Si acceptation définitive, créer l'employé et la notification
            if status == "accepted":
                candidate = application.candidate_profile
                
                # Vérifier si l'employé existe déjà
                existing_employee = db.query(Employee).filter(
                    Employee.company_id == company.id,
                    Employee.email == candidate.contact.email
                ).first()
                
                if not existing_employee:
                    new_employee = Employee(
                        company_id=company.id,
                        department_id=application.job.department_id,
                        first_name=candidate.name.split(' ')[0],
                        last_name=' '.join(candidate.name.split(' ')[1:]),
                        email=candidate.contact.email,
                        phone=candidate.contact.phone,
                        position=application.job.title,
                        hire_date=date.today(),
                        employment_type=application.job.employment_type,
                        status='active',
                        candidate_profile_id=candidate.id
                    )
                    db.add(new_employee)
                    
                    # Marquer le poste comme pourvu
                    application.job.status = "filled"
                
                # Chercher l'utilisateur par email plutôt que par profile_id
                user = db.query(User).filter(User.email == candidate.contact.email).first()
                
                if not user:
                    print(f"[v0] User not found, creating new user for candidate: {candidate.name}")
                    # Create a new user for the candidate
                    user = User(
                        email=candidate.contact.email,
                        first_name=candidate.name.split(' ')[0] if candidate.name else "Unknown",
                        last_name=' '.join(candidate.name.split(' ')[1:]) if len(candidate.name.split(' ')) > 1 else "",
                        password_hash="",  # Empty password hash for now
                        is_active=True,
                        is_verified=False,
                        created_at=datetime.now()
                    )
                    db.add(user)
                    db.commit()  # Commit to get the user.id
                    db.refresh(user)
                    print(f"[v0] Created new user with id: {user.id}")
                
                print(f"[v0] Creating notification for user_id: {user.id}")
                notification = Notification(
                    user_id=user.id,
                    type="application_accepted",
                    title="Candidature acceptée !",
                    message=f"Félicitations ! Votre candidature pour le poste de {application.job.title} chez {company.company_name} a été acceptée. Vous recevrez bientôt plus d'informations concernant les prochaines étapes.",
                    is_read=False,
                    application_id=application.id,
                    job_id=application.job.id,
                    status="accepted",
                    company_name=company.company_name,
                    job_title=application.job.title,
                    admin_name=f"{admin.first_name} {admin.last_name}"
                )
                db.add(notification)
                print(f"[v0] Notification created successfully for user_id: {user.id}")
            
            db.commit()
            
            return {
                "success": True, 
                "message": f"Candidature {'acceptée' if status == 'accepted' else 'en attente de validation'}"
            }
            
        except Exception as e:
            db.rollback()
            print(f"[v0] Error in accept_application: {str(e)}")
            return {"success": False, "message": f"Erreur: {str(e)}"}
        finally:
            db.close()
    except Exception as e:
        print(f"[v0] Internal error in accept_application: {str(e)}")
        return {"success": False, "message": f"Erreur interne: {str(e)}"}

@router.post("/api/applications/{application_id}/validate-skills")
async def validate_application_skills(application_id: int, validation_data: dict):
    try:
        user_id = current_user_session.get('user_id')
        if not user_id:
            return {"success": False, "message": "Utilisateur non connecté"}

        company = get_user_company(user_id)
        if not company:
            return {"success": False, "message": "Aucune entreprise associée"}

        db = SessionLocal()
        try:
            application = db.query(Application).filter(
                Application.id == application_id,
                Application.job.has(company_id=company.id)
            ).first()

            if not application:
                return {"success": False, "message": "Candidature non trouvée"}

            # Mettre à jour la validation des compétences
            application.skills_validated = validation_data.get('validated', False)
            application.skills_validated_by = user_id
            application.skills_validated_at = datetime.now()
            application.skills_validated_notes = validation_data.get('notes', '')

            db.commit()

            return {
                "success": True,
                "message": "Compétences validées avec succès"
            }
        except Exception as e:
            db.rollback()
            return {"success": False, "message": f"Erreur lors de la validation: {str(e)}"}
        finally:
            db.close()
    except Exception as e:
        return {"success": False, "message": f"Erreur interne du serveur: {str(e)}"}
    
@router.post("/api/applications/{application_id}/validate-quiz")
async def validate_application_quiz(application_id: int, validation_data: dict):
    try:
        user_id = current_user_session.get('user_id')
        if not user_id:
            return {"success": False, "message": "Utilisateur non connecté"}

        company = get_user_company(user_id)
        if not company:
            return {"success": False, "message": "Aucune entreprise associée"}

        db = SessionLocal()
        try:
            application = db.query(Application).filter(
                Application.id == application_id,
                Application.job.has(company_id=company.id)
            ).first()

            if not application:
                return {"success": False, "message": "Candidature non trouvée"}

            # Mettre à jour la validation du quiz
            application.quiz_validated = validation_data.get('validated', False)
            application.quiz_validated_by = user_id
            application.quiz_validated_at = datetime.now()
            application.quiz_validated_notes = validation_data.get('notes', '')

            db.commit()

            return {
                "success": True,
                "message": "Quiz validé avec succès"
            }
        except Exception as e:
            db.rollback()
            return {"success": False, "message": f"Erreur lors de la validation: {str(e)}"}
        finally:
            db.close()
    except Exception as e:
        return {"success": False, "message": f"Erreur interne du serveur: {str(e)}"}