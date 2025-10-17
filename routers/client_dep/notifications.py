from fastapi import APIRouter, Request, Depends, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse
from database import SessionLocal
from databaseclient.models import User, Application, Job, Company, ProfileCandidat, Notification
from databasehr.models import InterviewSlot, SlotStatus
from routers.client_dep.dependencies import get_db, get_current_user, require_auth
from sqlalchemy.orm import Session, joinedload
from fastapi.templating import Jinja2Templates
from typing import Dict, List
import json
import os
from datetime import datetime
from pydantic import BaseModel

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
    
    # Get notifications from the notifications table (safe)
    try:
        notifications = db.query(Notification).filter(
            Notification.user_id == current_user.id
        ).order_by(Notification.created_at.desc()).all()
    except Exception as e:
        print(f"Error loading notifications for user {current_user.id}: {e}")
        notifications = []
    
    # Convert to the format expected by the template
    notification_list = []
    for notif in notifications:
        safe_created_at_str = ""
        try:
            if getattr(notif, "created_at", None):
                safe_created_at_str = notif.created_at.strftime('%d/%m/%Y à %H:%M')
        except Exception:
            safe_created_at_str = ""
        notification_data = {
            'id': notif.id,
            'type': notif.type,
            'title': notif.title,
            'message': notif.message,
            'status': notif.status,
            'job_title': notif.job_title,
            'company_name': notif.company_name,
            'timestamp': notif.created_at,
            'created_at': notif.created_at,
            'created_at_str': safe_created_at_str,
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
    

@router.get("/api/notification/{application_id}")
async def get_application_notification(application_id: int, request: Request, db: Session = Depends(get_db)):
    """Get notification details for a specific application"""
    try:
        # Get the application
        application = db.query(Application).filter(Application.id == application_id).first()
        if not application:
            return {"notification": None}
        
        # Get the job details
        job = db.query(Job).options(
            joinedload(Job.company)
        ).filter(Job.id == application.job_id).first()
        
        if not job:
            return {"notification": None}
        
        # Create notification data
        notification_data = {
            "id": application.id,
            "job_title": job.title,
            "company_name": job.company.company_name if job.company else None,
            "status": application.status,
            "interview_date": application.interview_date.isoformat() if application.interview_date else None,
            "application_date": application.application_date.isoformat() if application.application_date else None
        }
        
        return {"notification": notification_data}
        
    except Exception as e:
        print(f"Error getting application notification: {str(e)}")
        return {"notification": None}

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


# ===== ROUTES POUR LA SÉLECTION DE CRÉNEAUX D'ENTRETIEN =====

class SlotSelectionRequest(BaseModel):
    slot_id: int
    application_id: int

@router.get("/interview-slots/{application_id}", response_class=HTMLResponse)
async def interview_slots_page(request: Request, application_id: int, db: Session = Depends(get_db)):
    """Page pour que le candidat choisisse un créneau d'entretien"""
    current_user = get_current_user(request, db)
    
    if not current_user:
        return templates.TemplateResponse("client-dep/auth/login.html", {
            "request": request,
            "error": "Vous devez être connecté pour accéder à cette page"
        })
    
    # Vérifier que l'application appartient au candidat
    application = db.query(Application).options(
        joinedload(Application.job).joinedload(Job.company),
        joinedload(Application.candidate_profile)
    ).filter(
        Application.id == application_id,
        Application.candidate_profile.has(ProfileCandidat.user_id == current_user.id)
    ).first()
    
    if not application:
        return templates.TemplateResponse("client-dep/404.html", {
            "request": request,
            "error": "Candidature non trouvée ou non autorisée"
        })
    
    # Récupérer les créneaux confirmés pour cette candidature
    available_slots = db.query(InterviewSlot).filter(
        InterviewSlot.application_id == application_id,
        InterviewSlot.is_confirmed == True,
        InterviewSlot.status == SlotStatus.FREE
    ).order_by(InterviewSlot.start_time.asc()).all()
    
    if not available_slots:
        return templates.TemplateResponse("client-dep/404.html", {
            "request": request,
            "error": "Aucun créneau d'entretien disponible pour cette candidature"
        })
    
    # Formater les créneaux pour l'affichage
    slots_data = []
    for slot in available_slots:
        slots_data.append({
            'id': slot.id,
            'start_time': slot.start_time,
            'end_time': slot.end_time,
            'start_time_str': slot.start_time.strftime('%d/%m/%Y à %H:%M'),
            'end_time_str': slot.end_time.strftime('%H:%M'),
            'date_str': slot.start_time.strftime('%d/%m/%Y'),
            'time_str': f"{slot.start_time.strftime('%H:%M')} - {slot.end_time.strftime('%H:%M')}"
        })
    
    return templates.TemplateResponse("client-dep/interview_slots.html", {
        "request": request,
        "application": application,
        "slots": slots_data,
        "current_user": current_user
    })

@router.post("/api/interview-slots/select")
async def select_interview_slot(
    request: Request,
    slot_data: SlotSelectionRequest,
    db: Session = Depends(get_db)
):
    """Sélectionner un créneau d'entretien et supprimer les autres"""
    current_user = get_current_user(request, db)
    
    if not current_user:
        return {"success": False, "message": "Authentication required"}
    
    try:
        # Vérifier que l'application appartient au candidat
        application = db.query(Application).options(
            joinedload(Application.candidate_profile)
        ).filter(
            Application.id == slot_data.application_id,
            Application.candidate_profile.has(ProfileCandidat.user_id == current_user.id)
        ).first()
        
        if not application:
            return {"success": False, "message": "Candidature non trouvée ou non autorisée"}
        
        # Récupérer le créneau sélectionné
        selected_slot = db.query(InterviewSlot).filter(
            InterviewSlot.id == slot_data.slot_id,
            InterviewSlot.application_id == slot_data.application_id,
            InterviewSlot.status == SlotStatus.FREE
        ).first()
        
        if not selected_slot:
            return {"success": False, "message": "Créneau non trouvé ou non disponible"}
        
        # Récupérer tous les autres créneaux pour cette candidature
        other_slots = db.query(InterviewSlot).filter(
            InterviewSlot.application_id == slot_data.application_id,
            InterviewSlot.id != slot_data.slot_id
        ).all()
        
        # Marquer le créneau sélectionné comme confirmé
        selected_slot.status = SlotStatus.CONFIRMED
        
        # Supprimer les autres créneaux
        for slot in other_slots:
            db.delete(slot)
        
        # Mettre à jour le statut de la candidature
        application.status = 'interview_scheduled'
        application.interview_date = selected_slot.start_time
        application.interview_time = selected_slot.start_time.strftime('%H:%M')
        application.interview_type = "Entretien confirmé"
        
        # Mettre à jour aussi la base de données HR
        try:
            from databasehr.database import SessionLocal as HRSessionLocal
            from databasehr.models import Application as HRApplication
            
            hr_db = HRSessionLocal()
            try:
                hr_application = hr_db.query(HRApplication).filter(HRApplication.id == application.id).first()
                if hr_application:
                    hr_application.interview_date = selected_slot.start_time
                    hr_application.interview_time = selected_slot.start_time.strftime('%H:%M')
                    hr_application.interview_type = "Entretien confirmé"
                    hr_application.status = 'interview_scheduled'
                    print(f"✅ HR UPDATE: Données d'entretien mises à jour pour l'application HR {hr_application.id}")
                    
                    # Créer un événement Google Calendar pour le HR agent
                    try:
                        from routers.hr.google_calendar import create_calendar_event
                        
                        # Récupérer les informations du candidat
                        candidate_name = f"{application.candidate_profile.user.first_name} {application.candidate_profile.user.last_name}"
                        candidate_email = application.candidate_profile.user.email
                        job_title = application.job.title
                        company_name = application.job.company.company_name
                        
                        # Récupérer l'ID du HR admin responsable (depuis le slot)
                        hr_admin_id = selected_slot.recruiter_id
                        
                        print(f"📅 Google Calendar: Création d'événement pour HR {hr_admin_id}")
                        calendar_result = create_calendar_event(
                            db=hr_db,
                            hr_admin_id=hr_admin_id,
                            candidate_name=candidate_name,
                            candidate_email=candidate_email,
                            job_title=job_title,
                            company_name=company_name,
                            interview_date=selected_slot.start_time,
                            interview_duration_minutes=60
                        )
                        
                        if calendar_result["success"]:
                            print(f"✅ Google Calendar: Événement créé avec succès - {calendar_result.get('event_id')}")
                            # Optionnel: sauvegarder l'ID de l'événement dans la base de données
                            hr_application.google_calendar_event_id = calendar_result.get('event_id')
                            hr_application.google_meet_link = calendar_result.get('meet_link')
                        else:
                            print(f"⚠️ Google Calendar: Échec création événement - {calendar_result.get('message')}")
                            
                    except Exception as calendar_error:
                        print(f"❌ Google Calendar: Erreur lors de la création d'événement: {str(calendar_error)}")
                        # Ne pas faire échouer le processus principal si Google Calendar échoue
                    
                hr_db.commit()
            finally:
                hr_db.close()
        except Exception as e:
            print(f"❌ HR UPDATE ERROR: {str(e)}")
        
        # Créer une notification de confirmation
        chosen_slot_str = selected_slot.start_time.strftime('%d/%m/%Y à %H:%M')
        notification = Notification(
            user_id=current_user.id,
            type='interview_scheduled',
            title='Créneau d\'entretien confirmé',
            message=f'Votre entretien pour le poste "{application.job.title}" chez {application.job.company.company_name} est confirmé pour le {chosen_slot_str}.',
            application_id=application.id,
            job_id=application.job_id,
            status='interview_scheduled',
            job_title=application.job.title,
            company_name=application.job.company.company_name,
            chosen_slot=chosen_slot_str,
            is_read=False
        )
        
        print(f"🔔 Creating notification with chosen_slot: {chosen_slot_str}")
        db.add(notification)
        db.commit()
        print(f"✅ Notification created successfully with ID: {notification.id}")
        
        # Envoyer une notification WebSocket
        try:
            websocket_notification = {
                'type': 'interview_scheduled',
                'title': 'Créneau d\'entretien confirmé',
                'message': f'Votre entretien pour le poste "{application.job.title}" chez {application.job.company.company_name} est confirmé pour le {selected_slot.start_time.strftime("%d/%m/%Y à %H:%M")}.',
                'status': 'interview_scheduled',
                'job_title': application.job.title,
                'company_name': application.job.company.company_name,
                'timestamp': notification.created_at.isoformat(),
                'job_id': application.job_id,
                'application_id': application.id,
                'notification_id': notification.id,
                'chosen_slot': selected_slot.start_time.strftime('%d/%m/%Y à %H:%M')
            }
            
            await manager.send_personal_message(websocket_notification, current_user.id)
        except Exception as e:
            print(f"Erreur lors de l'envoi WebSocket: {e}")
        
        return {
            "success": True,
            "message": "Créneau sélectionné avec succès",
            "selected_slot": {
                "id": selected_slot.id,
                "start_time": selected_slot.start_time.isoformat(),
                "end_time": selected_slot.end_time.isoformat(),
                "date_str": selected_slot.start_time.strftime('%d/%m/%Y'),
                "time_str": f"{selected_slot.start_time.strftime('%H:%M')} - {selected_slot.end_time.strftime('%H:%M')}"
            }
        }
        
    except Exception as e:
        db.rollback()
        print(f"Erreur lors de la sélection du créneau: {e}")
        return {"success": False, "message": f"Erreur interne: {str(e)}"}

@router.get("/api/interview-slots/{application_id}")
async def get_available_slots(
    application_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """Récupérer les créneaux disponibles pour une candidature"""
    current_user = get_current_user(request, db)
    
    if not current_user:
        return {"success": False, "message": "Authentication required"}
    
    # Vérifier que l'application appartient au candidat
    application = db.query(Application).options(
        joinedload(Application.candidate_profile)
    ).filter(
        Application.id == application_id,
        Application.candidate_profile.has(ProfileCandidat.user_id == current_user.id)
    ).first()
    
    if not application:
        return {"success": False, "message": "Candidature non trouvée ou non autorisée"}
    
    # Récupérer les créneaux disponibles
    available_slots = db.query(InterviewSlot).filter(
        InterviewSlot.application_id == application_id,
        InterviewSlot.is_confirmed == True,
        InterviewSlot.status == SlotStatus.FREE
    ).order_by(InterviewSlot.start_time.asc()).all()
    
    slots_data = []
    for slot in available_slots:
        slots_data.append({
            'id': slot.id,
            'start_time': slot.start_time.isoformat(),
            'end_time': slot.end_time.isoformat(),
            'start_time_str': slot.start_time.strftime('%d/%m/%Y à %H:%M'),
            'end_time_str': slot.end_time.strftime('%H:%M'),
            'date_str': slot.start_time.strftime('%d/%m/%Y'),
            'time_str': f"{slot.start_time.strftime('%H:%M')} - {slot.end_time.strftime('%H:%M')}"
        })
    
    return {
        "success": True,
        "slots": slots_data,
        "application": {
            "id": application.id,
            "job_title": application.job.title,
            "company_name": application.job.company.company_name
        }
    }



