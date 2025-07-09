from fastapi import APIRouter, Request, UploadFile, File, Depends, HTTPException
from fastapi.responses import HTMLResponse
from database import SessionLocal
from models import ProfileCandidat, Contact, AnalyseCandidat
from routers.client_dep.dependencies import get_db, get_current_user, require_auth
import json
import re
from sqlalchemy.orm import Session
import models
import os
from fastapi.templating import Jinja2Templates
from models import User

router = APIRouter()
# Templates
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

# Chemin vers le dossier templates
templates_dir = os.path.join(BASE_DIR, "templates")

templates = Jinja2Templates(directory=templates_dir)


def parse_skills(skills_data):
    """Parse skills list to extract name and percentage"""
    if not skills_data:
        return []
    
    # Si c'est une string JSON, la parser
    if isinstance(skills_data, str):
        try:
            skills_list = json.loads(skills_data)
        except:
            return []
    else:
        skills_list = skills_data
    
    if not isinstance(skills_list, list):
        return []
    
    parsed_skills = []
    for skill in skills_list:
        try:
            skill_str = str(skill)
            if ':' in skill_str:
                parts = skill_str.split(':')
                name = parts[0].strip()
                level_str = parts[1].strip()
                # Extract percentage number
                percentage_match = re.search(r'(\d+)', level_str)
                percentage = int(percentage_match.group(1)) if percentage_match else 0
                parsed_skills.append({
                    'name': name,
                    'level_str': level_str,
                    'percentage': min(percentage, 100)  # Cap at 100%
                })
            else:
                parsed_skills.append({
                    'name': skill_str.strip(),
                    'level_str': '',
                    'percentage': 0
                })
        except Exception as e:
            print(f"Erreur parsing skill {skill}: {e}")
            parsed_skills.append({
                'name': str(skill),
                'level_str': '',
                'percentage': 0
            })
    return parsed_skills

@router.get("/profile/{candidate_id}", response_class=HTMLResponse)
def profile_detail(request: Request, candidate_id: int, db: Session = Depends(get_db)):
    current_user = get_current_user(request, db)
    
    try:
        # Récupérer les données du candidat depuis la base
        profile = db.query(models.ProfileCandidat).filter(models.ProfileCandidat.id == candidate_id).first()
        if not profile:
            print(f"Profile not found for ID: {candidate_id}")
            return templates.TemplateResponse("client-dep/profile_detail.html", {
                "request": request,
                "profile": None,
                "contact": None,
                "analyse": None,
                "parsed_skills": [],
                "current_user": current_user
            })
        
        contact = db.query(models.Contact).filter(models.Contact.id == profile.contact_id).first()
        analyse = db.query(models.AnalyseCandidat).filter(models.AnalyseCandidat.id == profile.analyse_id).first()

        
        # Parse skills to extract percentages
        parsed_skills = parse_skills(profile.skills)
        
        # Récupérer les valeurs des attributs d'abord
        education_value = getattr(profile, 'education', None)
        languages_value = getattr(profile, 'languages', None)
        certificates_value = getattr(profile, 'certificates', None)
        
        # Parse education if it's a JSON string
        parsed_education = []
        if education_value:
            try:
                if isinstance(education_value, str):
                    parsed_education = json.loads(education_value)
                else:
                    parsed_education = education_value
            except:
                parsed_education = []
        
        # Parse languages if it's a JSON string
        parsed_languages = []
        if languages_value:
            try:
                if isinstance(languages_value, str):
                    parsed_languages = json.loads(languages_value)
                else:
                    parsed_languages = languages_value
            except:
                parsed_languages = []
        
        # Parse certificates if it's a JSON string
        parsed_certificates = []
        if certificates_value:
            try:
                if isinstance(certificates_value, str):
                    parsed_certificates = json.loads(certificates_value)
                else:
                    parsed_certificates = certificates_value
            except:
                parsed_certificates = []
        
        # Create a simple object to hold profile data
        class ProfileData:
            def __init__(self, **kwargs):
                for key, value in kwargs.items():
                    setattr(self, key, value)

        profile_data = ProfileData(
            id=profile.id,
            name=profile.name,
            title=profile.title,
            profile=profile.profile,
            education=parsed_education,
            languages=parsed_languages,
            certificates=parsed_certificates,
            years_of_experience=profile.yearOfExperience,
            profile_picture=profile.profile_picture,
            experience=getattr(profile, 'experience', None),
            projects=getattr(profile, 'projects', None),
            hobbies=getattr(profile, 'hobbies', None),
            references=getattr(profile, 'references', None),
            additional_info=getattr(profile, 'additional_info', None)
        )

        print(f"Profile found: {profile.name}")
        print(f"Parsed skills: {parsed_skills}")
        print(f"Parsed education: {parsed_education}")

        return templates.TemplateResponse("client-dep/profile_detail.html", {
            "request": request,
            "profile": profile_data,
            "contact": contact,
            "analyse": analyse,
            "parsed_skills": parsed_skills,
            "current_user": current_user
        })
    except Exception as e:
        print(f"Erreur dans profile_detail: {e}")
        import traceback
        traceback.print_exc()
        return templates.TemplateResponse("client-dep/profile_detail.html", {
            "request": request,
            "profile": None,
            "contact": None,
            "analyse": None,
            "parsed_skills": [],
            "current_user": current_user
        })

@router.get("/profile/by_user/{user_id}", response_class=HTMLResponse)
def profile_by_user_id(request: Request, user_id: int, db: Session = Depends(get_db)):
    current_user = get_current_user(request, db)

    try:
        # Find the candidate profile by user_id
        profile = db.query(models.ProfileCandidat).filter(models.ProfileCandidat.user_id == user_id).first()
        if not profile:
            print(f"Profile not found for user ID: {user_id}")
            return templates.TemplateResponse("client-dep/profile_detail.html", {
                "request": request,
                "profile": None,
                "contact": None,
                "analyse": None,
                "parsed_skills": [],
                "current_user": current_user
            })

        contact = db.query(models.Contact).filter(models.Contact.id == profile.contact_id).first()
        analyse = db.query(models.AnalyseCandidat).filter(models.AnalyseCandidat.id == profile.analyse_id).first()
        parsed_skills = parse_skills(profile.skills)

        # Parse fields
        def parse_json_field(field):
            try:
                if isinstance(field, str):
                    return json.loads(field)
                return field
            except:
                return []

        parsed_education = parse_json_field(profile.education)
        parsed_languages = parse_json_field(profile.languages)
        parsed_certificates = parse_json_field(profile.certificates)

        class ProfileData:
            def __init__(self, **kwargs):
                for key, value in kwargs.items():
                    setattr(self, key, value)

        profile_data = ProfileData(
            id=profile.id,
            name=profile.name,
            title=profile.title,
            profile=profile.profile,
            education=parsed_education,
            languages=parsed_languages,
            certificates=parsed_certificates,
            years_of_experience=profile.yearOfExperience,
            profile_picture=profile.profile_picture,
            experience=getattr(profile, 'experience', None),
            projects=getattr(profile, 'projects', None),
            hobbies=getattr(profile, 'hobbies', None),
            references=getattr(profile, 'references', None),
            additional_info=getattr(profile, 'additional_info', None)
        )

        return templates.TemplateResponse("client-dep/profile_detail.html", {
            "request": request,
            "profile": profile_data,
            "contact": contact,
            "analyse": analyse,
            "parsed_skills": parsed_skills,
            "current_user": current_user
        })

    except Exception as e:
        print(f"Erreur dans profile_by_user_id: {e}")
        import traceback
        traceback.print_exc()
        return templates.TemplateResponse("client-dep/profile_detail.html", {
            "request": request,
            "profile": None,
            "contact": None,
            "analyse": None,
            "parsed_skills": [],
            "current_user": current_user
        })

@router.post("/profile/{candidate_id}/upload-picture")
async def upload_profile_picture(
    candidate_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_auth)
):
    # Check if the candidate profile belongs to the current user
    profile = db.query(models.ProfileCandidat).filter(
        models.ProfileCandidat.id == candidate_id,
        models.ProfileCandidat.user_id == current_user.id
    ).first()
    
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    # Create upload directory if not exists
    os.makedirs("static/uploads/profile_pictures", exist_ok=True)
    
    # Generate unique filename
    file_ext = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = f"static/uploads/profile_pictures/{unique_filename}"
    
    # Save the file
    with open(file_path, "wb") as f:
        f.write(await file.read())
    
    # Update profile in database
    profile.profile_picture = f"/{file_path}"  # Store relative path
    db.commit()
    
    return {"success": True, "profile_picture": profile.profile_picture}
