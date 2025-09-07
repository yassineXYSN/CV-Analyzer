from fastapi import APIRouter, Request, Depends, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse,JSONResponse
from database import SessionLocal
from databaseclient.models import User, Application, Job, Company, ProfileCandidat, Notification
from routers.client_dep.dependencies import get_db, get_current_user, require_auth
from sqlalchemy.orm import Session, joinedload
from fastapi.templating import Jinja2Templates
from typing import Dict, List
import json
import os
from datetime import datetime
from pydantic import BaseModel

from databaseclient.models import Interview, InterviewStatus
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
        print(f"User {user_id} connected to notifications")

    def disconnect(self, user_id: int):
        if user_id in self.active_connections:
            del self.active_connections[user_id]
            print(f"User {user_id} disconnected from notifications")

    async def send_personal_message(self, message: dict, user_id: int):
        if user_id in self.active_connections:
            try:
                await self.active_connections[user_id].send_text(json.dumps(message))
                return True
            except Exception as e:
                print(f"Error sending message to user {user_id}: {e}")
                self.disconnect(user_id)
                return False
        else:
            print(f"No active WebSocket connection for user {user_id}")
            return False

    async def broadcast_to_users(self, message: dict, user_ids: List[int]):
        for user_id in user_ids:
            await self.send_personal_message(message, user_id)

manager = ConnectionManager()

@router.websocket("/ws/notifications/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int):
    await manager.connect(websocket, user_id)
    try:
        while True:
            # Keep connection alive
            data = await websocket.receive_text()
            # Echo back for heartbeat
            await websocket.send_text(json.dumps({"type": "heartbeat", "timestamp": datetime.now().isoformat()}))
    except WebSocketDisconnect:
        manager.disconnect(user_id)

@router.get("/notifications", response_class=HTMLResponse)
async def notifications_page(request: Request, db: Session = Depends(get_db)):
    current_user = get_current_user(request, db)
    
    if not current_user:
        return templates.TemplateResponse("client-dep/auth/login.html", {
            "request": request,
            "error": "Vous devez être connecté pour voir vos notifications"
        })
    
    # Get notifications from the notifications table
    notifications = db.query(Notification).filter(
        Notification.user_id == current_user.id
    ).order_by(Notification.created_at.desc()).all()
    
    # Convert to the format expected by the template
    notification_list = []
    for notif in notifications:
        notification_data = {
            'id': notif.id,
            'type': notif.type,
            'title': notif.title,
            'message': notif.message,
            'status': notif.status,
            'job_title': notif.job_title,
            'company_name': notif.company_name,
            'timestamp': notif.created_at,
            'is_read': notif.is_read,
            'job_id': notif.job_id,
            'application_id': notif.application_id
        }
        notification_list.append(notification_data)
    
    return templates.TemplateResponse("client-dep/notifications.html", {
        "request": request,
        "notifications": notification_list,
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
        return {"success": False, "message": "Authentication required"}
    
    # Find the notification and verify it belongs to the current user
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == current_user.id
    ).first()
    
    if not notification:
        return {"success": False, "message": "Notification not found"}
    
    # Mark as read
    notification.is_read = True
    db.commit()
    
    return {"success": True, "message": "Notification marked as read"}

@router.post("/api/notifications/mark-all-read")
async def mark_all_notifications_read(
    request: Request,
    db: Session = Depends(get_db)
):
    current_user = get_current_user(request, db)
    if not current_user:
        return {"success": False, "message": "Authentication required"}
    
    # Mark all notifications as read for the current user
    db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.is_read == False
    ).update({"is_read": True})
    
    db.commit()
    
    return {"success": True, "message": "All notifications marked as read"}

# Function to create and send notification when application status changes
async def send_application_status_notification(
    db: Session,
    application_id: int,
    new_status: str,
    admin_name: str = None
):
    """Send real-time notification and store in database when application status changes"""
    try:
        # Get application with related data
        application = db.query(Application).options(
            joinedload(Application.job).joinedload(Job.company),
            joinedload(Application.candidate_profile)
        ).filter(Application.id == application_id).first()
        
        if not application or not application.candidate_profile:
            return False
        
        # Get user ID from candidate profile
        user_id = application.candidate_profile.user_id
        if not user_id:
            return False
        
        # Create notification message
        status_messages = {
            'pending': 'est en cours d\'examen',
            'reviewed': 'a été examinée',
            'interview_scheduled': 'a été sélectionnée pour un entretien',
            'interview_completed': 'entretien terminé',
            'accepted': 'a été acceptée ! Félicitations !',
            'rejected': 'n\'a pas été retenue cette fois',
            'withdrawn': 'a été retirée'
        }
        
        status_message = status_messages.get(new_status, f'a été mise à jour vers "{new_status}"')
        
        title = 'Mise à jour de candidature'
        message = f'Votre candidature pour le poste "{application.job.title}" chez {application.job.company.company_name} {status_message}'
        
        # Create notification in database
        notification = Notification(
            user_id=user_id,
            type='application_status_change',
            title=title,
            message=message,
            application_id=application.id,
            job_id=application.job_id,
            status=new_status,
            job_title=application.job.title,
            company_name=application.job.company.company_name,
            admin_name=admin_name,
            is_read=False
        )
        
        db.add(notification)
        db.commit()
        db.refresh(notification)
        
        # Send WebSocket notification
        websocket_notification = {
            'type': 'application_status_change',
            'title': title,
            'message': message,
            'status': new_status,
            'job_title': application.job.title,
            'company_name': application.job.company.company_name,
            'timestamp': notification.created_at.isoformat(),
            'job_id': application.job_id,
            'application_id': application.id,
            'notification_id': notification.id,
            'admin_name': admin_name
        }
        
        # Send WebSocket notification
        success = await manager.send_personal_message(websocket_notification, user_id)
        
        if success:
            print(f"Notification sent to user {user_id} for application {application_id}")
        else:
            print(f"Failed to send WebSocket notification to user {user_id} - user not connected")
        
        return True
        
    except Exception as e:
        print(f"Error sending notification: {e}")
        db.rollback()
        return False

# ----- n8n/test: create and broadcast a notification -----
class NotificationCreatePayload(BaseModel):
    user_id: int
    type: str = "application_status_change"
    title: str
    message: str
    application_id: int | None = None
    job_id: int | None = None
    status: str | None = None
    company_name: str | None = None
    job_title: str | None = None
    admin_name: str | None = None


@router.post("/api/notifications/test-create")
async def test_create_notification(payload: NotificationCreatePayload, db: Session = Depends(get_db)):
    """Utility endpoint to create a notification (for n8n testing) and broadcast via WebSocket if user connected."""
    try:
        print("Creating test notification...")
        notification = Notification(
            user_id=payload.user_id,
            type=payload.type,
            title=payload.title,
            message=payload.message,
            application_id=payload.application_id,
            job_id=payload.job_id,
            status=payload.status,
            company_name=payload.company_name,
            job_title=payload.job_title,
            admin_name=payload.admin_name,
            is_read=False,
        )
        db.add(notification)
        print("Test notification created:", notification.id)
        db.commit()
        print("Test notification committed")
        db.refresh(notification)
        print("Test notification refreshed:", notification.id)

        message = {
            "type": notification.type,
            "title": notification.title,
            "message": notification.message,
            "status": notification.status,
            "job_title": notification.job_title,
            "company_name": notification.company_name,
            "timestamp": notification.created_at.isoformat(),
            "job_id": notification.job_id,
            "application_id": notification.application_id,
            "notification_id": notification.id,
            "admin_name": notification.admin_name,
        }
        print("Sending WebSocket notification to user:", notification.user_id)

        await manager.send_personal_message(message, notification.user_id)
        print("WebSocket notification sent successfully")
        return {"success": True, "notification_id": notification.id}
    except Exception as e:
        db.rollback()
        print(f"Error creating test notification: {e}")
        return {"success": False, "error": str(e)}
    

@router.get("/api/notifications/count")
async def get_notification_count(
    request: Request,
    db: Session = Depends(get_db)
):
    current_user = get_current_user(request, db)
    if not current_user:
        return {"success": False, "message": "Authentication required"}
    
    # Count unread notifications for the current user
    unread_count = db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.is_read == False
    ).count()
    
    return {
        "success": True,
        "unread_count": unread_count
    }

@router.get("/api/notifications/recent")
async def get_recent_notifications(
    request: Request,
    limit: int = 3,
    db: Session = Depends(get_db)
):
    current_user = get_current_user(request, db)
    if not current_user:
        return {"success": False, "message": "Authentication required"}
    
    # Get recent notifications for the current user
    notifications = db.query(Notification).filter(
        Notification.user_id == current_user.id
    ).order_by(Notification.created_at.desc()).limit(limit).all()
    
    # Convert to the format expected by the frontend
    notification_list = []
    for notif in notifications:
        notification_data = {
            'id': notif.id,
            'type': notif.type,
            'title': notif.title,
            'message': notif.message,
            'status': notif.status,
            'job_title': notif.job_title,
            'company_name': notif.company_name,
            'created_at': notif.created_at.isoformat(),
            'is_read': notif.is_read,
            'job_id': notif.job_id,
            'application_id': notif.application_id
        }
        notification_list.append(notification_data)
    
    return {
        "success": True,
        "notifications": notification_list
    }

# Quick ping endpoint to test WS without DB writes
@router.post("/api/notifications/ping/{user_id}")
async def ping_user_notification(user_id: int):
    message = {
        'type': 'test_ping',
        'title': 'Ping',
        'message': 'WebSocket ping notification',
        'status': 'pending',
        'job_title': 'N/A',
        'company_name': 'N/A',
        'timestamp': datetime.now().isoformat(),
        'job_id': None,
        'application_id': None,
        'notification_id': None,
        'admin_name': None,
    }
    success = await manager.send_personal_message(message, user_id)
    return {"success": success}
# -------------------------------
# Respond to interview invitation
# -------------------------------
@router.post("/api/respond-interview/{application_id}")
async def respond_interview(
    application_id: int,
    payload: dict,
    db: Session = Depends(get_db),
    request: Request = None
):
    current_user = get_current_user(request, db)
    if not current_user:
        return JSONResponse(
            status_code=401,
            content={"success": False, "message": "Utilisateur non connecté"}
        )

    response = payload.get("response")  # "accepted" ou "rejected"
    chosen_slot = payload.get("chosen_slot")

    # Récupérer la notification
    notification = db.query(Notification).filter(
        Notification.application_id == application_id,
        Notification.user_id == current_user.id,
        Notification.type == "interview_scheduled"
    ).first()

    if not notification:
        return JSONResponse(
            status_code=404,
            content={"success": False, "message": "Notification introuvable"}
        )

    # Mettre à jour la notification
    notification.response_status = 1 if response == "accepted" else 0
    if chosen_slot:
        notification.chosen_slot = chosen_slot

    # Si accepté → mise à jour de l'application + création de l'interview
    if response == "accepted" and chosen_slot:
        application = db.query(Application).filter(
            Application.id == application_id
        ).first()

        if application:
            application.interview_date = chosen_slot

            # Vérifier si une interview existe déjà
            existing_interview = db.query(Interview).filter(
                Interview.application_id == application.id,
                Interview.candidate_id == current_user.id
            ).first()

            if not existing_interview:
                new_interview = Interview(
                    candidate_id=current_user.id,
                    application_id=application.id,
                    status=InterviewStatus.PENDING,  # ✅ utiliser l'enum
                    start_session=False,
                    end_session=False,
                    scheduled_at=chosen_slot
                )
                db.add(new_interview)

    db.commit()

    redirect_url = f"/interview/{application_id}"
    return JSONResponse({
        "success": True,
        "message": "Réponse enregistrée",
        "redirect": redirect_url
    })
# -------------------------------
# Get specific notification
# -------------------------------
@router.get("/api/notification/{application_id}")
async def get_notifications(application_id: int, db: Session = Depends(get_db), request: Request = None):
    current_user = get_current_user(request, db)
    if not current_user:
        return JSONResponse(status_code=401, content={"success": False, "message": "Utilisateur non connecté"})

    # Récupérer toutes les notifications interview_scheduled de cette application pour l'utilisateur
    notifications = db.query(Notification).filter(
        Notification.application_id == application_id,
        Notification.user_id == current_user.id,
        Notification.type == "interview_scheduled"
    ).all()

    if not notifications:
        return JSONResponse(status_code=404, content={"success": False, "message": "Aucune notification trouvée pour cette application"})

    # Récupérer l'application
    application = db.query(Application).filter(Application.id == application_id).first()
    job_title = application.job.title if application and application.job else "Non spécifié"
    company_name = application.job.company.company_name if application and application.job and application.job.company else "Non spécifié"

    notifications_data = []
    for notif in notifications:
        notifications_data.append({
            "id": notif.id,
            "application_id": application_id,
            "title": notif.title,
            "message": notif.message,
            "chosen_slot": getattr(notif, "chosen_slot", None) or "",
            "scheduled_slot": notif.scheduled_slots,  # un créneau par notification
            "job_title": job_title,
            "company_name": company_name,
            "admin_name": getattr(notif, "admin_name", "Non spécifié"),
            "response_status": getattr(notif, "response_status", None) or "",
            "interview_date": application.interview_date.isoformat() if application and application.interview_date else None
        })

    return JSONResponse(status_code=200, content={"success": True, "notifications": notifications_data})


@router.get("/{application_id}/slots")
def get_interview_slots(application_id: int, db: Session = Depends(get_db)):
    application = db.query(Application).filter(Application.id == application_id).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    if not application.interview_slot:
        return {"slots": []}

    # ✅ Ensure proper splitting and trimming
    slots = [s.strip() for s in application.interview_slot.split(",") if s.strip()]
    return {"slots": slots}

@router.get("/api/applications/user/{user_id}")
async def get_user_applications(user_id: int, db: Session = Depends(get_db)):
    applications = db.query(Application).filter(Application.user_id == user_id).all()
    result = []
    for app in applications:
        result.append({
            "id": app.id,
            "job_id": app.job_id,
            "interview_date": app.interview_date.isoformat() if app.interview_date else None
        })
    return {"success": True, "applications": result}
