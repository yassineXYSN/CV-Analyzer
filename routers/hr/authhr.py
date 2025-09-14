from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import Optional, Dict, Any
import os
from databasehr.database import SessionLocal
from databasehr.models import HRAdmin
from auth_utils import authenticate_user
from company_utils import get_user_company
from databasehr.session_manager import current_user_session
from datetime import datetime
from jwt_utils import JWTManager, get_current_hr_user

# Création de l'objet templates
current_dir = os.path.dirname(os.path.abspath(__file__))
templates_dir = os.path.join(current_dir, '../../templates')  # Ajustez ce chemin selon votre structure
templates = Jinja2Templates(directory=templates_dir)  # Initialisation

router = APIRouter()

class LoginRequest(BaseModel):
    email: str
    password: str

class LoginResponse(BaseModel):
    success: bool
    message: str
    redirect_url: Optional[str] = None
    user: Optional[dict] = None
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    token_type: str = "bearer"

@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("client-dep/auth/client-login.html", {"request": request})

@router.get("/enterprise-login", response_class=HTMLResponse)
def hr_login_page(request: Request):
    return templates.TemplateResponse("HR-dep/auth/hr-login.html", {"request": request})

@router.post("/api/hr-login")
async def hr_login(login_data: LoginRequest):
    try:
        print(f"🔐 LOGIN API: Tentative de connexion pour {login_data.email}")
        user = authenticate_user(login_data.email, login_data.password)
        
        if not user:
            print(f"❌ LOGIN API: Authentification échouée")
            return LoginResponse(
                success=False,
                message="Email ou mot de passe incorrect"
            )
        
        print(f"✅ LOGIN API: Utilisateur authentifié - ID: {user['id']}")
        current_user_session['user_id'] = user['id']
        current_user_session['email'] = user['email']
        print(f"✅ LOGIN API: Session sauvegardée")
        
        db = SessionLocal()
        try:
            db_user = db.query(HRAdmin).filter(HRAdmin.email == login_data.email).first()
            if db_user:
                db_user.last_login = datetime.now()
                db.commit()
        except Exception as e:
            print(f"⚠️ LOGIN API: Erreur mise à jour last_login: {e}")
        finally:
            db.close()
        
        # Get user company first
        company = get_user_company(user['id'])
        
        # Create JWT tokens
        token_data = {
            "sub": str(user['id']),
            "email": user['email'],
            "role": "hr_admin",
            "company_id": str(company.id) if company else None
        }
        
        access_token = JWTManager.create_access_token(data=token_data)
        refresh_token = JWTManager.create_refresh_token(data=token_data)
        if not company:
            redirect_url = "/company-setup"
            message = "Configuration de l'entreprise requise"
        elif not company.setup_completed:
            redirect_url = "/company-setup"
            message = "Finalisation de la configuration requise"
        else:
            redirect_url = "/dashboard"
            message = "Connexion réussie"
        
        print(f"🎯 LOGIN API: Redirection vers {redirect_url}")
        return LoginResponse(
            success=True,
            message=message,
            redirect_url=redirect_url,
            user=user,
            access_token=access_token,
            refresh_token=refresh_token
        )
    except Exception as e:
        print(f"❌ LOGIN API: Erreur critique: {e}")
        import traceback
        traceback.print_exc()
        return LoginResponse(
            success=False,
            message="Erreur interne du serveur"
        )

@router.post("/api/hr-refresh-token")
async def refresh_token(refresh_token: str):
    """Refresh JWT access token"""
    try:
        # Verify refresh token
        payload = JWTManager.verify_token(refresh_token)
        
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")
        
        # Create new access token
        token_data = {
            "sub": payload.get("sub"),
            "email": payload.get("email"),
            "role": payload.get("role"),
            "company_id": payload.get("company_id")
        }
        
        new_access_token = JWTManager.create_access_token(data=token_data)
        
        return {
            "access_token": new_access_token,
            "token_type": "bearer"
        }
    except Exception as e:
        raise HTTPException(status_code=401, detail="Could not refresh token")

@router.post("/api/hr-logout")
async def hr_logout(current_user: Dict[str, Any] = Depends(get_current_hr_user)):
    """Logout HR user (in a real app, you'd blacklist the token)"""
    try:
        # Clear session if still using it
        current_user_session.clear()
        
        return {
            "success": True,
            "message": "Logged out successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail="Logout failed")

@router.get("/api/hr-me")
async def get_current_hr_profile(current_user: Dict[str, Any] = Depends(get_current_hr_user)):
    """Get current HR user profile"""
    try:
        db = SessionLocal()
        user_id = int(current_user.get("sub"))
        db_user = db.query(HRAdmin).filter(HRAdmin.id == user_id).first()
        
        if not db_user:
            raise HTTPException(status_code=404, detail="User not found")
        
        company = get_user_company(user_id)
        
        return {
            "id": db_user.id,
            "email": db_user.email,
            "name": db_user.name,
            "last_login": db_user.last_login,
            "company": {
                "id": company.id,
                "name": company.name,
                "setup_completed": company.setup_completed
            } if company else None
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()