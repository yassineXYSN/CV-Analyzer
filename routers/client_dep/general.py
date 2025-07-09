from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from database import SessionLocal
from routers.client_dep.dependencies import get_db, get_current_user
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import os


router = APIRouter()
# Templates
# Aller au dossier parent (c'est là que se trouve le vrai dossier templates)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

# Dossier correct des templates (C:\Users\yassine\Documents\GitHub\Training\templates)
templates_dir = os.path.join(BASE_DIR, "templates")

templates = Jinja2Templates(directory=templates_dir)


@router.get("/", response_class=HTMLResponse)
def home(request: Request, db: Session = Depends(get_db)):
    current_user = get_current_user(request, db)

    return templates.TemplateResponse("client-dep/index.html", {
        "request": request,
        "current_user": current_user
    })
