import json
from fastapi import FastAPI, Request, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import extract_information_cv.text_extractor as text_extractor
import extract_information_cv.textcleaner as textcleaner
import extract_information_cv.data_generator as data_generator

from cv_analyzer.information_analyzer import compute_similarity
from cv_analyzer.description_generator import generate_job_description
from pydantic import BaseModel
import os
from dotenv import load_dotenv
import json
load_dotenv()
app = FastAPI()

# Créer le dossier static s'il n'existe pas
os.makedirs("static", exist_ok=True)

# Monter les fichiers statiques CORRECTEMENT
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/analyze", response_class=HTMLResponse)
def analyze_page(request: Request):
    return templates.TemplateResponse("analyze.html", {"request": request})

@app.post("/scan", response_class=HTMLResponse)
async def scan_file(
    request: Request,
    filetoscan: UploadFile = File(...),
    job_description: str = Form(...)
):
    print("DATA_GENERATOR_TOKEN :" + os.getenv("DATA_GENERATOR_TOKEN"))
    print("TEXT_CLEANER_TOKEN :" + os.getenv("TEXT_CLEANER_TOKEN"))
    print("DESCRIPTION_GENERATOR_TOKEN :" + os.getenv("DESCRIPTION_GENERATOR_TOKEN"))
    # Créer le dossier uploads s'il n'existe pas
    os.makedirs("uploads", exist_ok=True)
    
    file_location = f"uploads/{filetoscan.filename}"

    # Save file to disk temporarily
    with open(file_location, "wb") as f:
        f.write(await filetoscan.read())

    # Process the file
    print("Extracting text from the file...")
    pdf_text, images_text = text_extractor.process_file(file_location)
    print("Text extraction completed.")

    # Clean up
    print("Cleaning up the extracted text...")
    pdf_text = textcleaner.cleantext(pdf_text)
    print("Cleaning up the extracted text...")
    # Generate summary
    print("Generating summary ...")
    summary = data_generator.generate_summary(pdf_text, images_text)
    print("Summary generation completed.")
    print("Generating structured data ...")
    data_json = data_generator.generate_json(pdf_text)
    print("Structured data generation completed.")

    # Compute matching score
    score = compute_similarity(summary, job_description)

    return templates.TemplateResponse("result.html", {
        "request": request,
        "filename": filetoscan.filename,
        "pdf_text": pdf_text,
        "images_text": images_text,
        "summary": summary,
        "score": score,
        "data_json": data_json,
        "job_description": job_description
    })

class TopicRequest(BaseModel):
    topic: str

@app.post("/generate-description")
async def generate_description(request: TopicRequest):
    description = generate_job_description(request.topic)
    return {"description": description}



