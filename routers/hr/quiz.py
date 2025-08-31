from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from databasehr.session_manager import current_user_session
from databasehr.database import SessionLocal
from databasehr.models import HRAdmin

router = APIRouter(prefix="/api/hr/quiz", tags=["Quiz"])

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

class QuizSkillConfig(BaseModel):
    name: str
    questions: int
    difficulty: str

class QuizCreateRequest(BaseModel):
    title: str
    time_limit: int
    skills: List[QuizSkillConfig]
    job_id: Optional[int] = None
    candidate_id: Optional[int] = None

@router.post("/create")
async def create_quiz(quiz_data: QuizCreateRequest, current_user=Depends(get_current_hr_user)):
    """
    Create a new quiz based on form data
    """
    try:
        # Print the received quiz data
        print("=== QUIZ CREATION REQUEST ===")
        print(f"User: {current_user.get('email', 'Unknown')}")
        print(f"Quiz Title: {quiz_data.title}")
        print(f"Time Limit: {quiz_data.time_limit} minutes")
        print(f"Job ID: {quiz_data.job_id}")
        print(f"Candidate ID: {quiz_data.candidate_id}")
        print("\nSkills Configuration:")

        for skill in quiz_data.skills:
            print(f"  - {skill.name}: {skill.questions} questions ({skill.difficulty} difficulty)")

        print("=============================")

        # For now, just return success message
        # TODO: Implement actual quiz creation logic
        return {
            "success": True,
            "message": "Quiz data received successfully",
            "quiz_data": {
                "title": quiz_data.title,
                "time_limit": quiz_data.time_limit,
                "skills_count": len(quiz_data.skills),
                "job_id": quiz_data.job_id,
                "candidate_id": quiz_data.candidate_id
            }
        }

    except Exception as e:
        print(f"Error creating quiz: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating quiz: {str(e)}")
