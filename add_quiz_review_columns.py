#!/usr/bin/env python3
"""
Database migration script to add quiz_review and quiz_review_date columns to applications table
"""

import sys
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from databasehr.database import DATABASE_URL

def add_quiz_review_columns():
    """Add quiz_review and quiz_review_date columns to applications table"""
    
    # Create engine
    engine = create_engine(DATABASE_URL)
    
    try:
        with engine.connect() as connection:
            # Check if columns already exist
            result = connection.execute(text("""
                SELECT COLUMN_NAME 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = 'applications' 
                AND COLUMN_NAME IN ('quiz_review', 'quiz_review_date')
            """))
            
            existing_columns = [row[0] for row in result.fetchall()]
            
            if 'quiz_review' not in existing_columns:
                print("Adding quiz_review column...")
                connection.execute(text("""
                    ALTER TABLE applications 
                    ADD COLUMN quiz_review TEXT COMMENT 'AI analysis review of quiz performance and candidate assessment'
                """))
                print("✅ quiz_review column added successfully")
            else:
                print("⚠️  quiz_review column already exists")
            
            if 'quiz_review_date' not in existing_columns:
                print("Adding quiz_review_date column...")
                connection.execute(text("""
                    ALTER TABLE applications 
                    ADD COLUMN quiz_review_date DATETIME COMMENT 'Date when the quiz review was generated'
                """))
                print("✅ quiz_review_date column added successfully")
            else:
                print("⚠️  quiz_review_date column already exists")
            
            # Commit the changes
            connection.commit()
            print("\n🎉 Migration completed successfully!")
            
    except Exception as e:
        print(f"❌ Error during migration: {str(e)}")
        return False
    
    return True

if __name__ == "__main__":
    print("🚀 Starting database migration: Adding quiz review columns")
    print("=" * 60)
    
    success = add_quiz_review_columns()
    
    if success:
        print("\n✅ Migration completed successfully!")
        print("The applications table now has quiz_review and quiz_review_date columns.")
    else:
        print("\n❌ Migration failed!")
        sys.exit(1)
