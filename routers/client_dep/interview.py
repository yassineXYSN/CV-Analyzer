from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse, JSONResponse, HTMLResponse
import cv2
import threading
import time
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from fastapi.templating import Jinja2Templates

from databaseclient.models import Application, User, Interview
from routers.client_dep.dependencies import get_db, get_current_user
from emotion_recognizer.emotion_detector import EmotionDetector

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
    candidate_name = application.candidate_profile.name

    # Interviewer name (assuming reviewed_by is HRAdmin ID)
    interviewer_name = "HR"  # default value
    if application.reviewed_by:
        hr_admin = db.query(User).filter(User.id == application.reviewed_by).first()
        if hr_admin:
            interviewer_name = hr_admin.full_name

    interview_date = application.interview_date

    return templates.TemplateResponse("/client-dep/interview.html", {
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

        # Get or create interview record
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

        # Start the session
        session_id = detector.start_session(candidate_name, interviewer_name)

        # Update interview record
        interview.start_session = True
        interview.started_at = datetime.now()
        db.commit()

        return JSONResponse({'success': True, 'session_id': session_id})

    except Exception as e:
        return JSONResponse({'success': False, 'message': str(e)})

@router.post("/end_session/{application_id}")
async def end_session(application_id: int, db: Session = Depends(get_db)):
    try:
        # Get the application
        application = db.query(Application).filter(Application.id == application_id).first()
        if not application:
            return JSONResponse({'success': False, 'message': 'Application not found'})

        candidate = application.user

        # Get existing interview record
        interview = db.query(Interview).filter(
            Interview.application_id == application_id,
            Interview.candidate_id == candidate.id
        ).first()
        if not interview:
            return JSONResponse({'success': False, 'message': 'Interview not found'})

        # End the session and get report
        report = detector.end_session()
        
        if report is None:
            return JSONResponse({'success': False, 'message': 'No active session found'})

        neutral_rate = report.get('success_rate', 0)  # This is the neutral emotion percentage
        
        # Rating system: 60%+ = rate 4, 80%+ = rate 5
        if neutral_rate >= 80:
            rate = 5
        elif neutral_rate >= 60:
            rate = 4
        else:
            rate = max(1, int(neutral_rate / 20))  # 1-3 based on percentage ranges
        
        # Determine pass/fail based on 60% threshold
        interview_result = 'PASS' if neutral_rate >= 60 else 'FAIL'
        status = 'APPROVED' if interview_result == 'PASS' else 'REJECTED'

        interview_results[application_id] = {
            'report': report,
            'timestamp': datetime.now().isoformat(),
            'success_rate': neutral_rate,
            'passed': interview_result == 'PASS',
            'candidate_name': application.candidate_profile.name,
            'application_id': application_id,
            'rate': rate
        }

        interview.end_session = True
        interview.ended_at = datetime.now()
        interview.success_rate = neutral_rate
        interview.neutral_rate = neutral_rate
        interview.dominant_emotion = report.get('dominant_emotion', 'neutral')
        interview.total_detections = report.get('total_detections', 0)
        interview.avg_confidence = report.get('avg_confidence', 0)
        interview.session_duration = report.get('session_duration', 0)
        interview.interview_result = interview_result
        interview.rate = rate
        interview.status = status
        db.commit()

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
    return templates.TemplateResponse("/client-dep/interview_results.html", {
        "request": request
    })

@router.get("/api/interview/{application_id}")
async def get_interview_api(application_id: int, db: Session = Depends(get_db)):
    """API endpoint to get interview data for an application"""
    try:
        # Get the application
        application = db.query(Application).filter(Application.id == application_id).first()
        if not application:
            return JSONResponse({'success': False, 'message': 'Application not found'}, status_code=404)

        # Safe access to candidate profile name
        candidate_name = "Unknown Candidate"
        if hasattr(application, 'candidate_profile') and application.candidate_profile:
            candidate_name = getattr(application.candidate_profile, 'name', 'Unknown Candidate')
        
        # Safe access to user ID
        user_id = None
        if hasattr(application, 'user') and application.user:
            user_id = application.user.id

        # Prepare interview data with safe defaults
        interview_data = {
            'application_id': application_id,
            'candidate_name': candidate_name,
            'interview_date': application.interview_date.isoformat() if application.interview_date else None,
            'status': 'NO_INTERVIEW'
        }

        interview = None
        if user_id:
            interview = db.query(Interview).filter(
                Interview.application_id == application_id,
                Interview.candidate_id == user_id
            ).first()

        if interview:
            status_value = 'PENDING'
            if interview.status:
                status_value = interview.status.value if hasattr(interview.status, 'value') else str(interview.status)
            
            interview_data.update({
                'status': status_value,
                'start_session': interview.start_session or False,
                'end_session': interview.end_session or False,
                'success_rate': float(interview.success_rate) if interview.success_rate else 0,
                'neutral_rate': float(interview.neutral_rate) if interview.neutral_rate else 0,
                'dominant_emotion': interview.dominant_emotion or 'neutral',
                'total_detections': interview.total_detections or 0,
                'avg_confidence': float(interview.avg_confidence) if interview.avg_confidence else 0,
                'session_duration': interview.session_duration or 0,
                'interview_result': interview.interview_result or 'PENDING',
                'rate': interview.rate or 0,
                'started_at': interview.started_at.isoformat() if interview.started_at else None,
                'ended_at': interview.ended_at.isoformat() if interview.ended_at else None,
                'scheduled_at': interview.scheduled_at.isoformat() if interview.scheduled_at else None
            })

            # Add results from memory if available
            if application_id in interview_results:
                result_data = interview_results[application_id]
                interview_data.update({
                    'report': result_data.get('report', {}),
                    'passed': result_data.get('passed', False)
                })

        return JSONResponse({'success': True, 'interview': interview_data})

    except Exception as e:
        print(f"Error in get_interview_api for application {application_id}: {str(e)}")
        return JSONResponse({'success': False, 'message': f'Internal server error: {str(e)}'}, status_code=500)

@router.get("/api/interview-result/{application_id}")
async def get_interview_result_api(application_id: int, db: Session = Depends(get_db)):
    """API endpoint to get interview results for an application"""
    try:
        # Get the application
        application = db.query(Application).filter(Application.id == application_id).first()
        if not application:
            return JSONResponse({'success': False, 'message': 'Application not found'}, status_code=404)

        # Get interview from database
        user_id = application.user.id if application.user else None
        if not user_id:
            return JSONResponse({'success': False, 'message': 'No user associated with application'}, status_code=404)

        interview = db.query(Interview).filter(
            Interview.application_id == application_id,
            Interview.candidate_id == user_id
        ).first()

        if not interview or not interview.end_session:
            return JSONResponse({'success': False, 'message': 'No completed interview found'}, status_code=404)

        # Prepare result data
        result_data = {
            'application_id': application_id,
            'candidate_name': application.candidate_profile.name if application.candidate_profile else 'Unknown',
            'success_rate': float(interview.success_rate) if interview.success_rate else 0,
            'neutral_rate': float(interview.neutral_rate) if interview.neutral_rate else 0,
            'dominant_emotion': interview.dominant_emotion or 'neutral',
            'total_detections': interview.total_detections or 0,
            'avg_confidence': float(interview.avg_confidence) if interview.avg_confidence else 0,
            'session_duration': interview.session_duration or 0,
            'interview_result': interview.interview_result or 'PENDING',
            'rate': interview.rate or 0,
            'passed': interview.interview_result == 'PASS',
            'status': interview.status.value if hasattr(interview.status, 'value') else str(interview.status),
            'ended_at': interview.ended_at.isoformat() if interview.ended_at else None
        }

        # Add memory results if available
        if application_id in interview_results:
            memory_result = interview_results[application_id]
            result_data['report'] = memory_result.get('report', {})
            result_data['timestamp'] = memory_result.get('timestamp')

        return JSONResponse({'success': True, 'result': result_data})

    except Exception as e:
        print(f"Error in get_interview_result_api for application {application_id}: {str(e)}")
        return JSONResponse({'success': False, 'message': f'Internal server error: {str(e)}'}, status_code=500)
