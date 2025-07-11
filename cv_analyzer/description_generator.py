from huggingface_hub import InferenceClient
import os
from dotenv import load_dotenv
import json


load_dotenv()

HF_TOKEN = os.getenv("DESCRIPTION_GENERATOR_TOKEN")

client = InferenceClient(
    model="HuggingFaceH4/zephyr-7b-beta",
    token=HF_TOKEN,
)

def generate_job_description(selectedProfiles) -> str:
    if isinstance(selectedProfiles, str):
        selectedProfiles = json.loads(selectedProfiles)

    jobs_text = "\n".join([f"- {profile['name']}" for profile in selectedProfiles])
    prompt = f"""
    Tu es un expert en ressources humaines. À partir d'une liste de titres de postes, génère une description globale qui présente clairement les rôles, responsabilités et compétences clés requises pour ces métiers.

    Liste des postes :
    {jobs_text}

    Génère une description combinée qui résume les principales attentes pour un candidat qui postule à ces postes.
    La description doit être claire, professionnelle et adaptée à une évaluation de compatibilité avec un CV.
    """
    try:
        response = client.chat_completion(
            messages=[
            {
                "role": "user",
                "content": prompt
            }
            ],
            max_tokens=150,
            temperature=0.7
        )
        return response.choices[0].message["content"].strip()
    except Exception as e:
        print("❌ ERREUR :", type(e).__name__, "-", str(e))
        return f"[Erreur de génération] {str(e)}"
