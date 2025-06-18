from sentence_transformers import SentenceTransformer, util

# Charger le modèle une seule fois (recommandé)
model = SentenceTransformer('BAAI/bge-base-en-v1.5')

# Offre d'emploi (peut être déplacée dans un paramètre si besoin)
job_description = """
Nous recherchons un développeur front-end ayant une expérience en React, TypeScript, HTML/CSS
et une bonne connaissance des pratiques d’accessibilité web.
"""

def compute_similarity(summary_text: str) -> float:
    """Calcule la similarité entre un résumé de CV et l'offre d'emploi"""
    cv_embedding = model.encode(summary_text, convert_to_tensor=True)
    job_embedding = model.encode(job_description, convert_to_tensor=True)
    score = util.cos_sim(cv_embedding, job_embedding).item() * 100
    return round(score, 2)
