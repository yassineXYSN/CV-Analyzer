import json
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse, Response
from fastapi.templating import Jinja2Templates
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import os
from dotenv import load_dotenv
from databasehr.database import engine
import databasehr.models as models
from routers.hr import (
    authhr, company, department, 
    employee, job, application, candidate, 
    dashboard, admin_router, quiz
)
from database import engine
import databaseclient.models as models
from routers.client_dep import auth, interview, jobs, profiles, scan, general, notifications
import routers.client_dep.quiz as quiz_client
import time
import base64
import cv2

# Interview system
from emotion_recognizer.emotion_detector import EmotionDetector
# Initialize shared detector
detector = EmotionDetector()
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()
app = FastAPI()

# Création des tables
models.Base.metadata.create_all(bind=engine)

# Create static directory
static_dir = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(static_dir, exist_ok=True)

# Create uploads directory
uploads_dir = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(uploads_dir, exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory=static_dir), name="static")
app.mount("/uploads", StaticFiles(directory=uploads_dir), name="uploads")

# Initialize templates
templates = Jinja2Templates(directory="templates")
# Include routers
app.include_router(auth.router)
app.include_router(jobs.router)
app.include_router(profiles.router)
app.include_router(scan.router)
app.include_router(general.router)
app.include_router(notifications.router)
app.include_router(quiz_client.router)
app.include_router(authhr.router)
app.include_router(company.router)
app.include_router(department.router)
app.include_router(employee.router)
app.include_router(job.router)
app.include_router(application.router)
app.include_router(candidate.router)
app.include_router(dashboard.router)
app.include_router(admin_router.router)
app.include_router(quiz.router)
# Interview

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclure le router
app.include_router(interview.router)
# --- Run system test ---
@app.get("/run_tests")
async def run_tests():
    """Run system tests (HR/Client + Interview)"""
    results = {
        "model_loaded": detector.model is not None,
        "camera_accessible": get_camera().isOpened(),
        "face_cascade_loaded": not detector.face_cascade.empty(),
        "timestamp": time.time(),
    }
    return results
# Favicon handler: serve static favicon if present, otherwise return a tiny placeholder
@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    path = os.path.join(static_dir, "favicon.ico")
    if os.path.exists(path):
        return FileResponse(path)
    # 1x1 transparent PNG (base64) to avoid 404s if no favicon provided
    import base64
    png_b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO3nSxkAAAAASUVORK5CYII="
    return Response(content=base64.b64decode(png_b64), media_type="image/png")

'''# 404 Error Handler
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle 404 and other HTTP errors with custom error pages"""
    if exc.status_code == 404:
        # Determine which template to use based on the request path
        if request.url.path.startswith('/hr') or request.url.path.startswith('/api/hr'):
            return templates.TemplateResponse("HR-dep/404.html", {"request": request})
        else:
            return templates.TemplateResponse("client-dep/404.html", {"request": request})
    
    # For other HTTP errors, return a generic error
    return templates.TemplateResponse("client-dep/404.html", {"request": request})

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors"""
    return templates.TemplateResponse("client-dep/404.html", {"request": request})
'''
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)