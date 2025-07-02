from database import SessionLocal
from models import Contact, AnalyseCandidat, ProfileCandidat
import json

def insert_candidate_data(data_json, summary, user_id=None):
    """Insert candidate data into database and optionally link to user"""
    db = SessionLocal()
    try:
        # Insert contact
        contact = Contact(
            email=data_json["contact"]["email"],
            phone=data_json["contact"]["phone"],
            linkedin=data_json["contact"]["linkedin"],
            address=data_json["contact"]["address"]
        )
        db.add(contact)
        db.flush()  # Get the ID without committing
        
        # Insert analysis
        analyse = AnalyseCandidat(analyse=summary)
        db.add(analyse)
        db.flush()  # Get the ID without committing
        
        # Insert profile with user link
        profile = ProfileCandidat(
            name=data_json["name"],
            title=data_json["title"],
            profile=data_json["profile"],
            contact_id=contact.id,
            analyse_id=analyse.id,
            user_id=user_id,  # Link to user if provided
            education=json.dumps(data_json["education"]),
            languages=json.dumps(data_json["languages"]),
            certificates=json.dumps(data_json["certificates"]),
            skills=json.dumps(data_json["skills"])
        )
        db.add(profile)
        db.commit()
        
        return profile.id
        
    except Exception as e:
        db.rollback()
        print(f"Error inserting candidate data: {e}")
        raise e
    finally:
        db.close()
