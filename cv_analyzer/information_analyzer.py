from sentence_transformers import SentenceTransformer, util

# Charger le modèle une seule fois (recommandé)
model = SentenceTransformer('BAAI/bge-base-en-v1.5')


def compute_similarity(summary_text: str, job_description: str) -> float:
    cv_embedding = model.encode(summary_text, convert_to_tensor=True)
    job_embedding = model.encode(job_description, convert_to_tensor=True)
    score = util.cos_sim(cv_embedding, job_embedding).item() * 100
    return round(score, 2)

