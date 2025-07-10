from fastapi import APIRouter, Request
from pydantic import BaseModel
from cv_analyzer.description_generator import generate_job_description

router = APIRouter()

class TopicRequest(BaseModel):
    topic: str

@router.post("/generate-description")
async def generate_description(request: TopicRequest):
    description = generate_job_description(request.topic)
    return {"description": description}

@router.post("/create-detailed-analysis")
async def create_detailed_analysis(request: Request):
    try:
        data = await request.json()
        return {
            "success": True,
            "categorie_scores": {
                "Expérience Professionnelle": 85,
                "Compétences Techniques": 78,
                "Formation & Éducation": 92,
                "Certifications": 65,
                "Compétences Relationnelles": 73,
                "Présentation & Structure": 88
            },
            "good_points": [
                "Solide expérience de 5+ années dans le développement web",
                "Maîtrise excellente des technologies modernes",
                "Formation universitaire pertinente en informatique"
            ],
            "weak_points": [
                "Manque de certifications professionnelles récentes",
                "Peu d'expérience avec les technologies cloud"
            ],
            "improvements": [
                "Obtenir des certifications AWS ou Azure",
                "Contribuer à des projets open source"
            ]
        }
    except Exception as e:
        return {"success": False, "error": str(e)}