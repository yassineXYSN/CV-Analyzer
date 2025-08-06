from sqlalchemy import Column, Integer, String, ForeignKey, JSON, DateTime, Float
from database import Base
from datetime import datetime

# QuizAttempt table for quiz results and attempts
class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"
    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("profile_candidat.id"))
    job_title = Column(String(255))
    difficulty = Column(String(50))
    questions = Column(JSON)
    answers = Column(JSON)
    total_score = Column(Float)
    category_scores = Column(JSON)
    detailed_results = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    # candidate = relationship("ProfileCandidat")  # If needed, import relationship and ProfileCandidat from the correct module

# If you have a Quiz table, define it here as well (based on your README):
# class Quiz(Base):
#     __tablename__ = "quiz"
#     id = Column(Integer, primary_key=True, index=True)
#     title = Column(String)
#     job_title = Column(String)
#     difficulty = Column(String)
#     questions = Column(JSON)
#     created_at = Column(DateTime, default=datetime.utcnow)
#     candidate_id = Column(Integer, ForeignKey("profile_candidat.id"))
