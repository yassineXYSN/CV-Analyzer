from fastapi import APIRouter, Request, Response, Form, Depends, UploadFile, File, Header, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
from database import SessionLocal
from databaseclient.models import User, HRGoogleToken
from databaseclient.auth import authenticate_user, create_user_session, delete_user_session, create_user
from routers.client_dep.dependencies import get_db, get_current_user
from sqlalchemy.orm import Session
import os
import json
import httpx
import requests
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode
from databaseclient.insert_to_db import insert_candidate_data
from fastapi.templating import Jinja2Templates
from utils1.email_service import send_verification_email, generate_verification_token, get_verification_token_expiry
from datetime import datetime, timezone, timedelta
from jwt_utils import JWTManager


router = APIRouter()
# Templates
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

# Chemin vers le dossier templates
templates_dir = os.path.join(BASE_DIR, "templates")

templates = Jinja2Templates(directory=templates_dir)

# n8n webhook URL (set N8N_AUTH_WEBHOOK_URL in env to override)
N8N_AUTH_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL")+"/profile-creation"


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
    
    # Récupérer l'URL de redirection après login
    redirect_to = request.query_params.get("redirect_to", "/analyze")
    return templates.TemplateResponse("client-dep/auth/login.html", {
        "request": request,
        "redirect_to": redirect_to
    })

@router.post("/login")
async def login(
    request: Request,
    response: Response,
    email: str = Form(...),
    password: str = Form(...),
    remember_me: bool = Form(False),
    redirect_to: str = Form("/analyze"),
    db: Session = Depends(get_db)
):
    try:
        user = authenticate_user(db, email, password)
        if not user:
            return {"success": False, "message": "Email ou mot de passe incorrect"}
        
        if not user.is_active:
            return {"success": False, "message": "Compte désactivé"}
        
        # Create session (kept for existing flows)
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

        # Issue JWT tokens
        token_data = {"sub": str(user.id), "email": user.email, "role": "client"}
        access_token = JWTManager.create_access_token(data=token_data)
        refresh_token = JWTManager.create_refresh_token(data=token_data)
        
        return {
            "success": True,
            "message": "Connexion réussie",
            "redirect_to": redirect_to,
            "user": {
                "id": user.id,
                "email": user.email,
                "first_name": getattr(user, "first_name", None),
                "last_name": getattr(user, "last_name", None),
            },
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }
        
    except Exception as e:
        print(f"Login error: {str(e)}")
        return {"success": False, "message": "Erreur lors de la connexion"}


@router.post("/api/client-refresh-token")
async def client_refresh_token(refresh_token: str):
    try:
        payload = JWTManager.verify_token(refresh_token)
        if payload.get("type") != "refresh" or payload.get("role") != "client":
            raise HTTPException(status_code=401, detail="Invalid token type")
        token_data = {"sub": payload.get("sub"), "email": payload.get("email"), "role": "client"}
        new_access = JWTManager.create_access_token(data=token_data)
        return {"access_token": new_access, "token_type": "bearer"}
    except Exception:
        raise HTTPException(status_code=401, detail="Could not refresh token")


@router.get("/api/client-me")
async def client_me(authorization: str = Header(None), db: Session = Depends(get_db)):
    try:
        if not authorization or not authorization.lower().startswith("bearer "):
            raise HTTPException(status_code=401, detail="Missing token")
        token = authorization.split(" ", 1)[1]
        payload = JWTManager.verify_token(token)
        if payload.get("role") != "client":
            raise HTTPException(status_code=403, detail="Not enough permissions")
        user_id = int(payload.get("sub"))
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return {
            "success": True,
            "user": {
                "id": user.id,
                "email": user.email,
                "first_name": getattr(user, "first_name", None),
                "last_name": getattr(user, "last_name", None),
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.post("/api/client-logout")
async def client_logout():
    return {"success": True, "message": "Logged out"}

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
        
        # Create a session for the user after verification
        session_token = create_user_session(db, user.id, remember_me=False)
        
        # Create response with session cookie
        response = templates.TemplateResponse("client-dep/auth/verification-success.html", {
            "request": request,
            "user": user
        })
        
        # Set session cookie
        response.set_cookie(
            key="session_token",
            value=session_token,
            max_age=24 * 60 * 60,  # 24 hours
            httponly=True,
            secure=False,
            samesite="lax"
        )
        
        return response
        
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
        google_client_id = os.getenv("GOOGLE_CLIENT_ID", "603669455866-ke5hutefk7fp474dt65vfo0mp39sh3i3.apps.googleusercontent.com")
        google_redirect_uri = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/auth/google/callback")
        
        if not google_client_id:
            print("❌ Google OAuth: GOOGLE_CLIENT_ID manquant")
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
        
        print(f"🔄 Google OAuth: Redirection vers {auth_url}")
        return RedirectResponse(url=auth_url)
        
    except Exception as e:
        print(f"Google auth error: {str(e)}")
        return {"success": False, "message": "Erreur lors de l'authentification Google"}

@router.get("/callback")
async def google_auth_callback_redirect_simple(request: Request, db: Session = Depends(get_db)):
    """Redirect callback vers le callback Google principal"""
    # Rediriger vers le callback Google principal avec tous les paramètres
    query_params = str(request.query_params)
    return RedirectResponse(f"/auth/google/callback?{query_params}")


@router.get("/auth/callback")
async def google_auth_callback_redirect(request: Request, db: Session = Depends(get_db)):
    """Redirect callback vers le callback Google principal"""
    # Rediriger vers le callback Google principal avec tous les paramètres
    query_params = str(request.query_params)
    return RedirectResponse(f"/auth/google/callback?{query_params}")


@router.get("/auth/google/callback")
async def google_auth_callback(request: Request, db: Session = Depends(get_db)):
    """Handle Google OAuth callback - both client and HR"""
    try:
        # Get authorization code and state from query parameters
        code = request.query_params.get("code")
        state = request.query_params.get("state")
        
        if not code:
            return {"success": False, "message": "Code d'autorisation manquant"}
        
        # Vérifier si c'est un callback HR (state contient un ID utilisateur numérique)
        if state and state.isdigit():
            print(f"🔄 Google OAuth Callback: Détection callback HR pour state: {state}")
            # Traiter directement le callback HR
            return await handle_hr_google_callback(code, state, db)
        
        print(f"🔄 Google OAuth Callback: Traitement callback client normal")
        
        # Exchange code for access token
        google_client_id = os.getenv("GOOGLE_CLIENT_ID", "603669455866-ke5hutefk7fp474dt65vfo0mp39sh3i3.apps.googleusercontent.com")
        google_client_secret = os.getenv("GOOGLE_CLIENT_SECRET", "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")
        google_redirect_uri = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/auth/google/callback")
        
        if not google_client_id or not google_client_secret:
            print(f"❌ Google OAuth Callback: GOOGLE_CLIENT_ID={bool(google_client_id)}, GOOGLE_CLIENT_SECRET={bool(google_client_secret)}")
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
        
        print(f"🔄 Google OAuth Callback: Échange du code contre token...")
        async with httpx.AsyncClient() as client:
            token_response = await client.post(token_url, data=token_data)
            
            print(f"🔄 Google OAuth Callback: Status {token_response.status_code}")
            if token_response.status_code != 200:
                print(f"❌ Google OAuth Callback: Erreur échange - {token_response.text}")
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


async def handle_hr_google_callback(code: str, state: str, db: Session):
    """
    Traite le callback Google OAuth pour les HR agents
    """
    try:
        print(f"🔄 HR Google OAuth Callback: Code reçu, State: {state}")
        
        # Vérifier si c'est un callback HR (state contient un ID utilisateur numérique)
        user_id = None
        if state and state.isdigit():
            user_id = int(state)
            print(f"✅ HR Google OAuth Callback: User ID extrait du state: {user_id}")
        else:
            print(f"❌ HR Google OAuth Callback: State invalide ou manquant: {state}")
            return RedirectResponse("/dashboard?error=invalid_state")
        
        # Configuration Google OAuth - utiliser les variables d'environnement (même que le callback existant)
        GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "603669455866-m2sqvd5s7qdmlcua4o6fvrsb42iqr1bb.apps.googleusercontent.com")
        GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "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")
        GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/auth/google/callback")
        GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
        
        # Échanger le code contre un token d'accès
        data = {
            "code": code,
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "redirect_uri": GOOGLE_REDIRECT_URI,
            "grant_type": "authorization_code",
        }
        
        print(f"🔄 HR Google OAuth Callback: Échange du code contre token...")
        r = requests.post(GOOGLE_TOKEN_URL, data=data, timeout=15)
        
        if r.status_code != 200:
            print(f"❌ HR Google OAuth Callback: Échec échange code - Status: {r.status_code}")
            print(f"❌ HR Google OAuth Callback: Response: {r.text}")
            return RedirectResponse("/dashboard?error=google_auth_failed&message=Erreur de configuration Google OAuth. Veuillez vérifier que l'URL de redirection http://localhost:8000/auth/google/callback est configurée dans Google Cloud Console pour le client ID 603669455866-ke5hutefk7fp474dt65vfo0mp39sh3i3.apps.googleusercontent.com")
        
        token_data = r.json()
        print(f"✅ HR Google OAuth Callback: Token reçu: {list(token_data.keys())}")
        
        # Sauvegarder les tokens
        save_hr_tokens(db, user_id, token_data)
        print(f"✅ HR Google OAuth Callback: Tokens sauvegardés pour user_id: {user_id}")
        
        return RedirectResponse("/dashboard?connected=google&message=Google Calendar connecté avec succès !")
        
    except Exception as e:
        print(f"❌ HR Google OAuth Callback Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return RedirectResponse("/dashboard?error=google_auth_failed&message=Erreur lors de la connexion Google Calendar")


def save_hr_tokens(db: Session, hr_admin_id: int, token_data: dict):
    """
    Sauvegarde les tokens Google OAuth pour un HR admin
    """
    access_token = token_data.get("access_token")
    refresh_token = token_data.get("refresh_token")
    token_type = token_data.get("token_type")
    scope = token_data.get("scope")
    expires_in = token_data.get("expires_in")

    expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in or 0)

    record = db.query(HRGoogleToken).filter(HRGoogleToken.hr_admin_id == hr_admin_id).first()
    if not record:
        record = HRGoogleToken(
            hr_admin_id=hr_admin_id,
            access_token=access_token,
            refresh_token=refresh_token,
            token_type=token_type,
            scope=scope,
            expires_at=expires_at,
        )
        db.add(record)
    else:
        record.access_token = access_token
        if refresh_token:
            record.refresh_token = refresh_token
        record.token_type = token_type
        record.scope = scope
        record.expires_at = expires_at
    db.commit()
