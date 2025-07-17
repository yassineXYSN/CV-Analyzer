from fastapi import APIRouter
from databasehr.database import SessionLocal
from databasehr.models import Application, Job, ProfileCandidat, Contact, Employee, Department, Company, HRAdmin, AdminDepartments
from databasehr.session_manager import current_user_session
from company_utils import get_user_company
from datetime import datetime, date
from typing import Optional

router = APIRouter()

@router.get("/api/applications")
async def get_applications(status: Optional[str] = None):
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
            
            # Construire la requête de base
            query = db.query(Application).join(
                Job, Application.job_id == Job.id
            ).join(
                Department, Job.department_id == Department.id
            ).filter(
                Job.company_id == company.id
            )
            
            # Si c'est un chef de département, filtrer par ses départements assignés
            if current_admin.role == 'department_head':
                print(f"🔒 Chef de département - Filtrage des candidatures pour: {current_admin.first_name} {current_admin.last_name}")
                
                # Récupérer les départements assignés à ce chef
                assigned_dept_ids = db.query(AdminDepartments.department_id).filter(
                    AdminDepartments.admin_id == user_id
                ).subquery()
                
                query = query.filter(Department.id.in_(assigned_dept_ids))
                
                print(f"📋 Filtrage appliqué pour les départements assignés")
            else:
                print(f"👑 Admin/Recruteur - Accès à toutes les candidatures: {current_admin.role}")
            
            if status and status != "all":
                query = query.filter(Application.status == status)
            
            applications = query.order_by(Application.application_date.desc()).all()
            
            applications_list = []
            for app in applications:
                job = db.query(Job).filter(Job.id == app.job_id).first()
                department = None
                if job:
                    department = db.query(Department).filter(
                        Department.id == job.department_id
                    ).first()
                
                candidate = db.query(ProfileCandidat).filter(
                    ProfileCandidat.id == app.candidate_profile_id
                ).first()
                
                contact = None
                if candidate and candidate.contact_id:
                    contact = db.query(Contact).filter(
                        Contact.id == candidate.contact_id
                    ).first()
                
                if candidate and job:
                    days_since_application = 0
                    if app.application_date:
                        days_since_application = (datetime.now() - app.application_date).days
                    
                    applications_list.append({
                        "id": app.id,
                        "job_id": job.id,
                        "job_title": job.title,
                        "department_name": department.name if department else "N/A",
                        "candidate_id": candidate.id,
                        "candidate_name": candidate.name,
                        "candidate_title": candidate.title,
                        "candidate_email": contact.email if contact else "N/A",
                        "status": app.status,
                        "application_date": app.application_date.isoformat() if app.application_date else None,
                        "days_since_application": days_since_application,
                        "hr_rating": float(app.hr_rating) if app.hr_rating else None,
                        "hr_notes": app.hr_notes,
                        "priority": job.priority,
                        "reviewed_by": app.reviewed_by,
                        "reviewed_at": app.reviewed_at.isoformat() if app.reviewed_at else None
                    })
            
            print(f"✅ {len(applications_list)} candidatures récupérées pour l'utilisateur {current_admin.role}")
            
            return {
                "success": True,
                "applications": applications_list,
                "total": len(applications_list)
            }
        except Exception as e:
            print(f"❌ Erreur lors de la récupération des candidatures: {str(e)}")
            return {"success": False, "message": f"Erreur lors de la récupération des candidatures: {str(e)}"}
        finally:
            db.close()
    except Exception as e:
        print(f"❌ Erreur interne: {str(e)}")
        return {"success": False, "message": f"Erreur interne du serveur: {str(e)}"}

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
            # Récupérer l'utilisateur actuel pour vérifier son rôle
            current_admin = db.query(HRAdmin).filter(HRAdmin.id == user_id).first()
            if not current_admin:
                return {"success": False, "message": "Utilisateur non trouvé"}
            
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
            
            job = db.query(Job).filter(Job.id == application.job_id).first()
            candidate = db.query(ProfileCandidat).filter(
                ProfileCandidat.id == application.candidate_profile_id
            ).first()
            contact = None
            if candidate and candidate.contact_id:
                contact = db.query(Contact).filter(
                    Contact.id == candidate.contact_id
                ).first()
            
            new_status = status_data.get('status')
            if not new_status:
                return {"success": False, "message": "Statut manquant"}
            
            if new_status == 'accepted' and job and candidate and contact:
                try:
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
                        email=candidate.email,
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
                    
                    job.status = 'filled'
                    job.assigned_employee_id = new_employee.id
                    
                    application.status = new_status
                    application.reviewed_by = user_id
                    application.reviewed_at = datetime.now()
                    application.decision_date = datetime.now()
                    application.decision_reason = f"Candidature acceptée - Embauché comme {job.title}"
                    
                    if status_data.get('hr_notes'):
                        application.hr_notes = status_data['hr_notes']
                    if status_data.get('hr_rating'):
                        application.hr_rating = float(status_data['hr_rating'])
                    
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
        
        # Récupérer l'utilisateur actuel pour vérifier son rôle
        current_admin = db.query(HRAdmin).filter(HRAdmin.id == user_id).first()
        if not current_admin:
            return {"success": False, "message": "Utilisateur non trouvé"}
        
        # Construire la requête avec vérification des permissions
        application_query = db.query(Application).join(
            Job, Application.job_id == Job.id
        ).join(
            Department, Job.department_id == Department.id
        ).filter(Application.id == application_id)
        
        # Si c'est un chef de département, vérifier qu'il a accès à cette candidature
        if current_admin.role == 'department_head':
            assigned_dept_ids = db.query(AdminDepartments.department_id).filter(
                AdminDepartments.admin_id == user_id
            ).subquery()
            
            application_query = application_query.filter(Department.id.in_(assigned_dept_ids))
        
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
