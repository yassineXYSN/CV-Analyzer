import json
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import os
from dotenv import load_dotenv
from databasehr.database import engine, SessionLocal
import databasehr.models as models
from routers.hr import (
    auth, company, department, 
    employee, job, application, candidate, 
    dashboard, analysis
)
from database import engine
import databaseclient.models as models
from routers.client_dep import auth, jobs, profiles, scan, general


load_dotenv()
app = FastAPI()

# Create database tables
app.include_router(auth.router)
app.include_router(jobs.router)
app.include_router(profiles.router)
app.include_router(scan.router)
app.include_router(general.router)

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

# Include routers
app.include_router(auth.router)
app.include_router(company.router)
app.include_router(department.router)
app.include_router(employee.router)
app.include_router(job.router)
app.include_router(application.router)
app.include_router(candidate.router)
app.include_router(dashboard.router)
app.include_router(analysis.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

