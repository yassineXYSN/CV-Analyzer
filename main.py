import json
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import os
from dotenv import load_dotenv
from database import engine
import models
from routers.client_dep import auth, jobs, profiles, scan, general


load_dotenv()
app = FastAPI()

app.include_router(auth.router)
app.include_router(jobs.router)
app.include_router(profiles.router)
app.include_router(scan.router)
app.include_router(general.router)

# Création des tables
models.Base.metadata.create_all(bind=engine)

# Créer le dossier static s'il n'existe pas
static_dir = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(static_dir, exist_ok=True)

# Vérifier que le fichier CSS existe
css_file = os.path.join(static_dir, "style.css")
if not os.path.exists(css_file):
    print(f"⚠️  ATTENTION: Le fichier CSS n'existe pas à {css_file}")
    print(f"📁 Dossier static: {static_dir}")
    print(f"📄 Fichiers dans static: {os.listdir(static_dir) if os.path.exists(static_dir) else 'Dossier inexistant'}")
else:
    print(f"✅ Fichier CSS trouvé: {css_file}")

# Monter les fichiers statiques
app.mount("/static", StaticFiles(directory=static_dir), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
