from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse, JSONResponse, HTMLResponse
import cv2
import threading
import time
from datetime import datetime, timedelta

from fastapi.templating import Jinja2Templates
from requests import Session
from databaseclient.models import Application, User, Interview  # Assurez-vous que Interview est importé
from emotion_recognizer.emotion_detector import EmotionDetector
from routers.client_dep.dependencies import get_db, get_current_user
router = APIRouter()
templates = Jinja2Templates(directory="templates")
detector = EmotionDetector()

# Global variables
camera = None
camera_lock = threading.Lock()
interview_results = {}  # Store results in memory (in production, use database)

def get_camera():
    """Get camera instance (singleton pattern)"""
    global camera
    if camera is None:
        camera = cv2.VideoCapture(0)
        camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        camera.set(cv2.CAP_PROP_FPS, 30)
    return camera

def generate_frames():
    """Generate video frames with emotion detection"""
    camera = get_camera()
    while True:
        with camera_lock:
            success, frame = camera.read()
            if not success:
                break

            results = detector.detect_faces_and_emotions(frame)

            for result in results:
                x, y, w, h = result['bbox']
                emotion = result['emotion']
                confidence = result['confidence']

                if detector.session_data['session_active']:
                    detector.record_emotion(emotion, confidence)

                # Only add text label without rectangle
                label = f"{emotion}: {confidence:.2f}"
                cv2.putText(frame, label, (x, y - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

            ret, buffer = cv2.imencode('.jpg', frame)
            frame_bytes = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

@router.get("/interview/{application_id}", response_class=HTMLResponse)
async def interview_page(request: Request, application_id: int, db: Session = Depends(get_db)):
    # Get the application
    application = db.query(Application).filter(Application.id == application_id).first()
    if not application:
        return HTMLResponse("Application not found", status_code=404)

    # Candidate name from profile
    candidate_name = application.candidate_profile.name  # ✅ use 'name' instead of 'full_name'

    # Interviewer name (assuming reviewed_by is HRAdmin ID)
    interviewer_name = "HR"  # default value
    if application.reviewed_by:
        hr_admin = db.query(User).filter(User.id == application.reviewed_by).first()
        if hr_admin:
            interviewer_name = hr_admin.full_name  # adjust if your User model has separate first_name/last_name

    interview_date = application.interview_date

    return templates.TemplateResponse("client-dep/interview.html", {
        "request": request,
        "candidate_name": candidate_name,
        "interviewer_name": interviewer_name,
        "interview_date": interview_date,
        "application_id": application_id
    })

@router.get("/video_feed")
async def video_feed():
    return StreamingResponse(generate_frames(),
                             media_type='multipart/x-mixed-replace; boundary=frame')

# -------------------------------
# Start session
# -------------------------------
@router.post("/start_session/{application_id}")
async def start_session(application_id: int, db: Session = Depends(get_db)):
    try:
        application = db.query(Application).filter(Application.id == application_id).first()
        if not application:
            return JSONResponse({'success': False, 'message': 'Application not found'})

        candidate_id = application.user.id
        candidate_name = application.candidate_profile.name
        interviewer_name = "HR"

        if application.reviewed_by:
            hr_admin = db.query(User).filter(User.id == application.reviewed_by).first()
            if hr_admin:
                interviewer_name = getattr(hr_admin, 'name', 'HR')

        # Récupérer ou créer interview
        interview = db.query(Interview).filter(
            Interview.application_id == application_id,
            Interview.candidate_id == candidate_id
        ).first()
        if not interview:
            interview = Interview(
                application_id=application_id,
                candidate_id=candidate_id,
                status="PENDING",
                start_session=False,
                end_session=False,
                scheduled_at=application.interview_date
            )
            db.add(interview)
            db.commit()
            db.refresh(interview)

        # Démarrer la session
        session_id = detector.start_session(candidate_name, interviewer_name)

        # Mettre à jour l'interview
        interview.start_session = True
        interview.started_at = datetime.now()
        db.commit()

        return JSONResponse({'success': True, 'session_id': session_id})

    except Exception as e:
        return JSONResponse({'success': False, 'message': str(e)})

@router.post("/end_session/{application_id}")
async def end_session(application_id: int, db: Session = Depends(get_db)):
    try:
        # Récupérer l'application
        application = db.query(Application).filter(Application.id == application_id).first()
        if not application:
            return JSONResponse({'success': False, 'message': 'Application not found'})

        candidate = application.user

        # Récupérer interview existante
        interview = db.query(Interview).filter(
            Interview.application_id == application_id,
            Interview.candidate_id == candidate.id
        ).first()
        if not interview:
            return JSONResponse({'success': False, 'message': 'Interview not found'})

        # Terminer la session dans EmotionDetector
        report = detector.end_session()  # renvoie un dict JSON-safe

        # Mettre à jour l'interview
        interview.end_session = True
        db.commit()

        # Retourner succès avec rapport
        return JSONResponse({'success': True, 'report': report})

    except Exception as e:
        return JSONResponse({'success': False, 'message': str(e)})

@router.get("/get_interview_result/{application_id}")
async def get_interview_result(application_id: int):
    """Get saved interview result for an application"""
    try:
        if application_id in interview_results:
            return JSONResponse({
                'success': True, 
                'result': interview_results[application_id]
            })
        else:
            return JSONResponse({
                'success': False, 
                'message': 'No interview result found for this application'
            })
    except Exception as e:
        return JSONResponse({'success': False, 'message': str(e)})

@router.get("/get_all_interview_results")
async def get_all_interview_results():
    """Get all saved interview results"""
    try:
        return JSONResponse({
            'success': True, 
            'results': interview_results
        })
    except Exception as e:
        return JSONResponse({'success': False, 'message': str(e)})

@router.get("/get_live_stats")
async def get_live_stats():
    return JSONResponse(detector.get_live_stats())

@router.get("/run_tests")
async def run_tests():
    results = {
        'model_loaded': detector.model is not None,
        'camera_accessible': get_camera().isOpened(),
        'face_cascade_loaded': not detector.face_cascade.empty(),
        'timestamp': time.time()
    }
    return JSONResponse(results)

@router.get("/interview-results", response_class=HTMLResponse)
async def interview_results_page(request: Request):
    """Display all interview results in a dashboard"""
    return templates.TemplateResponse("interview-results.html", {
        "request": request
    })
