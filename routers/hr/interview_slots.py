from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, validator
from typing import List, Optional
from datetime import datetime, timedelta

from databasehr.database import SessionLocal
from databasehr.models import InterviewSlot, SlotStatus, Job, Application, HRAdmin, Company
from .email_service import EmailService

router = APIRouter()


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


@router.get("/api/hr/interview-slots", response_model=List[dict])
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


@router.post("/api/hr/interview-slots")
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


@router.delete("/api/hr/interview-slots/{slot_id}")
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


@router.get("/api/hr/interview-slots/conflicts")
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


@router.post("/api/hr/interview-slots/confirm")
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


@router.get("/api/hr/interview-slots/job-confirmed/{job_id}")
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


@router.post("/api/hr/interview-slots/candidate-choice")
async def candidate_chooses_slot(payload: CandidateSlotChoiceRequest, db=Depends(get_db)):
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


