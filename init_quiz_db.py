#!/usr/bin/env python3
"""
Initialize database with quiz tables
"""

from database import engine, Base
from models import QuizAttempt, JobQuizAssignment

def init_quiz_database():
    """Initialize the quiz database tables"""
    print("Creating quiz database tables...")
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    print("✅ Quiz database tables created successfully!")
    print("   - quiz_attempts")
    print("   - job_quiz_assignments")

if __name__ == "__main__":
    init_quiz_database() 