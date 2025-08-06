#!/usr/bin/env python3
"""
Initialize database with quiz tables
"""

from database import engine
from models import Base

def init_quiz_database():
    """Create all database tables including quiz tables"""
    try:
        print("🔧 Creating database tables...")
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created successfully!")
        print("📋 Created tables:")
        print("  - contact")
        print("  - analyse_candidat") 
        print("  - profile_candidat")
        print("  - quiz_attempts")
    except Exception as e:
        print(f"❌ Error creating database tables: {e}")

if __name__ == "__main__":
    init_quiz_database() 