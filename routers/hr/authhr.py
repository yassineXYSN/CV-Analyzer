from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates  # Import ajouté
from pydantic import BaseModel
from typing import Optional
import os  # Import ajouté pour la gestion des chemins
from databasehr.database import SessionLocal
from databasehr.models import HRAdmin
from auth_utils import authenticate_user
from company_utils import get_user_company
from databasehr.session_manager import current_user_session
from datetime import datetime

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

@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("client-dep/auth/client-login.html", {"request": request})

@router.get("/hr-login", response_class=HTMLResponse)
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
        
        company = get_user_company(user['id'])
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
            user=user
        )
    except Exception as e:
        print(f"❌ LOGIN API: Erreur critique: {e}")
        import traceback
        traceback.print_exc()
        return LoginResponse(
            success=False,
            message="Erreur interne du serveur"
        )