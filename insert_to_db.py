from database import SessionLocal
import models

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

    except Exception as e:
        db.rollback()
        print("[ERREUR]", e)
    finally:
        db.close()



