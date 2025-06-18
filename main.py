from fastapi import FastAPI, Request, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import cv_analyzer.text_extractor as text_extractor
import cv_analyzer.textcleaner as textcleaner
import cv_analyzer.data_generator as data_generator

app = FastAPI()

app.mount("/static", StaticFiles(directory="css"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/scan", response_class=HTMLResponse)
async def scan_file(request: Request, filetoscan: UploadFile = File(...)):
    file_location = f"uploads/{filetoscan.filename}"
    
    # Save file to disk temporarily
    with open(file_location, "wb") as f:
        f.write(await filetoscan.read())
    
    # Process the file (adapt to your text_extractor method)
    pdf_text, images_text = text_extractor.process_file(file_location)

    # Clean up pdf text and images text
    client = textcleaner.intialize_client()
    pdf_text = textcleaner.cleantext(client,pdf_text)

    # Generate summary from cleaned text
    summary = data_generator.generate_summary(client, pdf_text)


    return templates.TemplateResponse("result.html", {
        "request": request,
        "filename": filetoscan.filename,
        "pdf_text": pdf_text,
        "images_text": images_text,
        "summary": summary
    })
