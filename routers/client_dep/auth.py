from fastapi import APIRouter, Request, Response, Form, Depends, UploadFile, File
from fastapi.responses import RedirectResponse, HTMLResponse
from database import SessionLocal
from models import User
from auth import authenticate_user, create_user_session, delete_user_session, create_user
from routers.client_dep.dependencies import get_db, get_current_user
from sqlalchemy.orm import Session
import os
import extract_information_cv.text_extractor as text_extractor
import extract_information_cv.textcleaner as textcleaner
import cv_analyzer.data_generator as data_generator
from insert_to_db import insert_candidate_data
from fastapi.templating import Jinja2Templates


router = APIRouter()
# Templates
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

# Chemin vers le dossier templates
templates_dir = os.path.join(BASE_DIR, "templates")

templates = Jinja2Templates(directory=templates_dir)


# Authentication routes
@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request, db: Session = Depends(get_db)):
    current_user = get_current_user(request, db)
    if current_user:
        return RedirectResponse(url="/", status_code=302)
    return templates.TemplateResponse("client-dep/auth/login.html", {"request": request})

@router.post("/login")
async def login(
    request: Request,
    response: Response,
    email: str = Form(...),
    password: str = Form(...),
    remember_me: bool = Form(False),
    db: Session = Depends(get_db)
):
    try:
        user = authenticate_user(db, email, password)
        if not user:
            return {"success": False, "message": "Email ou mot de passe incorrect"}
        
        if not user.is_active:
            return {"success": False, "message": "Compte désactivé"}
        
        # Create session
        session_token = create_user_session(db, user.id, remember_me)
        
        # Set cookie
        max_age = 30 * 24 * 60 * 60 if remember_me else 24 * 60 * 60  # 30 days or 1 day
        response.set_cookie(
            key="session_token",
            value=session_token,
            max_age=max_age,
            httponly=True,
            secure=False,  # Set to True in production with HTTPS
            samesite="lax"
        )
        
        return {"success": True, "message": "Connexion réussie"}
        
    except Exception as e:
        print(f"Login error: {str(e)}")
        return {"success": False, "message": "Erreur lors de la connexion"}

@router.get("/signup", response_class=HTMLResponse)
def signup_page(request: Request, db: Session = Depends(get_db)):
    current_user = get_current_user(request, db)
    if current_user:
        return RedirectResponse(url="/", status_code=302)
    return templates.TemplateResponse("client-dep/auth/signup.html", {"request": request})

@router.post("/signup")
async def signup(
    request: Request,
    response: Response,  # Add response parameter
    first_name: str = Form(...),
    last_name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
    db: Session = Depends(get_db)
):
    try:
        # Validation
        if password != confirm_password:
            return {"success": False, "message": "Les mots de passe ne correspondent pas"}
        
        if len(password) < 8:
            return {"success": False, "message": "Le mot de passe doit contenir au moins 8 caractères"}
        
        # Check if user exists
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            return {"success": False, "message": "Un compte avec cet email existe déjà"}
        
        # Create user
        # Create user
        user = create_user(db, email, password, first_name, last_name)
        
        # Automatically log in the user
        session_token = create_user_session(db, user.id, remember_me=False)
        
        # Set session cookie
        response.set_cookie(
            key="session_token",
            value=session_token,
            max_age=24 * 60 * 60,  # 1 day
            httponly=True,
            secure=False,  # Set to True in production with HTTPS
            samesite="lax"
        )
        
        return {"success": True, "redirect_url": "/signup/step2"}
        
    except Exception as e:
        print(f"Signup error: {str(e)}")
        return {"success": False, "message": "Erreur lors de la création du compte"}
    
# Add new signup step routes
@router.get("/signup/step2", response_class=HTMLResponse)
def signup_step2_page(request: Request, db: Session = Depends(get_db)):
    current_user = get_current_user(request, db)
    if not current_user:
        return RedirectResponse(url="/login", status_code=302)
    if current_user.profile:
        return RedirectResponse(url="/", status_code=302)
    return templates.TemplateResponse("client-dep/auth/signup-step2.html", {
        "request": request,
        "current_user": current_user
    })

@router.post("/signup/step2")
async def signup_step2(
    request: Request,
    response: Response,
    filetoscan: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    current_user = get_current_user(request, db)
    if not current_user:
        return {"success": False, "message": "Authentication required"}

        
    # Créer le dossier uploads s'il n'existe pas
    os.makedirs("uploads", exist_ok=True)
    
    file_location = f"uploads/{filetoscan.filename}"

    # Save file to disk temporarily
    with open(file_location, "wb") as f:
        f.write(await filetoscan.read())

    # Process the file
    pdf_text, images_text = text_extractor.process_file(file_location)

    # Clean up
    pdf_text = textcleaner.cleantext(pdf_text)

    # Generate summary
    summary = data_generator.generate_summary(pdf_text,images_text)

    data_json = data_generator.generate_json(pdf_text)

    # Insérer les données en base et lier au user si connecté
    candidate_id = insert_candidate_data(data_json, summary, current_user.id)

    # Redirect to profile detail page
    return RedirectResponse(url=f"/profile/{candidate_id}", status_code=303)


@router.post("/logout")
async def logout(request: Request, response: Response, db: Session = Depends(get_db)):
    session_token = request.cookies.get("session_token")
    if session_token:
        delete_user_session(db, session_token)
    
    response.delete_cookie("session_token")
    return templates.TemplateResponse("client-dep/index.html", {
        "request": request,
        "current_user": None
    })

@router.get("/api/auth/status")
async def auth_status(request: Request, db: Session = Depends(get_db)):
    try:
        current_user = get_current_user(request, db)
        if current_user:
            return {
                "authenticated": True,
                "user": {
                    "id": current_user.id,
                    "email": current_user.email,
                    "first_name": current_user.first_name,
                    "last_name": current_user.last_name,
                    "name": f"{current_user.first_name} {current_user.last_name}".strip(),
                    "is_active": current_user.is_active,
                    "profile_picture": current_user.profile_picture  ,
                    "profile": current_user.profile
                }
            }
        else:
            return {"authenticated": False}
    except Exception as e:
        print(f"Auth status error: {str(e)}")
        return {"authenticated": False}
