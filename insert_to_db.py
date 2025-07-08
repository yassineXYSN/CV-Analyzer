from database import SessionLocal
from models import Contact, AnalyseCandidat, ProfileCandidat
import json

def insert_candidate_data(data_json, summary, user_id):
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
        new_profile = ProfileCandidat(
            name=data_json.get('name', ''),
            title=data_json.get('title', ''),
            profile=data_json.get('profile', ''),
            education=json.dumps(data_json.get('education', [])),
            languages=json.dumps(data_json.get('languages', [])),
            certificates=json.dumps(data_json.get('certificates', [])),
            skills=json.dumps(data_json.get('skills', [])),
            yearOfExperience=data_json.get('yearsOfExperience', '0'),
            user_id=user_id,
        )
        db.add(new_profile)
        db.commit()
        
        return new_profile.id
        
    except Exception as e:
        db.rollback()
        print(f"Error inserting candidate data: {e}")
        raise e
    finally:
        db.close()
