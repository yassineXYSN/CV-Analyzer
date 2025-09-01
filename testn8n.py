import requests
from databasehr.models import HRAdmin, Quiz, QuizSkill, QuizQuestion, ProfileCandidat
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from databasehr.session_manager import current_user_session
from databasehr.database import SessionLocal
from databasehr.models import HRAdmin, Quiz, QuizSkill, QuizQuestion, ProfileCandidat
import os
import requests
from datetime import datetime
from sqlalchemy.orm import Session

'''
# The webhook URL from n8n
url = "https://aminechtourou.app.n8n.cloud/webhook-test/69c5f680-542e-4c5e-82cf-9bd935078c71"
print("Sending file to n8n...")
number = [
    { "skill": "JavaScript", "level": "advanced","nb": 2 },
    { "skill": "Python", "level": "intermediate","nb": 3 }
]
payload = {
    "number": number,
    }
response = requests.post(url, json=payload)

print("Status Code:", response.status_code)
print("Response:", response.text)'''


def get_current_hr_user():
    """Simple dependency to get current HR user from session"""
    user_id = current_user_session.get('user_id')
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    db = SessionLocal()
    try:
        user = db.query(HRAdmin).filter(HRAdmin.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return {"id": user.id, "email": user.email, "first_name": user.first_name, "last_name": user.last_name}
    finally:
        db.close()


def get_db():
    """Database dependency"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
db = SessionLocal()   # create a real SQLAlchemy session
try:
    candidat = db.query(ProfileCandidat).filter(ProfileCandidat.id == 31).first()
    if candidat:
        if candidat.user:  # Check if user exists
            print(candidat.user.id)  # Access user ID through relationship
        else:
            print("No user associated with this profile")
    else:
        print("Profile not found")
except Exception as e:
    print(f"Error: {e}")
finally:
    db.close()



