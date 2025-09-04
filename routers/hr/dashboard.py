from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from databasehr.database import SessionLocal
from databasehr.models import Department, Employee, Job, Application, HRAdmin, ProfileCandidat, Contact
from databasehr.session_manager import current_user_session
from company_utils import get_user_company
from datetime import date
from fastapi.templating import Jinja2Templates
from jwt_utils import get_current_hr_user, get_optional_current_hr_user
from typing import Dict, Any, Optional
import os

# Configuration des templates
current_dir = os.path.dirname(os.path.abspath(__file__))
templates_dir = os.path.join(current_dir, '../../templates')
templates = Jinja2Templates(directory=templates_dir)

router = APIRouter()

def check_hr_authentication():
    """Check if user is authenticated for HR pages"""
    user_id = current_user_session.get('user_id')
    if not user_id:
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/hr-login", status_code=302)
    return None

def check_super_admin_permission(user_id: int) -> bool:
    """
    Vérifie si l'utilisateur actuel est un super admin
    """
    db = SessionLocal()
    try:
        user = db.query(HRAdmin).filter(HRAdmin.id == user_id).first()
        if not user:
            return False
        return user.role == "super_admin"
    except Exception as e:
        print(f"Erreur lors de la vérification des permissions: {e}")
        return False
    finally:
        db.close()

@router.get("/dashboard", response_class=HTMLResponse)
def dashboard_page(request: Request):
    # Check authentication
    auth_check = check_hr_authentication()
    if auth_check:
        return auth_check
    
    response = templates.TemplateResponse("HR-dep/hr-dashboard.html", {"request": request})
    # Prevent caching of dashboard page
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

@router.get("/hr-reports", response_class=HTMLResponse)
def hr_reports_page(request: Request):
    # Check authentication
    auth_check = check_hr_authentication()
    if auth_check:
        return auth_check
    
    response = templates.TemplateResponse("HR-dep/hr-reports.html", {"request": request})
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

@router.get("/employee-profile", response_class=HTMLResponse)
def employee_profile_page(request: Request):
    # Check authentication
    auth_check = check_hr_authentication()
    if auth_check:
        return auth_check
    
    response = templates.TemplateResponse("HR-dep/employee-profile.html", {"request": request})
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

@router.get("/job-details", response_class=HTMLResponse)
def job_details_page(request: Request):
    # Check authentication
    auth_check = check_hr_authentication()
    if auth_check:
        return auth_check
    
    response = templates.TemplateResponse("HR-dep/job-details.html", {"request": request})
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

@router.get("/api/dashboard-stats-debug")
async def get_dashboard_stats_debug(current_user: Dict[str, Any] = Depends(get_current_hr_user)):
    """Debug version of dashboard stats with simplified queries"""
    try:
        print(f"🔍 DASHBOARD STATS DEBUG: Starting with user: {current_user}")
        user_id = int(current_user.get("sub"))
        print(f"🔍 DASHBOARD STATS DEBUG: User ID: {user_id}")
        company = get_user_company(user_id)
        print(f"🔍 DASHBOARD STATS DEBUG: Company: {company}")
        
        if not company:
            return JSONResponse(
                status_code=404,
                content={"success": False, "message": "Aucune entreprise associée"}
            )
        
        db = SessionLocal()
        try:
            print(f"🔍 DASHBOARD STATS DEBUG: Starting database queries for company ID: {company.id}")
            
            # Statistiques des départements
            total_departments = db.query(Department).filter(
                Department.company_id == company.id,
                Department.is_active == True
            ).count()
            print(f"🔍 DASHBOARD STATS DEBUG: Departments: {total_departments}")
            
            # Statistiques des employés
            total_employees = db.query(Employee).filter(
                Employee.company_id == company.id,
                Employee.status == 'active'
            ).count()
            print(f"🔍 DASHBOARD STATS DEBUG: Employees: {total_employees}")
            
            # Statistiques des postes
            total_jobs = db.query(Job).filter(
                Job.company_id == company.id,
                Job.status.in_(['draft', 'active'])
            ).count()
            print(f"🔍 DASHBOARD STATS DEBUG: Jobs: {total_jobs}")
            
            urgent_jobs = db.query(Job).filter(
                Job.company_id == company.id,
                Job.status.in_(['draft', 'active']),
                Job.priority == 'urgent'
            ).count()
            print(f"🔍 DASHBOARD STATS DEBUG: Urgent jobs: {urgent_jobs}")
            
            # Statistiques des candidatures (simplifiées)
            total_applications = db.query(Application).join(
                Job, Application.job_id == Job.id
            ).filter(
                Job.company_id == company.id,
                Application.status.in_(['pending', 'reviewed'])
            ).count()
            print(f"🔍 DASHBOARD STATS DEBUG: Applications: {total_applications}")
            
            # Pas de requête complexe pour les candidatures récentes pour l'instant
            recent_applications_list = []
            
            stats = {
                "total_departments": total_departments,
                "total_employees": total_employees,
                "total_jobs": total_jobs,
                "urgent_jobs": urgent_jobs,
                "total_applications": total_applications,
                "recent_applications": recent_applications_list,
            }
            
            print(f"🔍 DASHBOARD STATS DEBUG: Stats created: {stats}")
            
            return JSONResponse(
                status_code=200,
                content={"success": True, "stats": stats}
            )
            
        except Exception as e:
            print(f"❌ DASHBOARD STATS DEBUG: Database error: {str(e)}")
            import traceback
            traceback.print_exc()
            return JSONResponse(
                status_code=500,
                content={"success": False, "message": f"Erreur lors du calcul des statistiques: {str(e)}"}
            )
        finally:
            db.close()
            
    except Exception as e:
        print(f"❌ DASHBOARD STATS DEBUG: Outer error: {str(e)}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"Erreur interne du serveur: {str(e)}"}
        )

@router.get("/api/dashboard-stats")
async def get_dashboard_stats(current_user: Dict[str, Any] = Depends(get_current_hr_user)):
    try:
        print(f"🔍 DASHBOARD STATS: Starting with user: {current_user}")
        user_id = int(current_user.get("sub"))
        print(f"🔍 DASHBOARD STATS: User ID: {user_id}")
        company = get_user_company(user_id)
        print(f"🔍 DASHBOARD STATS: Company: {company}")
        if not company:
            return JSONResponse(
                status_code=404,
                content={"success": False, "message": "Aucune entreprise associée"}
            )
        
        db = SessionLocal()
        try:
            print(f"🔍 DASHBOARD STATS: Starting database queries for company ID: {company.id}")
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
            print(f"🔍 DASHBOARD STATS: Querying recent applications...")
            recent_applications = db.query(
                Application.id,
                ProfileCandidat.name.label("candidate_name"),
                Contact.email.label("candidate_email"),
                Application.status,
                Job.title.label("job_title"),
                Application.application_date
            ).join(
                Job, Application.job_id == Job.id
            ).join(
                ProfileCandidat, Application.candidate_profile_id == ProfileCandidat.id
            ).join(
                Contact, ProfileCandidat.contact_id == Contact.id
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
                    "name": app.candidate_name,
                    "email": app.candidate_email,
                    "status": app.status,
                    "job": app.job_title,
                    "date": app.application_date.strftime("%d/%m/%Y") if app.application_date else None
                })
            
            stats = {
                "total_departments": total_departments,
                "total_employees": total_employees,
                "total_jobs": total_jobs,
                "urgent_jobs": urgent_jobs,
                "total_applications": total_applications,
                "recent_applications": recent_applications_list,
            }
            
            return JSONResponse(
                status_code=200,
                content={"success": True, "stats": stats}
            )
            
        except Exception as e:
            print(f"❌ DASHBOARD STATS: Database error: {str(e)}")
            import traceback
            traceback.print_exc()
            return JSONResponse(
                status_code=500,
                content={"success": False, "message": f"Erreur lors du calcul des statistiques: {str(e)}"}
            )
        finally:
            db.close()
            
    except Exception as e:
        print(f"❌ DASHBOARD STATS: Outer error: {str(e)}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"Erreur interne du serveur: {str(e)}"}
        )

@router.get("/api/test-simple")
async def test_simple():
    """Simple test endpoint without authentication"""
    print("🔍 TEST SIMPLE: Endpoint called")
    return JSONResponse(
        status_code=200,
        content={"success": True, "message": "Simple test works"}
    )

@router.get("/api/test-dashboard-simple")
async def test_dashboard_simple():
    """Test dashboard endpoint without authentication to isolate the issue"""
    print("🔍 TEST DASHBOARD SIMPLE: Starting test")
    try:
        db = SessionLocal()
        try:
            # Test basic database connection
            print("🔍 TEST DASHBOARD SIMPLE: Testing database connection")
            departments_count = db.query(Department).count()
            print(f"🔍 TEST DASHBOARD SIMPLE: Found {departments_count} departments")
            
            return JSONResponse(
                status_code=200,
                content={"success": True, "message": f"Database test successful - {departments_count} departments found"}
            )
        except Exception as e:
            print(f"❌ TEST DASHBOARD SIMPLE: Database error: {str(e)}")
            return JSONResponse(
                status_code=500,
                content={"success": False, "message": f"Database error: {str(e)}"}
            )
        finally:
            db.close()
    except Exception as e:
        print(f"❌ TEST DASHBOARD SIMPLE: Outer error: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"Outer error: {str(e)}"}
        )

@router.get("/api/test-dashboard-with-auth")
async def test_dashboard_with_auth(current_user: Dict[str, Any] = Depends(get_current_hr_user)):
    """Test dashboard endpoint with authentication to isolate the issue"""
    print(f"🔍 TEST DASHBOARD AUTH: Starting with user: {current_user}")
    try:
        user_id = int(current_user.get("sub"))
        print(f"🔍 TEST DASHBOARD AUTH: User ID: {user_id}")
        company = get_user_company(user_id)
        print(f"🔍 TEST DASHBOARD AUTH: Company: {company}")
        
        if not company:
            return JSONResponse(
                status_code=404,
                content={"success": False, "message": "Aucune entreprise associée"}
            )
        
        db = SessionLocal()
        try:
            print(f"🔍 TEST DASHBOARD AUTH: Testing basic queries for company ID: {company.id}")
            
            # Test simple queries
            total_departments = db.query(Department).filter(
                Department.company_id == company.id,
                Department.is_active == True
            ).count()
            
            total_employees = db.query(Employee).filter(
                Employee.company_id == company.id,
                Employee.status == 'active'
            ).count()
            
            total_jobs = db.query(Job).filter(
                Job.company_id == company.id,
                Job.status.in_(['draft', 'active'])
            ).count()
            
            print(f"🔍 TEST DASHBOARD AUTH: Departments: {total_departments}, Employees: {total_employees}, Jobs: {total_jobs}")
            
            return JSONResponse(
                status_code=200,
                content={
                    "success": True, 
                    "message": "Auth test successful",
                    "stats": {
                        "total_departments": total_departments,
                        "total_employees": total_employees,
                        "total_jobs": total_jobs
                    }
                }
            )
        except Exception as e:
            print(f"❌ TEST DASHBOARD AUTH: Database error: {str(e)}")
            import traceback
            traceback.print_exc()
            return JSONResponse(
                status_code=500,
                content={"success": False, "message": f"Database error: {str(e)}"}
            )
        finally:
            db.close()
    except Exception as e:
        print(f"❌ TEST DASHBOARD AUTH: Outer error: {str(e)}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"Outer error: {str(e)}"}
        )

@router.get("/api/test-auth")
async def test_auth(current_user: Dict[str, Any] = Depends(get_current_hr_user)):
    """Test endpoint to debug JWT authentication"""
    print(f"🔍 TEST AUTH: User data: {current_user}")
    return JSONResponse(
        status_code=200,
        content={"success": True, "user": current_user}
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
            
            # Vérifier les permissions
            is_super_admin = check_super_admin_permission(user_id)
            
            # Return user data with permissions
            user_data = {
                "id": user.id,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "role": user.role,
                "last_login": user.last_login.strftime("%d/%m/%Y %H:%M") if user.last_login else None,
                "permissions": {
                    "is_super_admin": is_super_admin,
                    "can_create_users": is_super_admin
                }
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

@router.get("/api/applications")
async def get_applications():
    """
    Récupère toutes les candidatures avec leurs détails de compatibilité
    """
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
            applications = db.query(
                Application.id,
                Application.status,
                Application.application_date,
                Application.candidate_profile_id,
                Application.job_id,
                Application.is_recommended,
                Application.recommendation_priority,
                Application.recommended_by,
                Application.recommendation_comment,
                Application.recommendation_date,
                Application.compatibility_percentage,
                Application.matched_skills_count,
                Application.total_job_skills,
                Application.compatibility_score,
                Application.compatibility_reason,
                ProfileCandidat.name.label("candidate_name"),
                Contact.email.label("candidate_email"),
                Job.title.label("job_title"),
                Job.priority,
                Department.name.label("department_name")
            ).join(
                Job, Application.job_id == Job.id
            ).join(
                Department, Job.department_id == Department.id
            ).join(
                ProfileCandidat, Application.candidate_profile_id == ProfileCandidat.id
            ).join(
                Contact, ProfileCandidat.contact_id == Contact.id
            ).filter(
                Job.company_id == company.id
            ).order_by(
                Application.application_date.desc()
            ).all()
            
            applications_list = []
            for app in applications:
                # Calcul des jours depuis la candidature
                days_since = 0
                if app.application_date:
                    days_since = (date.today() - app.application_date).days
                
                has_ai_compatibility = app.compatibility_score is not None and app.compatibility_reason is not None
                
                # Use AI data if available, otherwise use calculated data
                if has_ai_compatibility:
                    compatibility_percentage = float(app.compatibility_score) if app.compatibility_score else 0
                    compatibility_source = "ai"
                    compatibility_reason = app.compatibility_reason
                else:
                    compatibility_percentage = app.compatibility_percentage or 0
                    compatibility_source = "calculated"
                    compatibility_reason = None
                
                applications_list.append({
                    "id": app.id,
                    "candidate_id": app.candidate_profile_id,
                    "candidate_name": app.candidate_name,
                    "candidate_email": app.candidate_email,
                    "job_id": app.job_id,
                    "job_title": app.job_title,
                    "department_name": app.department_name,
                    "status": app.status,
                    "priority": app.priority,
                    "application_date": app.application_date.strftime("%Y-%m-%d") if app.application_date else None,
                    "days_since_application": days_since,
                    "is_recommended": app.is_recommended or False,
                    "recommendation_priority": app.recommendation_priority,
                    "recommended_by": app.recommended_by,
                    "recommendation_comment": app.recommendation_comment,
                    "recommendation_date": app.recommendation_date.strftime("%Y-%m-%d") if app.recommendation_date else None,
                    "compatibility_percentage": compatibility_percentage,
                    "compatibility_source": compatibility_source,
                    "compatibility_reason": compatibility_reason,
                    "matched_skills_count": app.matched_skills_count or 0,
                    "total_job_skills": app.total_job_skills or 0,

                })
            
            return JSONResponse(
                status_code=200,
                content={
                    "success": True, 
                    "applications": applications_list,
                    "total": len(applications_list)
                }
            )
            
        except Exception as e:
            print(f"Erreur lors de la récupération des candidatures: {e}")
            return JSONResponse(
                status_code=500,
                content={"success": False, "message": f"Erreur lors de la récupération des candidatures: {str(e)}"}
            )
        finally:
            db.close()
            
    except Exception as e:
        print(f"Erreur interne: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"Erreur interne du serveur: {str(e)}"}
        )

@router.get("/quiz-preview/{application_id}", response_class=HTMLResponse)
async def quiz_preview_page(request: Request, application_id: int):
    """Display quiz preview page for HR admin"""
    try:
        # Check authentication
        auth_check = check_hr_authentication()
        if auth_check:
            return auth_check
        
        # Get quiz results data
        from routers.hr.application import get_quiz_results
        from databasehr.database import SessionLocal
        
        db = SessionLocal()
        try:
            result = await get_quiz_results(application_id, db)
            if not result["success"]:
                return JSONResponse(
                    status_code=400,
                    content={"error": result["message"]}
                )
            
            return templates.TemplateResponse("HR-dep/quiz-preview.html", {
                "request": request,
                "quiz_data": result["quiz_data"]
            })
        finally:
            db.close()
            
    except Exception as e:
        print(f"Error loading quiz preview: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Erreur lors du chargement de l'aperçu du quiz: {str(e)}"}
        )