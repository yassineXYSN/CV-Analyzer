from fastapi import APIRouter, Request, Depends, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import HTMLResponse
from database import SessionLocal
from databaseclient.models import User, Application, Job, Company, ProfileCandidat
from routers.client_dep.dependencies import get_db, get_current_user, require_auth
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, and_
from fastapi.templating import Jinja2Templates
from typing import Dict, List
import json
import os
from datetime import datetime

router = APIRouter()

# Templates
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
templates_dir = os.path.join(BASE_DIR, "templates")
templates = Jinja2Templates(directory=templates_dir)

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, WebSocket] = {}

    async def connect(self, websocket: WebSocket, user_id: int):
        await websocket.accept()
        self.active_connections[user_id] = websocket
        print(f"WebSocket connected for user {user_id}")

    def disconnect(self, user_id: int):
        if user_id in self.active_connections:
            del self.active_connections[user_id]
            print(f"WebSocket disconnected for user {user_id}")

    async def send_personal_message(self, message: dict, user_id: int):
        if user_id in self.active_connections:
            try:
                await self.active_connections[user_id].send_text(json.dumps(message))
                print(f"Sent notification to user {user_id}: {message}")
                return True
            except Exception as e:
                print(f"Error sending message to user {user_id}: {e}")
                self.disconnect(user_id)
                return False
        return False

manager = ConnectionManager()

@router.websocket("/ws/notifications/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int):
    await manager.connect(websocket, user_id)
    try:
        while True:
            # Keep connection alive
            data = await websocket.receive_text()
            # Echo back for heartbeat
            await websocket.send_text(f"Heartbeat: {data}")
    except WebSocketDisconnect:
        manager.disconnect(user_id)
    except Exception as e:
        print(f"WebSocket error for user {user_id}: {e}")
        manager.disconnect(user_id)

@router.get("/notifications", response_class=HTMLResponse)
async def notifications_page(request: Request, db: Session = Depends(get_db)):
    current_user = get_current_user(request, db)
    
    # Require authentication
    if not current_user:
        return templates.TemplateResponse("client-dep/auth/login.html", {
            "request": request,
            "error": "Vous devez être connecté pour voir vos notifications"
        })
    
    # Get user's candidate profile
    candidate_profile = db.query(ProfileCandidat).filter(
        ProfileCandidat.user_id == current_user.id
    ).first()
    
    notifications = []
    if candidate_profile:
        # Get all applications for this user with job and company details
        applications = db.query(Application).options(
            joinedload(Application.job).joinedload(Job.company)
        ).filter(
            Application.candidate_profile_id == candidate_profile.id
        ).order_by(Application.updated_at.desc()).limit(50).all()
        
        # Convert applications to notification format
        for app in applications:
            if app.job and app.job.company:
                # Create notification-like object
                notification = type('Notification', (), {
                    'id': app.id,
                    'title': f"Mise à jour de candidature - {app.job.title}",
                    'message': f"Le statut de votre candidature pour le poste '{app.job.title}' chez {app.job.company.company_name} a été mis à jour vers '{app.status}'.",
                    'status': app.status,
                    'company_name': app.job.company.company_name,
                    'job_id': app.job.id,
                    'timestamp': app.updated_at or app.created_at
                })()
                notifications.append(notification)
    
    return templates.TemplateResponse("client-dep/notifications.html", {
        "request": request,
        "notifications": notifications,
        "current_user": current_user
    })

@router.post("/api/notifications/{notification_id}/mark-read")
async def mark_notification_read(
    notification_id: int, 
    request: Request, 
    db: Session = Depends(get_db)
):
    current_user = get_current_user(request, db)
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # For now, just return success since we don't have a separate notifications table
    # In a real implementation, you'd update a notifications table
    return {"success": True, "message": "Notification marked as read"}

@router.post("/api/notifications/mark-all-read")
async def mark_all_notifications_read(
    request: Request, 
    db: Session = Depends(get_db)
):
    current_user = get_current_user(request, db)
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # For now, just return success since we don't have a separate notifications table
    # In a real implementation, you'd update all notifications for the user
    return {"success": True, "message": "All notifications marked as read"}

# Function to send real-time notifications
async def send_application_status_notification(
    user_id: int, 
    application_id: int, 
    job_title: str, 
    company_name: str, 
    new_status: str,
    job_id: int
):
    """Send real-time notification when application status changes"""
    
    # Create status-specific messages
    status_messages = {
        'pending': f"Votre candidature pour '{job_title}' est en cours d'examen.",
        'reviewed': f"Votre candidature pour '{job_title}' a été examinée par l'équipe RH.",
        'interview_scheduled': f"Félicitations ! Un entretien a été programmé pour le poste '{job_title}'.",
        'interview_completed': f"Votre entretien pour '{job_title}' a été complété.",
        'accepted': f"🎉 Excellente nouvelle ! Votre candidature pour '{job_title}' a été acceptée !",
        'rejected': f"Votre candidature pour '{job_title}' n'a pas été retenue cette fois.",
        'withdrawn': f"Votre candidature pour '{job_title}' a été retirée."
    }
    
    message = status_messages.get(new_status, f"Le statut de votre candidature pour '{job_title}' a été mis à jour.")
    
    notification_data = {
        'type': 'application_status_change',
        'application_id': application_id,
        'job_id': job_id,
        'job_title': job_title,
        'company_name': company_name,
        'status': new_status,
        'title': f"Mise à jour de candidature - {job_title}",
        'message': message,
        'timestamp': datetime.now().isoformat()
    }
    
    # Send via WebSocket
    success = await manager.send_personal_message(notification_data, user_id)
    
    if success:
        print(f"Real-time notification sent to user {user_id} for application {application_id}")
    else:
        print(f"Failed to send real-time notification to user {user_id} - user may be offline")
    
    return success
