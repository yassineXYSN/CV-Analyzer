from huggingface_hub import InferenceClient
import os
from dotenv import load_dotenv

load_dotenv()

HF_TOKEN = os.getenv("HF_TOKEN")
print("🔐 HF_TOKEN loaded:", HF_TOKEN[:10] + "..." if HF_TOKEN else "❌ AUCUN TOKEN")

client = InferenceClient(
    model="HuggingFaceH4/zephyr-7b-beta",
    token=HF_TOKEN,
)

def generate_job_description(topic: str) -> str:
    try:
        response = client.chat_completion(
            messages=[
                {"role": "user", "content": f"Rédige une description de poste pour un profil en {topic}."}
            ],
            max_tokens=150,
            temperature=0.7
        )
        return response.choices[0].message["content"].strip()
    except Exception as e:
        print("❌ ERREUR :", type(e).__name__, "-", str(e))
        return f"[Erreur de génération] {str(e)}"
