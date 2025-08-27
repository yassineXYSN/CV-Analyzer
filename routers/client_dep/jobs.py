import json
from fastapi import APIRouter, Request, Query, Depends, HTTPException
from fastapi.responses import HTMLResponse
from database import SessionLocal
from databaseclient.models import *
from routers.client_dep.dependencies import get_db, get_current_user
import math
from pydantic import BaseModel
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, or_, and_
from fastapi.templating import Jinja2Templates
from typing import Optional
import os
import requests


router = APIRouter()
# Templates
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

# Chemin vers le dossier templates
templates_dir = os.path.join(BASE_DIR, "templates")

templates = Jinja2Templates(directory=templates_dir)


# Pagination helper class
class Pagination:
    def __init__(self, page: int, per_page: int, total: int):
        self.current_page = page
        self.per_page = per_page
        self.total_jobs = total
        self.total_pages = math.ceil(total / per_page) if per_page > 0 else 0
        self.has_prev = page > 1
        self.has_next = page < self.total_pages
        self.prev_page = page - 1 if self.has_prev else None
        self.next_page = page + 1 if self.has_next else None

# Search parameters helper class
class SearchParams:
    def __init__(self, search: str = "", location: str = "", category: str = "", 
                 employment_type: str = "", salary_min: Optional[int] = None, 
                 salary_max: Optional[int] = None):
        self.search = search
        self.location = location
        self.category = category
        self.employment_type = employment_type
        self.salary_min = salary_min
        self.salary_max = salary_max


@router.get("/jobs", response_class=HTMLResponse)
async def jobs_page(
    request: Request,
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    search: str = Query(""),
    location: str = Query(""),
    category: str = Query(""),
    employment_type: str = Query(""),
    salary_min: Optional[str] = Query(None),
    salary_max: Optional[str] = Query(None),
    sort: str = Query("newest")
):
    current_user = get_current_user(request, db)
    
    # Convert salary strings to integers, handling empty strings
    salary_min_int = None
    salary_max_int = None

    if salary_min and salary_min.strip():
        try:
            salary_min_int = int(salary_min)
        except ValueError:
            salary_min_int = None

    if salary_max and salary_max.strip():
        try:
            salary_max_int = int(salary_max)
        except ValueError:
            salary_max_int = None

    print(f"Salary filters - Min: {salary_min_int}, Max: {salary_max_int}")
    
    per_page = 12
    
    # Build base query with eager loading
    query = db.query(Job).options(
        joinedload(Job.company),
        joinedload(Job.department)
    )
    
    # Always join Company and Department for flexible searching
    query = query.join(Company, Job.company_id == Company.id, isouter=True)
    query = query.join(Department, Job.department_id == Department.id, isouter=True)
    
    # Apply filters - only add filters that have values
    filters = [Job.status == 'active']
    
    # Search filter - search across multiple fields with flexible matching
    if search and search.strip():
        search_term = f"%{search.strip()}%"
        search_filter = or_(
            Job.title.ilike(search_term),
            Job.description.ilike(search_term),
            Job.requirements.ilike(search_term),
            Company.company_name.ilike(search_term),
            Department.name.ilike(search_term),
            # Also search in job tags if they exist
            Job.tags.ilike(search_term) if hasattr(Job, 'tags') else False
        )
        filters.append(search_filter)
    
    # Location filter - flexible location matching
    if location and location.strip():
        location_term = f"%{location.strip()}%"
        location_filter = or_(
            Company.address.ilike(location_term),
            Job.location.ilike(location_term) if hasattr(Job, 'location') else False
        )
        filters.append(location_filter)
    
    # Category filter - flexible category matching
    if category and category.strip():
        category_term = f"%{category.strip()}%"
        category_filter = or_(
            Department.name.ilike(category_term),
            Job.title.ilike(category_term),
            Job.description.ilike(category_term),
            Job.tags.ilike(category_term) if hasattr(Job, 'tags') else False
        )
        filters.append(category_filter)
    
    # Employment type filter - flexible matching
    if employment_type and employment_type.strip():
        if employment_type.lower() != 'all':
            employment_filter = or_(
                Job.employment_type.ilike(f"%{employment_type}%"),
                Job.employment_type == employment_type
            )
            filters.append(employment_filter)
    
    # Improved salary filters
    if salary_min_int and salary_min_int > 0:
        # User wants jobs that pay at least salary_min_int
        # Include jobs where the maximum salary meets the minimum requirement
        # OR where minimum salary meets the requirement (if max is null)
        salary_min_filter = or_(
            and_(Job.salary_max.isnot(None), Job.salary_max >= salary_min_int),
            and_(Job.salary_max.is_(None), Job.salary_min >= salary_min_int),
            # Also include jobs where salary_min >= user's minimum (they definitely meet the requirement)
            Job.salary_min >= salary_min_int
        )
        filters.append(salary_min_filter)
        print(f"Applied minimum salary filter: >= {salary_min_int}")

    if salary_max_int and salary_max_int > 0:
        # User wants jobs within their budget (salary_max_int)
        # Include jobs where the minimum salary is within budget
        # OR where maximum salary is within budget (if min is null)
        salary_max_filter = or_(
            and_(Job.salary_min.isnot(None), Job.salary_min <= salary_max_int),
            and_(Job.salary_min.is_(None), Job.salary_max <= salary_max_int),
            # Also include jobs where salary_max <= user's maximum (they're definitely within budget)
            Job.salary_max <= salary_max_int
        )
        filters.append(salary_max_filter)
        print(f"Applied maximum salary filter: <= {salary_max_int}")
    
    # Apply all filters
    if filters:
        query = query.filter(and_(*filters))
    
    # Fetch all jobs matching filters (before sorting by compatibility or pagination)
    all_filtered_jobs = query.all()

    # Prepare candidate skills for comparison
    candidate_skills_lower = []
    if current_user:
        candidate_profile = db.query(ProfileCandidat).filter(
            ProfileCandidat.user_id == current_user.id
        ).first()
        
        if candidate_profile and candidate_profile.skills:
            raw_skills_data = candidate_profile.skills 
            
            try:
                # Attempt to load as JSON if it's a string
                if isinstance(raw_skills_data, str):
                    parsed_skills = json.loads(raw_skills_data)
                else:
                    # Assume it's already a list if not a string (e.g., if JSON column type worked)
                    parsed_skills = raw_skills_data

                if isinstance(parsed_skills, list):
                    processed_skills = []
                    for s in parsed_skills:
                        if isinstance(s, str) and s: # Ensure skill is a non-empty string
                            # Handle "Skill: Percentage" format
                            if ':' in s:
                                processed_skills.append(s.split(':')[0].strip())
                            else:
                                # Handle simple skill names
                                processed_skills.append(s.strip())
                    candidate_skills_lower = [s.lower() for s in processed_skills]
                else:
                    print(f"WARNING: Parsed candidate skills for user {current_user.id} is not a list: {parsed_skills}")
                    candidate_skills_lower = [] # Fallback if unexpected format
            except json.JSONDecodeError:
                print(f"ERROR: Could not decode JSON for candidate skills: {raw_skills_data}")
                candidate_skills_lower = [] # Fallback if JSON decoding fails
            except Exception as e:
                print(f"ERROR: Unexpected error processing candidate skills: {e}")
                candidate_skills_lower = []

    # Process jobs to add skill compatibility, application status, and saved status
    processed_jobs = []
    user_applications = set()
    saved_job_ids = set()

    if current_user:
        candidate_profile_for_status = db.query(ProfileCandidat).filter(
            ProfileCandidat.user_id == current_user.id
        ).first()
        if candidate_profile_for_status:
            user_applications = db.query(Application.job_id).filter(
                Application.candidate_profile_id == candidate_profile_for_status.id
            ).all()
            user_applications = {app.job_id for app in user_applications}
        
        saved_jobs_db = db.query(SavedJob.job_id).filter(
            SavedJob.user_id == current_user.id
        ).all()
        saved_job_ids = {saved.job_id for saved in saved_jobs_db}

    for job in all_filtered_jobs:
        job_skills_for_card = db.query(JobSkill).filter(JobSkill.job_id == job.id).all()
        
        matched_skills_count = 0
        total_job_skills = len(job_skills_for_card)
        
        if total_job_skills > 0 and candidate_skills_lower:
            for job_skill in job_skills_for_card:
                if job_skill.skill_name.lower().strip() in candidate_skills_lower:
                    matched_skills_count += 1
            compatibility_percentage = (matched_skills_count / total_job_skills) * 100
        else:
            compatibility_percentage = 0 # Default to 0 if no job skills or no candidate skills
        
        processed_jobs.append({
            'job': job,
            'has_applied': job.id in user_applications,
            'is_saved': job.id in saved_job_ids,
            'compatibility_percentage': round(compatibility_percentage)
        })
    
    # Apply sorting to the processed list
    if sort == "newest":
        processed_jobs.sort(key=lambda x: x['job'].created_at, reverse=True)
    elif sort == "oldest":
        processed_jobs.sort(key=lambda x: x['job'].created_at, reverse=False)
    elif sort == "salary_high":
        # Sort by salary_max, then salary_min, handling None values
        processed_jobs.sort(key=lambda x: (x['job'].salary_max if x['job'].salary_max is not None else -1, 
                                           x['job'].salary_min if x['job'].salary_min is not None else -1), 
                            reverse=True)
    elif sort == "salary_low":
        # Sort by salary_min, then salary_max, handling None values
        processed_jobs.sort(key=lambda x: (x['job'].salary_min if x['job'].salary_min is not None else float('inf'), 
                                           x['job'].salary_max if x['job'].salary_max is not None else float('inf')), 
                            reverse=False)
    elif sort == "relevance" and search:
        # This sort is harder to do in Python without a proper scoring function.
        # For simplicity, we'll default to newest if relevance is requested without a search term,
        # or if a more complex relevance score isn't implemented.
        # For now, we'll just use a simple title/company match for relevance.
        processed_jobs.sort(key=lambda x: (
            (search.lower() in x['job'].title.lower()) * 2 + # Higher weight for title match
            (search.lower() in x['job'].company.company_name.lower() if x['job'].company else 0)
        ), reverse=True)
        processed_jobs.sort(key=lambda x: x['job'].created_at, reverse=True) # Secondary sort by newest
    elif sort == "compatibility":
        # Sort by compatibility percentage, highest first
        processed_jobs.sort(key=lambda x: x['compatibility_percentage'], reverse=True)
    else:
        # Default to newest
        processed_jobs.sort(key=lambda x: x['job'].created_at, reverse=True)

    # Get total count after all filters and processing
    total_jobs = len(processed_jobs)
    print(f"Total jobs found after processing: {total_jobs}")

    # Apply pagination to the sorted list
    offset = (page - 1) * per_page
    jobs_for_page = processed_jobs[offset : offset + per_page]
    
    # Create pagination object
    pagination = Pagination(page, per_page, total_jobs)
    
    # Create search params object
    search_params = SearchParams(search, location, category, employment_type, salary_min_int, salary_max_int)
    
    # Get all departments for category dropdown - make it more flexible
    try:
        departments = db.query(Department.name).filter(Department.name.isnot(None)).distinct().all()
        categories = [dept[0] for dept in departments if dept[0]]
        
        # Add some common categories if none exist
        if not categories:
            categories = [
                "Développement", "Marketing", "Design", "Finance", 
                "Ressources Humaines", "Ventes", "Support Client"
            ]
    except:
        categories = [
            "Développement", "Marketing", "Design", "Finance", 
            "Ressources Humaines", "Ventes", "Support Client"
        ]
    
    return templates.TemplateResponse("client-dep/jobs.html", {
        "request": request,
        "jobs_with_status": jobs_for_page, # Pass the paginated and processed jobs
        "pagination": pagination,
        "search_params": search_params,
        "sort": sort,
        "categories": categories,
        "total_jobs": total_jobs,
        "current_user": current_user
    })

@router.get("/jobs/{job_id}", response_class=HTMLResponse)
async def job_detail(request: Request, job_id: int, db: Session = Depends(get_db)):
    current_user = get_current_user(request, db)
    
    job = db.query(Job).options(
        joinedload(Job.company),
        joinedload(Job.department)
    ).filter(Job.id == job_id).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Increment view count
    job.views_count = (job.views_count or 0) + 1
    db.commit()
    
    # Get job skills
    job_skills = db.query(JobSkill).filter(JobSkill.job_id == job.id).all()
    
    # Prepare candidate skills for comparison
    candidate_skills_lower = []
    if current_user:
        candidate_profile = db.query(ProfileCandidat).filter(
            ProfileCandidat.user_id == current_user.id
        ).first()
        
        if candidate_profile and candidate_profile.skills:
            raw_skills_data = candidate_profile.skills 
            
            print(f"DEBUG: Raw candidate skills from DB: {raw_skills_data} (Type: {type(raw_skills_data)})")

            try:
                # Attempt to load as JSON if it's a string
                if isinstance(raw_skills_data, str):
                    parsed_skills = json.loads(raw_skills_data)
                else:
                    # Assume it's already a list if not a string (e.g., if JSON column type worked)
                    parsed_skills = raw_skills_data

                if isinstance(parsed_skills, list):
                    processed_skills = []
                    for s in parsed_skills:
                        if isinstance(s, str) and s: # Ensure skill is a non-empty string
                            # Handle "Skill: Percentage" format
                            if ':' in s:
                                processed_skills.append(s.split(':')[0].strip())
                            else:
                                # Handle simple skill names
                                processed_skills.append(s.strip())
                    candidate_skills_lower = [s.lower() for s in processed_skills]
                else:
                    print(f"WARNING: Parsed candidate skills for user {current_user.id} is not a list: {parsed_skills}")
                    candidate_skills_lower = [] # Fallback if unexpected format
            except json.JSONDecodeError:
                print(f"ERROR: Could not decode JSON for candidate skills: {raw_skills_data}")
                candidate_skills_lower = [] # Fallback if JSON decoding fails
            except Exception as e:
                print(f"ERROR: Unexpected error processing candidate skills: {e}")
                candidate_skills_lower = []

    print(f"DEBUG: Parsed candidate skills for comparison: {candidate_skills_lower}")
    print(f"DEBUG: Job skills for comparison: {[s.skill_name.lower() for s in job_skills]}")

    # Perform skill matching in Python
    matched_job_skills = []
    unmatched_job_skills = []
    
    for skill in job_skills:
        job_skill_name_lower = skill.skill_name.lower().strip()
        if job_skill_name_lower in candidate_skills_lower:
            matched_job_skills.append(skill)
            print(f"DEBUG: Skill match found: '{job_skill_name_lower}' in {candidate_skills_lower}")
        else:
            unmatched_job_skills.append(skill)
            print(f"DEBUG: Skill '{job_skill_name_lower}' is NOT present in {candidate_skills_lower}")


    # Check if user has applied and saved
    has_applied = False
    is_saved = False
    if current_user:
        # Get the candidate profile for the current user
        candidate_profile_for_app = db.query(ProfileCandidat).filter(
            ProfileCandidat.user_id == current_user.id
        ).first()

        if candidate_profile_for_app:
            application = db.query(Application).filter(
                and_(
                    Application.job_id == job_id,
                    Application.candidate_profile_id == candidate_profile_for_app.id
                )
            ).first()
            has_applied = application is not None
        
        # Check if job is saved
        saved_job = db.query(SavedJob).filter(
            and_(
                SavedJob.user_id == current_user.id,
                SavedJob.job_id == job_id
            )
        ).first()
        is_saved = saved_job is not None

    return templates.TemplateResponse("client-dep/job_detail.html", {
        "request": request,
        "job": job,
        "current_user": current_user,
        "has_applied": has_applied,
        "is_saved": is_saved,
        "matched_job_skills": matched_job_skills, # Pass matched job skills
        "unmatched_job_skills": unmatched_job_skills, # Pass unmatched job skills
        "candidate_skills": candidate_skills_lower # Still pass for general info/debugging if needed
    })

@router.get("/my-applications", response_class=HTMLResponse)
async def my_applications_page(request: Request, db: Session = Depends(get_db)):
    current_user = get_current_user(request, db)
    
    # Require authentication
    if not current_user:
        # Redirect to login page or show error
        return templates.TemplateResponse("client-dep/login.html", {
            "request": request,
            "error": "Vous devez être connecté pour voir vos candidatures"
        })
    
    # Get user's candidate profile
    candidate_profile = db.query(ProfileCandidat).filter(
        ProfileCandidat.user_id == current_user.id
    ).first()
    
    applications = []
    if candidate_profile:
        # Get all applications for this user with job and company details
        applications_query = db.query(Application).filter(
            Application.candidate_profile_id == candidate_profile.id
        ).order_by(Application.application_date.desc())
        
        applications = applications_query.all()
        
        # Manually load job and company data for each application
        for app in applications:
            app.job = db.query(Job).options(
                joinedload(Job.company),
                joinedload(Job.department)
            ).filter(Job.id == app.job_id).first()
    
    # Group applications by status for summary
    status_counts = {
        'pending': 0,
        'reviewed': 0,
        'interview_scheduled': 0,
        'interview_completed': 0,
        'accepted': 0,
        'rejected': 0,
        'withdrawn': 0
    }
    
    for app in applications:
        if app.status in status_counts:
            status_counts[app.status] += 1
    
    return templates.TemplateResponse("client-dep/my-applications.html", {
        "request": request,
        "applications": applications,
        "status_counts": status_counts,
        "total_applications": len(applications),
        "current_user": current_user
    })

# NEW: Saved jobs page
@router.get("/saved-jobs", response_class=HTMLResponse)
async def saved_jobs_page(
    request: Request, 
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    sort: str = Query("newest")
):
    current_user = get_current_user(request, db)
    
    # Require authentication
    if not current_user:
        return templates.TemplateResponse("client-dep/login.html", {
            "request": request,
            "error": "Vous devez être connecté pour voir vos offres sauvegardées"
        })
    
    per_page = 12
    
    # Get saved jobs for the current user
    query = db.query(SavedJob).options(
        joinedload(SavedJob.job).joinedload(Job.company),
        joinedload(SavedJob.job).joinedload(Job.department)
    ).filter(SavedJob.user_id == current_user.id)
    
    # Apply sorting
    if sort == "newest":
        query = query.order_by(SavedJob.saved_at.desc())
    elif sort == "oldest":
        query = query.order_by(SavedJob.saved_at.asc())
    elif sort == "job_newest":
        query = query.join(Job).order_by(Job.created_at.desc())
    elif sort == "salary_high":
        query = query.join(Job).order_by(Job.salary_max.desc().nullslast())
    elif sort == "salary_low":
        query = query.join(Job).order_by(Job.salary_min.asc().nullslast())
    else:
        query = query.order_by(SavedJob.saved_at.desc())
    
    # Get total count
    total_saved = query.count()
    
    # Apply pagination
    offset = (page - 1) * per_page
    saved_jobs = query.offset(offset).limit(per_page).all()
    
    # Check application status for each saved job
    saved_jobs_with_status = []
    if current_user:
        # Get the candidate profile for the current user
        candidate_profile = db.query(ProfileCandidat).filter(
            ProfileCandidat.user_id == current_user.id
        ).first()

        # Get all applications for this user
        user_applications = set()
        if candidate_profile:
            user_applications = db.query(Application.job_id).filter(
                Application.candidate_profile_id == candidate_profile.id
            ).all()
            user_applications = {app.job_id for app in user_applications}
        
        for saved_job in saved_jobs:
            saved_job_dict = {
                'saved_job': saved_job,
                'job': saved_job.job,
                'has_applied': saved_job.job.id in user_applications,
                'is_saved': True  # Obviously true since we're on saved jobs page
            }
            saved_jobs_with_status.append(saved_job_dict)
    
    # Create pagination object
    pagination = Pagination(page, per_page, total_saved)
    
    return templates.TemplateResponse("client-dep/saved-jobs.html", {
        "request": request,
        "saved_jobs_with_status": saved_jobs_with_status,
        "pagination": pagination,
        "sort": sort,
        "total_saved": total_saved,
        "current_user": current_user
    })

# API endpoints for job interactions
@router.post("/api/jobs/{job_id}/save")
async def save_job(job_id: int, request: Request, db: Session = Depends(get_db)):
    """Save job to user's favorites"""
    current_user = get_current_user(request, db)
    if not current_user:
        return {"success": False, "message": "Vous devez être connecté pour sauvegarder une offre"}
    
    try:
        # Check if job exists
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            return {"success": False, "message": "Offre d'emploi non trouvée"}
        
        # Check if already saved
        existing_saved = db.query(SavedJob).filter(
            and_(SavedJob.user_id == current_user.id, SavedJob.job_id == job_id)
        ).first()
        
        if existing_saved:
            return {"success": False, "message": "Cette offre est déjà dans vos favoris"}
        
        # Create new saved job
        saved_job = SavedJob(
            user_id=current_user.id,
            job_id=job_id
        )
        
        db.add(saved_job)
        db.commit()
        
        return {"success": True, "message": "Offre ajoutée aux favoris"}
        
    except Exception as e:
        db.rollback()
        print(f"Error saving job: {str(e)}")
        return {"success": False, "message": "Erreur lors de la sauvegarde"}

@router.delete("/api/jobs/{job_id}/save")
async def unsave_job(job_id: int, request: Request, db: Session = Depends(get_db)):
    """Remove job from user's favorites"""
    current_user = get_current_user(request, db)
    if not current_user:
        return {"success": False, "message": "Vous devez être connecté"}
    
    try:
        # Find and delete saved job
        saved_job = db.query(SavedJob).filter(
            and_(SavedJob.user_id == current_user.id, SavedJob.job_id == job_id)
        ).first()
        
        if not saved_job:
            return {"success": False, "message": "Cette offre n'est pas dans vos favoris"}
        
        db.delete(saved_job)
        db.commit()
        
        return {"success": True, "message": "Offre retirée des favoris"}
        
    except Exception as e:
        db.rollback()
        print(f"Error unsaving job: {str(e)}")
        return {"success": False, "message": "Erreur lors de la suppression"}

class ApplicationRequest(BaseModel):
    message: Optional[str] = None

@router.post("/api/jobs/{job_id}/apply")
async def apply_to_job(job_id: int, application_data: ApplicationRequest, request: Request, db: Session = Depends(get_db)):
    """Submit job application - requires authentication"""
    try:
        # Require authentication
        current_user = get_current_user(request, db)
        if not current_user:
            return {"success": False, "message": "Vous devez être connecté pour postuler à une offre"}
        
        # Check if job exists
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Get user's candidate profile
        candidate_profile = db.query(ProfileCandidat).filter(ProfileCandidat.user_id == current_user.id).first()
        if not candidate_profile:
            return {"success": False, "message": "Vous devez d'abord analyser votre CV pour créer votre profil candidat"}
        
        # Check if application already exists
        existing_application = db.query(Application).filter(
            and_(Application.job_id == job_id, Application.candidate_profile_id == candidate_profile.id)
        ).first()
        
        if existing_application:
            return {"success": False, "message": "Vous avez déjà postulé à cette offre"}

        URL = os.getenv("N8N_COMP_WEBHOOK_URL")
        print("Sending variable to n8n...")

        # Example variable (can be dict, list, etc.)
        data = get_compatibility_data(job_id, current_user.id)

        # Send JSON payload
        response = requests.post(URL, json=data)

        print("Status Code:", response.status_code)
        print("Response:", response.text)
        
        if response.status_code == 200:
            n8n_webhook_triggered = True
            compatibility_score = response.json().get("compatibility_score")
            compatibility_reason = response.json().get("reason")
            

        # Create new application
        new_application = Application(
            job_id=job_id,
            candidate_profile_id=candidate_profile.id,
            status='pending',
            source='job_portal',
            user_id=current_user.id,
            compatibility_score=compatibility_score,
            n8n_webhook_triggered=n8n_webhook_triggered,
            compatibility_reason=compatibility_reason
        )
        
        db.add(new_application)
        
        # Increment application count for the job
        job.applications_count = (job.applications_count or 0) + 1
        
        db.commit()
        
        print(f"Application created: Job {job_id}, User {current_user.id}, Candidate {candidate_profile.id}")
        
        return {
            "success": True, 
            "message": f"Candidature envoyée avec succès pour le poste '{job.title}'!",
            "application_id": new_application.id
        }
        
    except Exception as e:
        db.rollback()
        print(f"Error applying to job: {str(e)}")
        return {"success": False, "message": "Erreur lors de l'envoi de la candidature"}

@router.get("/api/jobs/{job_id}/application-status")
async def check_application_status(job_id: int, request: Request, db: Session = Depends(get_db)):
    """Check if user has already applied to this job"""
    try:
        current_user = get_current_user(request, db)
        if not current_user:
            return {"has_applied": False}
        
        application = db.query(Application).filter(
            and_(Application.job_id == job_id, Application.user_id == current_user.id)
        ).first()
        
        if application:
            return {
                "has_applied": True,
                "application_date": application.application_date.isoformat(),
                "status": application.status
            }
        else:
            return {"has_applied": False}
            
    except Exception as e:
        print(f"Error checking application status: {str(e)}")
        return {"has_applied": False}

@router.post("/api/applications/{application_id}/withdraw")
async def withdraw_application(application_id: int, request: Request, db: Session = Depends(get_db)):
    """Withdraw a job application"""
    try:
        current_user = get_current_user(request, db)
        if not current_user:
            return {"success": False, "message": "Vous devez être connecté"}
        
        # Get the application
        application = db.query(Application).filter(
            and_(
                Application.id == application_id,
                Application.user_id == current_user.id
            )
        ).first()
        
        if not application:
            return {"success": False, "message": "Candidature non trouvée"}
        
        # Check if application can be withdrawn
        if application.status in ['accepted', 'rejected', 'withdrawn']:
            return {"success": False, "message": "Cette candidature ne peut plus être retirée"}
        
        # Update application status
        application.status = 'withdrawn'
        db.commit()
        
        return {"success": True, "message": "Candidature retirée avec succès"}
        
    except Exception as e:
        db.rollback()
        print(f"Error withdrawing application: {str(e)}")
        return {"success": False, "message": "Erreur lors du retrait de la candidature"}



def get_compatibility_data(job_id: int, user_id: int):
    try:
        from database import SessionLocal
        db = SessionLocal()
        
        # Get job with related data
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            return {"error": "Job not found"}
        
        job_skills = db.query(JobSkill).filter(JobSkill.job_id == job_id).all()
        
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return {"error": "User not found"}
            
        candidate_profile = db.query(ProfileCandidat).filter(ProfileCandidat.user_id == user_id).first()
        if not candidate_profile:
            return {"error": "User profile not found"}
        
        company = db.query(Company).filter(Company.id == job.company_id).first()
        department = db.query(Department).filter(Department.id == job.department_id).first()
        
        # Build dictionary
        data = {
            "job": {
                "title": job.title,
                "company": company.company_name if company else None,
                "department": department.name if department else None,
                "industry": company.industry if company else None,
                "employment_type": job.employment_type,
                "priority_level": job.priority,
                "salary_range": f"{job.salary_min or 'N/A'} - {job.salary_max or 'N/A'} {job.currency}"
                                if job.salary_min or job.salary_max else None,
                "description": job.description,
                "requirements": job.requirements,
                "responsibilities": job.responsibilities,
                "skills": [
                    {
                        "name": skill.skill_name,
                        "level": skill.skill_level,
                        "status": "REQUIRED" if skill.is_required else "PREFERRED"
                    }
                    for skill in job_skills
                ]
            },
            "candidate": {
                "name": candidate_profile.name or f"{user.first_name} {user.last_name}",
                "title": candidate_profile.title or None,
                "years_of_experience": candidate_profile.yearOfExperience or 0,
                "summary": candidate_profile.profile or None,
                "education": candidate_profile.education if candidate_profile.education else [],
                "skills": candidate_profile.skills if candidate_profile.skills else [],
                "languages": candidate_profile.languages if candidate_profile.languages else [],
                "certifications": candidate_profile.certificates if candidate_profile.certificates else []
            }
        }
        
        return data
    
    except Exception as e:
        return {"error": str(e)}
    
    finally:
        if 'db' in locals():
            db.close()
