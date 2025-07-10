from databasehr.database import SessionLocal
import databasehr.models as models

def insert_candidate_data(data_json, summary):
    db = SessionLocal()
    try:
        contact = models.Contact(**data_json["contact"])
        db.add(contact)
        db.commit()
        db.refresh(contact)

        analyse = models.AnalyseCandidat(analyse=summary)
        db.add(analyse)
        db.commit()
        db.refresh(analyse)

        profile = models.ProfileCandidat(
            name=data_json.get("name"),
            title=data_json.get("title"),
            profile=data_json.get("profile"),
            contact_id=contact.id,
            analyse_id=analyse.id,
            education=data_json.get("education"),
            languages=data_json.get("languages"),
            certificates=data_json.get("certificates"),
            skills=data_json.get("skills"),
        )
        db.add(profile)
        db.commit()
        db.refresh(profile)
        
        return profile.id  # Retourner l'ID du profil créé

    except Exception as e:
        db.rollback()
        print("[ERREUR]", e)
        return None
    finally:
        db.close()
