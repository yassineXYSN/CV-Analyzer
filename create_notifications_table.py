from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Text, ForeignKey
from databaseclient.models import Base
from sqlalchemy.orm import sessionmaker
import os
import databaseclient.models
from dotenv import load_dotenv

load_dotenv()

# Database configuration
# Configuration de la base de données
DATABASE_HOST = os.getenv("DATABASE_HOST", "localhost")
DATABASE_PORT = os.getenv("DATABASE_PORT", "3306")
DATABASE_USER = os.getenv("DATABASE_USER", "root")
DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD", "")
DATABASE_NAME = os.getenv("DATABASE_NAME", "cv_analyzer_pro")

# Construction de l'URL de connexion
SQLALCHEMY_DATABASE_URL = f"mysql+pymysql://{DATABASE_USER}:{DATABASE_PASSWORD}@{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Notification(Base):
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    type = Column(String(50), nullable=False)
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, nullable=False)
    
    # Optional fields for application-related notifications
    application_id = Column(Integer, ForeignKey("applications.id"), nullable=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=True)
    
    # Additional data
    status = Column(String(50), nullable=True)
    company_name = Column(String(200), nullable=True)
    job_title = Column(String(200), nullable=True)
    admin_name = Column(String(100), nullable=True)

def create_notifications_table():
    """Create the notifications table"""
    try:
        # Create the table
        Notification.__table__.create(engine, checkfirst=True)
        print("✅ Notifications table created successfully!")
        return True
    except Exception as e:
        print(f"❌ Error creating notifications table: {e}")
        return False


