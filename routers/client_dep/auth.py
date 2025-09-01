from fastapi import APIRouter, Request, Response, Form, Depends, UploadFile, File
from fastapi.responses import RedirectResponse, HTMLResponse
from database import SessionLocal
from databaseclient.models import User
from databaseclient.auth import authenticate_user, create_user_session, delete_user_session, create_user
from routers.client_dep.dependencies import get_db, get_current_user
from sqlalchemy.orm import Session
import os
import json
import httpx
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode
from databaseclient.insert_to_db import insert_candidate_data
from fastapi.templating import Jinja2Templates
from utils1.email_service import send_verification_email, generate_verification_token, get_verification_token_expiry
from datetime import datetime


router = APIRouter()
# Templates
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

# Chemin vers le dossier templates
templates_dir = os.path.join(BASE_DIR, "templates")

templates = Jinja2Templates(directory=templates_dir)

# n8n webhook URL (set N8N_AUTH_WEBHOOK_URL in env to override)
N8N_AUTH_WEBHOOK_URL = os.getenv("N8N_AUTH_WEBHOOK_URL")

# Optional polling endpoint if your n8n exposes one (leave empty if not used)
N8N_RESULT_URL = os.getenv("N8N_RESULT_URL")


# Helper functions from scan.py for n8n integration
def add_query_params(url: str, params: Dict[str, str]) -> str:
    parsed = urlparse(url)
    q = dict(parse_qsl(parsed.query, keep_blank_values=True))
    q.update(params)
    new_query = urlencode(q)
    return urlunparse((
        str(parsed.scheme) or '',
        str(parsed.netloc) or '',
        str(parsed.path) or '',
        str(parsed.params) or '',
        new_query,
        str(parsed.fragment) or ''
    ))

def to_prod_webhook(url: str) -> str:
    return url.replace("/webhook-test/", "/webhook/")


def first_item_if_list(data: Any) -> Any:
    if isinstance(data, list) and data:
        return data[0]
    return data


async def post_to_n8n_wait_for_json(
    url: str,
    file_name: str,
    file_bytes: bytes,
    content_type: Optional[str],
    selected_profiles: str,
    job_data: str = None,
    timeout_seconds: int = 180,
) -> Optional[dict]:
    """
    Post to n8n webhook and wait for JSON:
    - Adds wait=true to query string
    - Long timeout
    - Tries both test and prod paths
    - Includes job data for enhanced analysis
    """
    wait_url = add_query_params(url, {"wait": "true"})
    alt_wait_url = add_query_params(to_prod_webhook(url), {"wait": "true"})

    async with httpx.AsyncClient(timeout=timeout_seconds) as client:
        for target_url in (wait_url, alt_wait_url):
            try:
                files = {
                    "CV": (file_name, file_bytes, content_type or "application/pdf")
                }
                data = {
                    "selectedProfiles": selected_profiles,
                    "jobData": job_data or "[]",
                    "includeJobAnalysis": "true"  # Flag for n8n to include job-specific analysis
                }
                
                print(f"[v0] Sending to n8n: {target_url}")
                print(f"[v0] Job data being sent: {job_data}")
                
                resp = await client.post(target_url, files=files, data=data)

                if resp.status_code >= 400:
                    print(f"[v0] HTTP error {resp.status_code} for {target_url}")
                    continue

                ctype = (resp.headers.get("content-type") or "").lower()
                text = resp.text or ""
                if "application/json" in ctype:
                    try:
                        print(f"[v0] Received JSON response from n8n: {resp.text}")
                        return resp.json()
                    except Exception as e:
                        print(f"[v0] JSON parse error: {e}")
                        pass

                if text.strip().startswith("{") or text.strip().startswith("["):
                    try:
                        return json.loads(text)
                    except Exception as e:
                        print(f"[v0] JSON parse error on text: {e}")
                        pass
            except httpx.HTTPError as e:
                print(f"[v0] HTTP error for {target_url}: {e}")
                continue

    print("[v0] No valid response received from n8n")
    return None


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
    response: Response,
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
        
        # Create user (not verified yet)
        user = create_user(db, email, password, first_name, last_name)
        
        # Generate verification token
        verification_token = generate_verification_token()
        token_expiry = get_verification_token_expiry()
        
        # Update user with verification token
        user.verification_token = verification_token
        user.verification_token_expires = token_expiry
        db.commit()
        
        # Send verification email
        user_name = f"{first_name} {last_name}"
        email_sent = send_verification_email(email, user_name, verification_token)
        
        if not email_sent:
            return {"success": False, "message": "Erreur lors de l'envoi de l'email de vérification"}
        
        # Automatically log in the user (but they still need to verify email)
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
        
        return {"success": True, "redirect_url": "/auth/email-verification"}
        
    except Exception as e:
        print(f"Signup error: {str(e)}")
        return {"success": False, "message": "Erreur lors de la création du compte"}

@router.get("/auth/email-verification", response_class=HTMLResponse)
def email_verification_page(request: Request, db: Session = Depends(get_db)):
    current_user = get_current_user(request, db)
    if not current_user:
        return RedirectResponse(url="/login", status_code=302)
    
    # If already verified, redirect to step 2
    if current_user.is_verified:
        return RedirectResponse(url="/signup/step2", status_code=302)
    
    return templates.TemplateResponse("client-dep/auth/email-verification.html", {
        "request": request,
        "current_user": current_user,
        "user_email": current_user.email
    })

@router.get("/auth/verify-email")
async def verify_email(
    request: Request,
    token: str,
    db: Session = Depends(get_db)
):
    try:
        # Find user with this verification token
        user = db.query(User).filter(
            User.verification_token == token,
            User.verification_token_expires > datetime.utcnow()
        ).first()
        
        if not user:
            return templates.TemplateResponse("client-dep/auth/verification-error.html", {
                "request": request,
                "error": "Lien de vérification invalide ou expiré"
            })
        
        # Verify the user
        user.is_verified = 1
        user.verification_token = None
        user.verification_token_expires = None
        db.commit()
        
        return templates.TemplateResponse("client-dep/auth/verification-success.html", {
            "request": request,
            "user": user
        })
        
    except Exception as e:
        print(f"Email verification error: {str(e)}")
        return templates.TemplateResponse("client-dep/auth/verification-error.html", {
            "request": request,
            "error": "Erreur lors de la vérification"
        })

@router.post("/auth/resend-verification")
async def resend_verification(
    request: Request,
    db: Session = Depends(get_db)
):
    try:
        current_user = get_current_user(request, db)
        if not current_user:
            return {"success": False, "message": "Authentication required"}
        
        if current_user.is_verified:
            return {"success": False, "message": "Compte déjà vérifié"}
        
        # Generate new verification token
        verification_token = generate_verification_token()
        token_expiry = get_verification_token_expiry()
        
        # Update user with new verification token
        current_user.verification_token = verification_token
        current_user.verification_token_expires = token_expiry
        db.commit()
        
        # Send verification email
        user_name = f"{current_user.first_name} {current_user.last_name}"
        email_sent = send_verification_email(current_user.email, user_name, verification_token)
        
        if email_sent:
            return {"success": True, "message": "Email de vérification renvoyé"}
        else:
            return {"success": False, "message": "Erreur lors de l'envoi de l'email"}
            
    except Exception as e:
        print(f"Resend verification error: {str(e)}")
        return {"success": False, "message": "Erreur lors de l'envoi"}

@router.get("/signup/step2", response_class=HTMLResponse)
def signup_step2_page(request: Request, db: Session = Depends(get_db)):
    current_user = get_current_user(request, db)
    if not current_user:
        return RedirectResponse(url="/login", status_code=302)
    
    # Check if email is verified
    if not current_user.is_verified:
        return RedirectResponse(url="/auth/email-verification", status_code=302)
    
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

    # Save uploaded file
    os.makedirs("uploads", exist_ok=True)
    file_location = f"uploads/{filetoscan.filename}"
    file_bytes = await filetoscan.read()
    with open(file_location, "wb") as f:
        f.write(file_bytes)

    # Send to n8n and wait for JSON response
    n8n_data = await post_to_n8n_wait_for_json(
        N8N_AUTH_WEBHOOK_URL,
        filetoscan.filename,
        file_bytes,
        filetoscan.content_type,
        "general",  # Default profile for signup
        "[]",  # No job data for signup
        timeout_seconds=180,
    )

    # Optional: single poll on a result endpoint (if configured)
    if n8n_data is None and N8N_RESULT_URL:
        try:
            poll_url = add_query_params(N8N_RESULT_URL, {"filename": filetoscan.filename})
            async with httpx.AsyncClient(timeout=60) as client:
                r = await client.get(poll_url)
                if r.status_code < 400 and r.text.strip():
                    if "application/json" in (r.headers.get("content-type", "").lower()):
                        n8n_data = r.json()
                    elif r.text.strip().startswith("{") or r.text.strip().startswith("["):
                        n8n_data = json.loads(r.text)
        except Exception:
            n8n_data = None

    # Handle case where n8n doesn't respond
    if n8n_data is None:
        return {"success": False, "message": "CV processing failed. Please try again."}

    # Process n8n response
    n8n_data = first_item_if_list(n8n_data)
    if not isinstance(n8n_data, dict):
        n8n_data = {}

    # Extract data from n8n response
    summary: str = n8n_data.get("summary", "") or ""
    user_info: Dict[str, Any] = {
        "name": n8n_data.get("name", "") or "",
        "title": n8n_data.get("title", "") or "",
        "yearsOfExperience": n8n_data.get("yearsOfExperience", "0") or "0",
        "contact": n8n_data.get("contact", {}) or {"email": "", "phone": "", "linkedin": "", "address": ""},
        "profile": n8n_data.get("profile", "") or "",
        "education": n8n_data.get("education", []) or [],
        "languages": n8n_data.get("languages", []) or [],
        "certificates": n8n_data.get("certificates", []) or [],
        "skills": n8n_data.get("skills", []) or [],
        "strong_points": n8n_data.get("strong_points", []) or [],
        "weak_points": n8n_data.get("weak_points", []) or [],
        "scores": n8n_data.get("scores", {}) or {},
        "key_improvements": n8n_data.get("key_improvements", n8n_data.get("improvements", [])) or [],
    }

    # Insert candidate data and link to current user
    candidate_id = insert_candidate_data(user_info, summary, current_user.id)

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

# Social Authentication Routes
@router.get("/auth/google")
async def google_auth_redirect():
    """Redirect to Google OAuth"""
    try:
        # Google OAuth configuration
        google_client_id = os.getenv("GOOGLE_CLIENT_ID")
        google_redirect_uri = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/auth/google/callback")
        
        if not google_client_id:
            return {"success": False, "message": "Google OAuth non configuré"}
        
        # Google OAuth URL
        google_auth_url = f"https://accounts.google.com/o/oauth2/v2/auth"
        params = {
            "client_id": google_client_id,
            "redirect_uri": google_redirect_uri,
            "response_type": "code",
            "scope": "openid email profile",
            "access_type": "offline",
            "prompt": "consent"
        }
        
        # Build URL with parameters
        from urllib.parse import urlencode
        auth_url = f"{google_auth_url}?{urlencode(params)}"
        
        return RedirectResponse(url=auth_url)
        
    except Exception as e:
        print(f"Google auth error: {str(e)}")
        return {"success": False, "message": "Erreur lors de l'authentification Google"}

@router.get("/auth/google/callback")
async def google_auth_callback(request: Request, db: Session = Depends(get_db)):
    """Handle Google OAuth callback"""
    try:
        # Get authorization code from query parameters
        code = request.query_params.get("code")
        if not code:
            return {"success": False, "message": "Code d'autorisation manquant"}
        
        # Exchange code for access token
        google_client_id = os.getenv("GOOGLE_CLIENT_ID")
        google_client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
        google_redirect_uri = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/auth/google/callback")
        
        if not google_client_id or not google_client_secret:
            return {"success": False, "message": "Google OAuth non configuré"}
        
        # Exchange code for tokens
        token_url = "https://oauth2.googleapis.com/token"
        token_data = {
            "client_id": google_client_id,
            "client_secret": google_client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": google_redirect_uri
        }
        
        async with httpx.AsyncClient() as client:
            token_response = await client.post(token_url, data=token_data)
            
            if token_response.status_code != 200:
                return {"success": False, "message": "Erreur lors de l'échange du code"}
            
            token_info = token_response.json()
            access_token = token_info.get("access_token")
            
            if not access_token:
                return {"success": False, "message": "Token d'accès manquant"}
            
            # Get user info from Google
            userinfo_url = "https://www.googleapis.com/oauth2/v2/userinfo"
            headers = {"Authorization": f"Bearer {access_token}"}
            
            userinfo_response = await client.get(userinfo_url, headers=headers)
            
            if userinfo_response.status_code != 200:
                return {"success": False, "message": "Erreur lors de la récupération des informations utilisateur"}
            
            user_info = userinfo_response.json()
            
            # Extract user data
            google_id = user_info.get("id")
            email = user_info.get("email")
            first_name = user_info.get("given_name", "")
            last_name = user_info.get("family_name", "")
            profile_picture = user_info.get("picture")
            
            if not google_id or not email:
                return {"success": False, "message": "Informations utilisateur incomplètes"}
            
            # Check if user exists
            existing_user = db.query(User).filter(
                (User.email == email) | (User.google_id == google_id)
            ).first()
            
            if existing_user:
                # Update existing user with Google info
                existing_user.google_id = google_id
                existing_user.profile_picture = profile_picture
                existing_user.is_verified = True
                db.commit()
                user = existing_user
            else:
                # Create new user
                new_user = User(
                    email=email,
                    first_name=first_name,
                    last_name=last_name,
                    google_id=google_id,
                    profile_picture=profile_picture,
                    is_verified=True,
                    is_active=True
                )
                db.add(new_user)
                db.commit()
                db.refresh(new_user)
                user = new_user
            
            # Create session
            session_token = create_user_session(db, user.id, True)
            
            # Redirect to dashboard with session
            response = RedirectResponse(url="/analyze")
            response.set_cookie(
                key="session_token",
                value=session_token,
                max_age=30 * 24 * 60 * 60,  # 30 days
                httponly=True,
                secure=False,
                samesite="lax"
            )
            
            return response
            
    except Exception as e:
        print(f"Google callback error: {str(e)}")
        return {"success": False, "message": "Erreur lors de l'authentification Google"}

@router.get("/auth/microsoft")
async def microsoft_auth_redirect():
    """Redirect to Microsoft OAuth"""
    try:
        # Microsoft OAuth configuration
        microsoft_client_id = os.getenv("MICROSOFT_CLIENT_ID")
        microsoft_redirect_uri = os.getenv("MICROSOFT_REDIRECT_URI", "http://localhost:8000/auth/microsoft/callback")
        
        if not microsoft_client_id:
            return {"success": False, "message": "Microsoft OAuth non configuré"}
        
        # Microsoft OAuth URL
        microsoft_auth_url = "https://login.microsoftonline.com/common/oauth2/v2.0/authorize"
        params = {
            "client_id": microsoft_client_id,
            "redirect_uri": microsoft_redirect_uri,
            "response_type": "code",
            "scope": "openid email profile",
            "response_mode": "query"
        }
        
        # Build URL with parameters
        from urllib.parse import urlencode
        auth_url = f"{microsoft_auth_url}?{urlencode(params)}"
        
        return RedirectResponse(url=auth_url)
        
    except Exception as e:
        print(f"Microsoft auth error: {str(e)}")
        return {"success": False, "message": "Erreur lors de l'authentification Microsoft"}

@router.get("/auth/microsoft/callback")
async def microsoft_auth_callback(request: Request, db: Session = Depends(get_db)):
    """Handle Microsoft OAuth callback"""
    try:
        # Get authorization code from query parameters
        code = request.query_params.get("code")
        if not code:
            return {"success": False, "message": "Code d'autorisation manquant"}
        
        # Exchange code for access token
        microsoft_client_id = os.getenv("MICROSOFT_CLIENT_ID")
        microsoft_client_secret = os.getenv("MICROSOFT_CLIENT_SECRET")
        microsoft_redirect_uri = os.getenv("MICROSOFT_REDIRECT_URI", "http://localhost:8000/auth/microsoft/callback")
        
        if not microsoft_client_id or not microsoft_client_secret:
            return {"success": False, "message": "Microsoft OAuth non configuré"}
        
        # Exchange code for tokens
        token_url = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
        token_data = {
            "client_id": microsoft_client_id,
            "client_secret": microsoft_client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": microsoft_redirect_uri
        }
        
        async with httpx.AsyncClient() as client:
            token_response = await client.post(token_url, data=token_data)
            
            if token_response.status_code != 200:
                return {"success": False, "message": "Erreur lors de l'échange du code"}
            
            token_info = token_response.json()
            access_token = token_info.get("access_token")
            
            if not access_token:
                return {"success": False, "message": "Token d'accès manquant"}
            
            # Get user info from Microsoft
            userinfo_url = "https://graph.microsoft.com/v1.0/me"
            headers = {"Authorization": f"Bearer {access_token}"}
            
            userinfo_response = await client.get(userinfo_url, headers=headers)
            
            if userinfo_response.status_code != 200:
                return {"success": False, "message": "Erreur lors de la récupération des informations utilisateur"}
            
            user_info = userinfo_response.json()
            
            # Extract user data
            microsoft_id = user_info.get("id")
            email = user_info.get("mail") or user_info.get("userPrincipalName")
            first_name = user_info.get("givenName", "")
            last_name = user_info.get("surname", "")
            
            if not microsoft_id or not email:
                return {"success": False, "message": "Informations utilisateur incomplètes"}
            
            # Check if user exists
            existing_user = db.query(User).filter(User.email == email).first()
            
            if existing_user:
                # Update existing user
                existing_user.is_verified = True
                db.commit()
                user = existing_user
            else:
                # Create new user
                new_user = User(
                    email=email,
                    first_name=first_name,
                    last_name=last_name,
                    is_verified=True,
                    is_active=True
                )
                db.add(new_user)
                db.commit()
                db.refresh(new_user)
                user = new_user
            
            # Create session
            session_token = create_user_session(db, user.id, True)
            
            # Redirect to dashboard with session
            response = RedirectResponse(url="/analyze")
            response.set_cookie(
                key="session_token",
                value=session_token,
                max_age=30 * 24 * 60 * 60,  # 30 days
                httponly=True,
                secure=False,
                samesite="lax"
            )
            
            return response
            
    except Exception as e:
        print(f"Microsoft callback error: {str(e)}")
        return {"success": False, "message": "Erreur lors de l'authentification Microsoft"}
