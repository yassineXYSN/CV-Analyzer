import json
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
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
from routers.client_dep import auth, jobs, profiles, scan, general, notifications


load_dotenv()
app = FastAPI()

# Create database tables
app.include_router(auth.router)
app.include_router(jobs.router)
app.include_router(profiles.router)
app.include_router(scan.router)
app.include_router(general.router)
app.include_router(notifications.router)

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

# 404 Error Handler
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)