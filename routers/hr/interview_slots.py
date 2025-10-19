from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, validator
from typing import List, Optional
from datetime import datetime, timedelta
import sys
import os
import requests
import json
from sqlalchemy.orm import Session

from databasehr.database import SessionLocal
from databasehr.models import InterviewSlot, SlotStatus, Job, Application, HRAdmin, Company
from .email_service import EmailService

# Add the parent directory to the path to import utils1
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from utils1.interview_notifications import InterviewNotificationService, InterviewNotificationScheduler

router = APIRouter(prefix="/api/hr", tags=["interview-slots"])
templates = Jinja2Templates(directory="templates")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class SlotCreateRequest(BaseModel):
    job_id: int
    application_id: Optional[int] = None
    slots: List[dict]

    @validator("slots")
    def validate_slots(cls, value):
        if not value:
            raise ValueError("At least one slot is required")
        if len(value) > 4:
            raise ValueError("Maximum 4 slots can be created at once")
        for s in value:
            if "start_time" not in s or "end_time" not in s:
                raise ValueError("Each slot must have start_time and end_time")
        return value


class SlotUpdateStatusRequest(BaseModel):
    status: SlotStatus
    application_id: Optional[int] = None


class CandidateSlotChoiceRequest(BaseModel):
    slot_id: int
    application_id: int

class CreateMeetRequest(BaseModel):
    application_id: int
    admin_id: int
    candidate_name: str
    job_title: str
    company_name: str
    interview_date: str


@router.get("/interview-slots", response_model=List[dict])
def list_interview_slots(
    job_id: Optional[int] = Query(None),
    recruiter_id: Optional[int] = Query(None),
    db=Depends(get_db)
):
    query = db.query(InterviewSlot)
    if job_id:
        query = query.filter(InterviewSlot.job_id == job_id)
    if recruiter_id:
        query = query.filter(InterviewSlot.recruiter_id == recruiter_id)
    slots = query.order_by(InterviewSlot.start_time.asc()).all()
    return [
        {
            "id": s.id,
            "job_id": s.job_id,
            "recruiter_id": s.recruiter_id,
            "application_id": s.application_id,
            "start_time": s.start_time.isoformat(),
            "end_time": s.end_time.isoformat(),
            "status": s.status.value,
            "is_confirmed": s.is_confirmed,
            "confirmed_at": s.confirmed_at.isoformat() if s.confirmed_at else None,
            "confirmed_by": s.confirmed_by,
        }
        for s in slots
    ]


@router.post("/interview-slots")
def create_interview_slots(payload: SlotCreateRequest, db=Depends(get_db)):
    # Récupérer le premier admin HR disponible
    hr_admin = db.query(HRAdmin).first()
    if not hr_admin:
        raise HTTPException(status_code=400, detail="Aucun administrateur HR trouvé")
    user_id = hr_admin.id

    job = db.query(Job).filter(Job.id == payload.job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job introuvable")

    created: List[InterviewSlot] = []
    # Validate no conflicts per recruiter and enforce max 3 across both pending and existing for the day
    for s in payload.slots:
        start = datetime.fromisoformat(s["start_time"]) if isinstance(s["start_time"], str) else s["start_time"]
        end = datetime.fromisoformat(s["end_time"]) if isinstance(s["end_time"], str) else s["end_time"]
        if end <= start:
            raise HTTPException(status_code=400, detail="end_time doit être après start_time")

        # Enforce max 4 slots per request already checked, but also ensure no more than 4 per day existing
        start_day = start.date()
        same_day_count = db.query(InterviewSlot).filter(
            InterviewSlot.recruiter_id == user_id,
            InterviewSlot.start_time >= datetime.combine(start_day, datetime.min.time()),
            InterviewSlot.start_time < datetime.combine(start_day + timedelta(days=1), datetime.min.time()),
        ).count()
        # pending in this payload for same day
        pending_same_day = sum(1 for c in created if c.start_time.date() == start_day)
        if same_day_count + pending_same_day >= 4:
            raise HTTPException(status_code=400, detail="Maximum 4 créneaux par jour autorisés")

        overlap = db.query(InterviewSlot).filter(
            InterviewSlot.recruiter_id == user_id,
            InterviewSlot.start_time < end,
            InterviewSlot.end_time > start,
        ).first()
        if overlap:
            raise HTTPException(status_code=400, detail="Conflit avec un créneau existant")

        created.append(
            InterviewSlot(
                recruiter_id=user_id,
                job_id=payload.job_id,
                application_id=payload.application_id,
                start_time=start,
                end_time=end,
                status=SlotStatus.FREE,
            )
        )

    for slot in created:
        db.add(slot)
    db.commit()
    
    
    return {"success": True, "created": [c.id for c in created]}


@router.patch("/api/hr/interview-slots/{slot_id}")
def update_slot_status(slot_id: int, payload: SlotUpdateStatusRequest, db=Depends(get_db)):
    # Récupérer le premier admin HR disponible
    hr_admin = db.query(HRAdmin).first()
    if not hr_admin:
        raise HTTPException(status_code=400, detail="Aucun administrateur HR trouvé")
    user_id = hr_admin.id

    slot = db.query(InterviewSlot).filter(InterviewSlot.id == slot_id).first()
    if not slot:
        raise HTTPException(status_code=404, detail="Créneau introuvable")
    if slot.recruiter_id != user_id:
        raise HTTPException(status_code=403, detail="Non autorisé à modifier ce créneau")

    # Vérifier si le créneau est confirmé - bloquer les modifications
    if slot.is_confirmed:
        raise HTTPException(status_code=400, detail="Ce créneau est confirmé et ne peut plus être modifié")

    if payload.status in [SlotStatus.RESERVED, SlotStatus.CONFIRMED]:
        if not payload.application_id:
            raise HTTPException(status_code=400, detail="application_id requis pour réserver/confirmer")
        app = db.query(Application).filter(Application.id == payload.application_id).first()
        if not app:
            raise HTTPException(status_code=404, detail="Candidature introuvable")
        slot.application_id = app.id

    slot.status = payload.status
    db.commit()
    return {"success": True}


@router.delete("/interview-slots/{slot_id}")
def delete_slot(slot_id: int, db=Depends(get_db)):
    # Récupérer le premier admin HR disponible
    hr_admin = db.query(HRAdmin).first()
    if not hr_admin:
        raise HTTPException(status_code=400, detail="Aucun administrateur HR trouvé")
    user_id = hr_admin.id
    slot = db.query(InterviewSlot).filter(InterviewSlot.id == slot_id).first()
    if not slot:
        raise HTTPException(status_code=404, detail="Créneau introuvable")
    if slot.recruiter_id != user_id:
        raise HTTPException(status_code=403, detail="Non autorisé à supprimer ce créneau")
    
    # Vérifier si le créneau est confirmé - bloquer la suppression
    if slot.is_confirmed:
        raise HTTPException(status_code=400, detail="Ce créneau est confirmé et ne peut plus être supprimé")
    
    db.delete(slot)
    db.commit()
    return {"success": True}


@router.get("/interview-slots/conflicts")
def check_conflicts(start_time: str, end_time: str, db=Depends(get_db)):
    # Récupérer le premier admin HR disponible
    hr_admin = db.query(HRAdmin).first()
    if not hr_admin:
        raise HTTPException(status_code=400, detail="Aucun administrateur HR trouvé")
    user_id = hr_admin.id
    start = datetime.fromisoformat(start_time)
    end = datetime.fromisoformat(end_time)
    overlap = db.query(InterviewSlot).filter(
        InterviewSlot.recruiter_id == user_id,
        InterviewSlot.start_time < end,
        InterviewSlot.end_time > start,
    ).count()
    return {"has_conflict": overlap > 0}


class ConfirmSlotsRequest(BaseModel):
    job_id: int
    application_id: Optional[int] = None
    slot_ids: List[int]


@router.post("/interview-slots/confirm")
async def confirm_interview_slots(payload: ConfirmSlotsRequest, db=Depends(get_db)):
    print("🚨 ENDPOINT CONFIRM APPELÉ ! 🚨")
    print(f"🔍 DEBUG: confirm_interview_slots appelé avec payload: {payload}")
    # Récupérer le premier admin HR disponible
    hr_admin = db.query(HRAdmin).first()
    if not hr_admin:
        raise HTTPException(status_code=400, detail="Aucun administrateur HR trouvé")
    user_id = hr_admin.id

    # Vérifier que tous les créneaux appartiennent au même job et au même recruteur
    slots = db.query(InterviewSlot).filter(
        InterviewSlot.id.in_(payload.slot_ids),
        InterviewSlot.job_id == payload.job_id,
        InterviewSlot.recruiter_id == user_id
    ).all()

    if len(slots) != len(payload.slot_ids):
        raise HTTPException(status_code=400, detail="Certains créneaux sont introuvables ou n'appartiennent pas à ce job")

    # Vérifier qu'aucun créneau n'est déjà confirmé
    already_confirmed = [s.id for s in slots if s.is_confirmed]
    if already_confirmed:
        raise HTTPException(status_code=400, detail=f"Les créneaux {already_confirmed} sont déjà confirmés")

    # Confirmer tous les créneaux
    now = datetime.now()
    for slot in slots:
        slot.is_confirmed = True
        slot.confirmed_at = now
        slot.confirmed_by = user_id
        if payload.application_id:
            slot.application_id = payload.application_id

    # Ne pas remplir les champs d'entretien ici - ils seront remplis quand le candidat confirme son choix

    db.commit()
    
    # Envoyer automatiquement l'email d'invitation si une candidature est associée
    print(f"🔍 DEBUG: application_id = {payload.application_id}")
    if payload.application_id:
        print(f"📧 Tentative d'envoi d'email pour application_id: {payload.application_id}")
        try:
            # Récupérer les informations de la candidature
            application = db.query(Application).filter(Application.id == payload.application_id).first()
            print(f"🔍 DEBUG: Application trouvée: {application is not None}")
            if application:
                # Accéder aux données du candidat via les relations
                candidate_name = application.candidate_profile.name if application.candidate_profile else "Candidat"
                candidate_email = application.candidate_profile.contact.email if application.candidate_profile and application.candidate_profile.contact else "email@example.com"
                print(f"📧 Candidat: {candidate_name} ({candidate_email})")
                # Récupérer les informations du job
                job = db.query(Job).filter(Job.id == payload.job_id).first()
                print(f"🔍 DEBUG: Job trouvé: {job is not None}")
                if job:
                    # Récupérer l'entreprise via une requête séparée
                    company = db.query(Company).filter(Company.id == job.company_id).first()
                    company_name = company.company_name if company else "Entreprise"
                    print(f"📧 Job: {job.title} chez {company_name}")
                    # Préparer les créneaux confirmés pour l'email
                    interview_slots = []
                    for slot in slots:
                        interview_slots.append({
                            'start_time': slot.start_time,
                            'end_time': slot.end_time
                        })
                    
                    # Envoyer l'email d'invitation
                    print(f"📧 Appel de l'email service...")
                    email_service = EmailService()
                    email_sent = email_service.send_interview_invitation_email(
                        candidate_email=candidate_email,
                        candidate_name=candidate_name,
                        job_title=job.title,
                        company_name=company_name,
                        interview_slots=interview_slots
                    )
                    print(f"📧 Résultat de l'envoi d'email: {email_sent}")
                    
                    if email_sent:
                        print(f"✅ Email d'invitation automatique envoyé à {candidate_email}")
                    else:
                        print(f"❌ Échec de l'envoi automatique de l'email à {candidate_email}")
                    
                    # Créer une notification pour le candidat
                    try:
                        from databaseclient.models import Notification
                        # Récupérer l'user_id du candidat via le profile
                        candidate_user_id = application.candidate_profile.user_id if application.candidate_profile else None
                        if candidate_user_id:
                            # Préparer les créneaux pour la notification
                            slots_text = []
                            for slot in slots:
                                start_str = slot.start_time.strftime('%d/%m/%Y à %H:%M')
                                end_str = slot.end_time.strftime('%H:%M')
                                slots_text.append(f"{start_str} - {end_str}")
                            
                            # Créer la notification
                            notification = Notification(
                                user_id=candidate_user_id,
                                type='interview_scheduled',
                                title='Entretien programmé',
                                message=f'Vos créneaux d\'entretien pour le poste "{job.title}" chez {company_name} ont été confirmés. Veuillez choisir votre créneau préféré.',
                                application_id=payload.application_id,
                                job_id=payload.job_id,
                                company_name=company_name,
                                job_title=job.title,
                                scheduled_slots='; '.join(slots_text),
                                is_read=False
                            )
                            db.add(notification)
                            db.commit()
                            db.refresh(notification)
                            print(f"✅ Notification créée pour le candidat (user_id: {candidate_user_id})")
                            
                            # Envoyer la notification via WebSocket
                            try:
                                from routers.client_dep.notifications import manager
                                websocket_notification = {
                                    'type': 'interview_scheduled',
                                    'title': 'Entretien programmé',
                                    'message': f'Vos créneaux d\'entretien pour le poste "{job.title}" chez {company_name} ont été confirmés. Veuillez choisir votre créneau préféré.',
                                    'status': 'interview_scheduled',
                                    'job_title': job.title,
                                    'company_name': company_name,
                                    'timestamp': notification.created_at.isoformat(),
                                    'job_id': payload.job_id,
                                    'application_id': payload.application_id,
                                    'notification_id': notification.id,
                                    'scheduled_slots': '; '.join(slots_text)
                                }
                                
                                success = await manager.send_personal_message(websocket_notification, candidate_user_id)
                                if success:
                                    print(f"✅ Notification WebSocket envoyée au candidat (user_id: {candidate_user_id})")
                                else:
                                    print(f"⚠️ Candidat non connecté au WebSocket (user_id: {candidate_user_id})")
                            except Exception as e:
                                print(f"❌ Erreur lors de l'envoi WebSocket: {e}")
                        else:
                            print(f"⚠️ Impossible de trouver l'user_id du candidat")
                    except Exception as e:
                        print(f"❌ Erreur lors de la création de la notification: {e}")
                        # Ne pas faire échouer la confirmation à cause de la notification
        except Exception as e:
            print(f"❌ Erreur lors de l'envoi automatique de l'email: {e}")
            # Ne pas faire échouer la confirmation à cause de l'email
    
    return {"success": True, "confirmed_slots": [s.id for s in slots], "confirmed_at": now.isoformat()}


@router.get("/interview-slots/job-confirmed/{job_id}")
def check_job_slots_confirmed(job_id: int, db=Depends(get_db)):
    """
    Vérifie si un job a des créneaux confirmés (calendrier verrouillé)
    """
    # Récupérer le premier admin HR disponible
    hr_admin = db.query(HRAdmin).first()
    if not hr_admin:
        raise HTTPException(status_code=400, detail="Aucun administrateur HR trouvé")
    user_id = hr_admin.id

    # Vérifier s'il y a des créneaux confirmés pour ce job
    confirmed_slots = db.query(InterviewSlot).filter(
        InterviewSlot.job_id == job_id,
        InterviewSlot.recruiter_id == user_id,
        InterviewSlot.is_confirmed == True
    ).all()

    return {
        "has_confirmed_slots": len(confirmed_slots) > 0,
        "confirmed_count": len(confirmed_slots),
        "confirmed_slots": [
            {
                "id": slot.id,
                "start_time": slot.start_time.isoformat(),
                "end_time": slot.end_time.isoformat(),
                "confirmed_at": slot.confirmed_at.isoformat() if slot.confirmed_at else None
            }
            for slot in confirmed_slots
        ]
    }


class SendInvitationRequest(BaseModel):
    application_id: int
    job_id: int


@router.post("/send-invitation")
async def send_interview_invitation(
    request: SendInvitationRequest,
    db: SessionLocal = Depends(get_db)
):
    """Envoyer un email d'invitation au candidat avec les créneaux disponibles"""
    try:
        # Récupérer les informations de la candidature
        application = db.query(Application).filter(Application.id == request.application_id).first()
        if not application:
            raise HTTPException(status_code=404, detail="Candidature non trouvée")
        
        # Récupérer les informations du job
        job = db.query(Job).filter(Job.id == request.job_id).first()
        if not job:
            raise HTTPException(status_code=404, detail="Offre d'emploi non trouvée")
        
        # Récupérer les créneaux confirmés pour cette candidature
        confirmed_slots = db.query(InterviewSlot).filter(
            InterviewSlot.application_id == request.application_id,
            InterviewSlot.status == SlotStatus.CONFIRMED
        ).all()
        
        if not confirmed_slots:
            raise HTTPException(status_code=400, detail="Aucun créneau confirmé trouvé pour cette candidature")
        
        # Préparer les données pour l'email
        interview_slots = []
        for slot in confirmed_slots:
            interview_slots.append({
                'start_time': slot.start_time,
                'end_time': slot.end_time
            })
        
        # Envoyer l'email
        email_service = EmailService()
        success = email_service.send_interview_invitation_email(
            candidate_email=application.candidate_email,
            candidate_name=application.candidate_name,
            job_title=job.title,
            company_name=job.company_name,
            interview_slots=interview_slots
        )
        
        if success:
            return {
                "message": "Email d'invitation envoyé avec succès",
                "candidate_email": application.candidate_email,
                "slots_count": len(interview_slots)
            }
        else:
            raise HTTPException(status_code=500, detail="Erreur lors de l'envoi de l'email")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur interne: {str(e)}")


@router.post("/interview-slots/candidate-choice")
async def candidate_chooses_slot(payload: CandidateSlotChoiceRequest, background_tasks: BackgroundTasks, db=Depends(get_db)):
    """
    Endpoint pour que le candidat confirme son choix de créneau
    """
    print(f"🎯 CANDIDATE CHOICE: Candidat {payload.application_id} choisit le créneau {payload.slot_id}")
    
    # Vérifier que le créneau existe et est confirmé par le HR
    slot = db.query(InterviewSlot).filter(
        InterviewSlot.id == payload.slot_id,
        InterviewSlot.application_id == payload.application_id,
        InterviewSlot.is_confirmed == True
    ).first()
    
    if not slot:
        raise HTTPException(status_code=400, detail="Créneau non trouvé ou non confirmé")
    
    # Mettre le statut du créneau à "reserved" (choisi par le candidat)
    slot.status = SlotStatus.RESERVED
    
    # Récupérer l'application
    application = db.query(Application).filter(Application.id == payload.application_id).first()
    if application:
        # Maintenant remplir les champs d'entretien
        print(f"🔍 DEBUG: Avant mise à jour - interview_date: {application.interview_date}, interview_time: {application.interview_time}, interview_type: {application.interview_type}")
        
        application.interview_date = slot.start_time
        application.interview_time = slot.start_time.strftime('%H:%M')
        application.interview_type = "Entretien confirmé"
        application.status = 'interview_scheduled'
        
        print(f"🔍 DEBUG: Après mise à jour - interview_date: {application.interview_date}, interview_time: {application.interview_time}, interview_type: {application.interview_type}")
        print(f"✅ CANDIDATE CHOICE: Données d'entretien mises à jour pour l'application {application.id}")
        
        # Send immediate notification to HR about candidate's choice
        notification_service = InterviewNotificationService()
        background_tasks.add_task(
            notification_service.send_candidate_choice_notification_to_hr,
            application.id
        )
        
        # Schedule all future notifications
        scheduler = InterviewNotificationScheduler()
        background_tasks.add_task(
            scheduler.schedule_interview_notifications,
            application.id
        )
        
    else:
        print(f"❌ CANDIDATE CHOICE: Application {payload.application_id} non trouvée")
    
    db.commit()
    print(f"🔍 DEBUG: Commit effectué")

    
    
    return {
        "success": True, 
        "message": "Choix de créneau confirmé avec succès",
        "slot": {
            "id": slot.id,
            "start_time": slot.start_time.isoformat(),
            "end_time": slot.end_time.isoformat(),
            "status": slot.status.value
        }
    }


@router.get("/interview-slots/zoom-meeting-setup", response_class=HTMLResponse)
async def zoom_meeting_setup(
    request: Request,
    application_id: int = Query(..., description="ID de la candidature"),
    admin_id: int = Query(..., description="ID de l'administrateur HR"),
    db: Session = Depends(get_db)
):
    """Page de configuration Zoom pour créer une réunion d'entretien"""
    try:
        # Récupérer les informations de la candidature
        application = db.query(Application).filter(Application.id == application_id).first()
        if not application:
            raise HTTPException(status_code=404, detail="Candidature non trouvée")
        
        # Récupérer les informations du job
        job = db.query(Job).filter(Job.id == application.job_id).first()
        if not job:
            raise HTTPException(status_code=404, detail="Offre d'emploi non trouvée")
        
        # Récupérer les informations de l'entreprise
        company = db.query(Company).filter(Company.id == job.company_id).first()
        if not company:
            raise HTTPException(status_code=404, detail="Entreprise non trouvée")
        
        # Récupérer les informations du candidat
        candidate_profile = application.candidate_profile
        if not candidate_profile:
            raise HTTPException(status_code=404, detail="Profil candidat non trouvé")
        
        # Récupérer les informations de l'admin HR
        hr_admin = db.query(HRAdmin).filter(HRAdmin.id == admin_id).first()
        if not hr_admin:
            raise HTTPException(status_code=404, detail="Administrateur HR non trouvé")
        
        # Préparer les données pour le template
        context = {
            "request": request,
            "application_id": application_id,
            "admin_id": admin_id,
            "candidate_name": candidate_profile.name or "Candidat",
            "job_title": job.title,
            "company_name": company.company_name,
            "interview_date": application.interview_date.strftime("%d/%m/%Y à %H:%M") if application.interview_date else "Non défini",
            "interview_time": application.interview_time or "Non défini",
            "hr_admin_name": f"{hr_admin.first_name} {hr_admin.last_name}",
            "hr_admin_email": hr_admin.email
        }
        
        return templates.TemplateResponse("HR-dep/zoom-meeting-setup.html", context)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors du chargement de la page: {str(e)}")


@router.post("/interview-slots/create-meet")
async def create_meet(request: CreateMeetRequest):
    """Create a Zoom meeting via n8n webhook"""
    try:
        # Get n8n URL from environment variables
        n8n_base_url = os.getenv("N8N_WEBHOOK_URL")
        if not n8n_base_url:
            raise HTTPException(status_code=500, detail="N8N_WEBHOOK_URL environment variable not set")
        
        # Construct the full URL
        n8n_url = f"{n8n_base_url}/create-meet"
        
        # Prepare the payload for n8n
        payload = {
            "application_id": request.application_id,
            "admin_id": request.admin_id,
            "candidate_name": request.candidate_name,
            "job_title": request.job_title,
            "company_name": request.company_name,
            "interview_date": request.interview_date,
            "timestamp": datetime.now().isoformat()
        }
        
        print(f"🚀 Sending request to n8n: {n8n_url}")
        print(f"📦 Payload: {json.dumps(payload, indent=2)}")
        
        # Send request to n8n
        response = requests.post(
            n8n_url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"📡 N8N Response Status: {response.status_code}")
        print(f"📄 N8N Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            try:
                response_data = response.json()
                print(f"✅ N8N Response Data: {json.dumps(response_data, indent=2)}")
                
                # If n8n returned meeting URLs, store them and send to candidate
                if "start" in response_data and "join" in response_data:
                    await store_meeting_and_notify_candidate(
                        request.application_id,
                        request.candidate_name,
                        request.job_title,
                        request.company_name,
                        response_data["start"],
                        response_data["join"]
                    )
                    
            except json.JSONDecodeError:
                response_text = response.text
                print(f"📝 N8N Response Text: {response_text}")
                response_data = {"message": response_text, "status": "success"}
        else:
            error_text = response.text
            print(f"❌ N8N Error Response: {error_text}")
            response_data = {"error": error_text, "status": "error"}
        
        # Return the response to the frontend
        return JSONResponse(
            status_code=200 if response.status_code == 200 else 500,
            content={
                "success": response.status_code == 200,
                "n8n_response": response_data,
                "n8n_status_code": response.status_code,
                "message": "Meeting creation request sent to n8n successfully" if response.status_code == 200 else "Error from n8n webhook"
            }
        )
        
    except requests.exceptions.Timeout:
        error_msg = "Timeout while calling n8n webhook"
        print(f"⏰ {error_msg}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": error_msg}
        )
    except requests.exceptions.ConnectionError:
        error_msg = "Could not connect to n8n webhook"
        print(f"🔌 {error_msg}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": error_msg}
        )
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        print(f"💥 {error_msg}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": error_msg}
        )


async def store_meeting_and_notify_candidate(
    application_id: int,
    candidate_name: str,
    job_title: str,
    company_name: str,
    start_url: str,
    join_url: str
):
    """Store meeting details in database and send join link to candidate"""
    try:
        db = SessionLocal()
        
        # Get application details
        application = db.query(Application).filter(Application.id == application_id).first()
        if not application:
            print(f"❌ Application {application_id} not found")
            return
        
        # Update application with meeting details
        application.google_meet_link = join_url  # Using existing field for join URL
        application.google_calendar_event_id = start_url  # Using existing field for start URL
        db.commit()
        
        print(f"✅ Meeting details stored for application {application_id}")
        print(f"📧 Start URL: {start_url}")
        print(f"👥 Join URL: {join_url}")
        
        # Send email to candidate with join link
        from utils1.interview_notifications import InterviewNotificationService
        notification_service = InterviewNotificationService()
        
        # Send meeting link to candidate
        result = notification_service.send_meeting_time_candidate_link(application_id)
        
        if result:
            print(f"✅ Meeting link sent to candidate: {candidate_name}")
        else:
            print(f"❌ Failed to send meeting link to candidate: {candidate_name}")
        
        db.close()
        
    except Exception as e:
        print(f"❌ Error storing meeting and notifying candidate: {e}")


