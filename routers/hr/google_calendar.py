import json
from datetime import datetime, timedelta, timezone
from typing import Optional

import requests
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse

from database import SessionLocal
from databaseclient.models import HRGoogleToken
from databasehr.session_manager import current_user_session

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_user_id_from_request(request: Request) -> Optional[int]:
    """
    Récupère l'ID utilisateur depuis les cookies JWT ou les headers d'autorisation.
    """
    user_id = None
    
    # Essayer d'abord les cookies
    access_token = request.cookies.get('hr_access_token')
    
    # Si pas de cookie, essayer les headers d'autorisation
    if not access_token:
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            access_token = auth_header[7:]  # Enlever "Bearer "
    
    if access_token:
        try:
            from jwt_utils import JWTManager
            payload = JWTManager.verify_token(access_token)
            user_id = int(payload.get('sub'))
            print(f"✅ User ID récupéré depuis token: {user_id}")
        except Exception as e:
            print(f"⚠️ Erreur vérification token: {e}")
    
    return user_id


GOOGLE_CLIENT_ID = "603669455866-ke5hutefk7fp474dt65vfo0mp39sh3i3.apps.googleusercontent.com"
GOOGLE_CLIENT_SECRET = "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"
GOOGLE_REDIRECT_URI = "http://localhost:8000/auth/google/callback"  # Retour à l'ancienne URL
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
SCOPES = [
    "https://www.googleapis.com/auth/calendar.events",
    "https://www.googleapis.com/auth/calendar.readonly",
]


def save_tokens(db, hr_admin_id: int, token_data: dict):
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


def get_valid_access_token(db, hr_admin_id: int) -> Optional[str]:
    rec = db.query(HRGoogleToken).filter(HRGoogleToken.hr_admin_id == hr_admin_id).first()
    if not rec:
        return None
    if not rec.expires_at or rec.expires_at <= datetime.now(timezone.utc) + timedelta(seconds=60):
        if not rec.refresh_token:
            return None
        data = {
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "refresh_token": rec.refresh_token,
            "grant_type": "refresh_token",
        }
        r = requests.post(GOOGLE_TOKEN_URL, data=data, timeout=15)
        if r.status_code != 200:
            return None
        token_data = r.json()
        save_tokens(db, hr_admin_id, token_data)
        return token_data.get("access_token")
    return rec.access_token


@router.get("/api/hr/google/status")
def google_status(request: Request, db=Depends(get_db)):
    """
    Vérifie le statut de connexion Google Calendar pour l'utilisateur HR connecté.
    """
    try:
        user_id = get_user_id_from_request(request)
        
        if not user_id:
            return {"connected": False}
        
        token = get_valid_access_token(db, user_id)
        return {"connected": bool(token)}
        
    except Exception as e:
        print(f"❌ Google Status Error: {str(e)}")
        return {"connected": False}


@router.get("/api/hr/google/oauth/start")
def google_oauth_start(request: Request):
    """
    Démarre le processus OAuth Google pour HR.
    Récupère l'utilisateur connecté depuis les cookies JWT ou headers d'autorisation.
    """
    try:
        user_id = get_user_id_from_request(request)
        
        if not user_id:
            print("❌ Google OAuth Start: Aucun utilisateur connecté")
            return RedirectResponse("/enterprise-login?error=not_authenticated")
        
        from urllib.parse import urlencode
        params = {
            "client_id": GOOGLE_CLIENT_ID,
            "redirect_uri": GOOGLE_REDIRECT_URI,
            "response_type": "code",
            "scope": " ".join(SCOPES),
            "access_type": "offline",
            "prompt": "consent",
            "include_granted_scopes": "true",
            "state": str(user_id),  # Passer l'ID utilisateur dans le state
        }
        
        auth_url = f"{GOOGLE_AUTH_URL}?{urlencode(params)}"
        print(f"🔄 Google OAuth Start: Redirection vers Google pour user_id: {user_id}")
        return RedirectResponse(auth_url)
        
    except Exception as e:
        print(f"❌ Google OAuth Start Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return RedirectResponse("/enterprise-login?error=oauth_start_failed")


@router.get("/api/hr/google/callback")
def google_oauth_callback_hr(code: str, state: str = None, db=Depends(get_db)):
    """
    Callback Google OAuth pour HR.
    Le paramètre 'state' contient l'ID utilisateur.
    """
    try:
        print(f"🔄 Google OAuth Callback HR: Code reçu, State: {state}")
        
        # Vérifier si c'est un callback HR (state contient un ID utilisateur numérique)
        user_id = None
        if state and state.isdigit():
            user_id = int(state)
            print(f"✅ Google OAuth Callback HR: User ID extrait du state: {user_id}")
        else:
            print(f"❌ Google OAuth Callback HR: State invalide ou manquant: {state}")
            return RedirectResponse("/HR-dep/job-details.html?error=invalid_state")
        
        # Échanger le code contre un token d'accès
        data = {
            "code": code,
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "redirect_uri": GOOGLE_REDIRECT_URI,
            "grant_type": "authorization_code",
        }
        
        print(f"🔄 Google OAuth Callback HR: Échange du code contre token...")
        r = requests.post(GOOGLE_TOKEN_URL, data=data, timeout=15)
        
        if r.status_code != 200:
            print(f"❌ Google OAuth Callback HR: Échec échange code - Status: {r.status_code}")
            print(f"❌ Google OAuth Callback HR: Response: {r.text}")
            return RedirectResponse("/HR-dep/job-details.html?error=google_auth_failed")
        
        token_data = r.json()
        print(f"✅ Google OAuth Callback HR: Token reçu: {list(token_data.keys())}")
        
        # Sauvegarder les tokens
        save_tokens(db, user_id, token_data)
        print(f"✅ Google OAuth Callback HR: Tokens sauvegardés pour user_id: {user_id}")
        
        return RedirectResponse("/HR-dep/job-details.html?connected=google")
        
    except Exception as e:
        print(f"❌ Google OAuth Callback HR Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return RedirectResponse("/HR-dep/job-details.html?error=google_callback_error")


@router.get("/api/hr/google/calendar-list")
def list_calendars(request: Request, db=Depends(get_db)):
    """
    Liste les calendriers Google de l'utilisateur HR connecté.
    """
    try:
        user_id = get_user_id_from_request(request)
        
        if not user_id:
            raise HTTPException(status_code=401, detail="Utilisateur non connecté")
        
        token = get_valid_access_token(db, user_id)
        if not token:
            raise HTTPException(status_code=401, detail="Google non connecté")
        
        r = requests.get("https://www.googleapis.com/calendar/v3/users/me/calendarList", 
                        headers={"Authorization": f"Bearer {token}"}, timeout=15)
        if r.status_code != 200:
            raise HTTPException(status_code=400, detail="Impossible de lister les agendas")
        
        items = r.json().get("items", [])
        return {"success": True, "calendars": [{"id": it.get("id"), "summary": it.get("summary")} for it in items]}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Calendar List Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Erreur interne du serveur")


@router.get("/api/hr/google/busy")
def freebusy(calendarId: str, timeMin: str, timeMax: str, request: Request, db=Depends(get_db)):
    """
    Récupère les créneaux occupés depuis Google Calendar.
    """
    try:
        user_id = get_user_id_from_request(request)
        
        if not user_id:
            raise HTTPException(status_code=401, detail="Utilisateur non connecté")
        
        token = get_valid_access_token(db, user_id)
        if not token:
            raise HTTPException(status_code=401, detail="Google non connecté")
        
        url = "https://www.googleapis.com/calendar/v3/freeBusy"
        body = {
            "timeMin": timeMin,
            "timeMax": timeMax,
            "items": [{"id": calendarId}],
        }
        r = requests.post(url, headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"}, 
                        data=json.dumps(body), timeout=15)
        if r.status_code != 200:
            raise HTTPException(status_code=400, detail="Impossible de récupérer les busy times")
        
        resp = r.json()
        cal = resp.get("calendars", {}).get(calendarId, {})
        return {"success": True, "busy": cal.get("busy", [])}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Freebusy Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Erreur interne du serveur")


@router.post("/api/hr/google/events")
def create_event(calendarId: str, start: str, end: str, summary: str = "Entretien", description: str = "", location: str = "", request: Request = None, db=Depends(get_db)):
    """
    Crée un événement dans Google Calendar.
    """
    try:
        user_id = get_user_id_from_request(request)
        
        if not user_id:
            raise HTTPException(status_code=401, detail="Utilisateur non connecté")
        
        token = get_valid_access_token(db, user_id)
        if not token:
            raise HTTPException(status_code=401, detail="Google non connecté")
        
        url = f"https://www.googleapis.com/calendar/v3/calendars/{calendarId}/events"
        event = {
            "summary": summary,
            "description": description,
            "location": location,
            "start": {"dateTime": start},
            "end": {"dateTime": end},
        }
        r = requests.post(url, headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"}, 
                        data=json.dumps(event), timeout=15)
        if r.status_code not in (200, 201):
            raise HTTPException(status_code=400, detail="Création d'événement échouée")
        
        return {"success": True, "event": r.json()}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Create Event Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Erreur interne du serveur")



