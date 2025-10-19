#!/usr/bin/env python3
"""
Test HR Meeting Link Email
This script tests the 5-minute HR meeting link email with real database data.
"""

import os
import sys

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from databasehr.database import SessionLocal
from databasehr.models import Application, Job, HRAdmin, Company, Department, ProfileCandidat, Contact, User
from utils1.interview_notifications import InterviewNotificationService

def test_hr_meeting_link():
    """Test the 5-minute HR meeting link email with real data"""
    print("=" * 60)
    print("Testing HR Meeting Link Email")
    print("=" * 60)
    
    db = SessionLocal()
    try:
        # Find an existing application
        application = db.query(Application).first()
        
        if not application:
            print("ERROR: No applications found in database")
            print("Please create an application first or run the interview notification test")
            return
        
        print(f"Found application ID: {application.id}")
        
        # Get related data
        job = db.query(Job).filter(Job.id == application.job_id).first()
        company = db.query(Company).filter(Company.id == job.company_id).first() if job else None
        candidate = application.candidate_profile
        hr_admin = db.query(HRAdmin).first()
        
        print(f"Job: {job.title if job else 'Not found'}")
        print(f"Company: {company.company_name if company else 'Not found'}")
        print(f"Candidate: {candidate.name if candidate else 'Not found'}")
        print(f"HR Admin: {hr_admin.email if hr_admin else 'Not found'}")
        print("-" * 60)
        
        if not hr_admin:
            print("ERROR: No HR admin found in database")
            return
        
        # Test the notification service
        notification_service = InterviewNotificationService()
        
        print("Sending 5-minute HR meeting link email...")
        result = notification_service.send_5min_hr_meeting_link(application.id)
        
        if result:
            print("SUCCESS: HR meeting link email sent!")
            print(f"Check your inbox at: {hr_admin.email}")
            print("\nThe email should contain a link to:")
            print(f"http://localhost:8000/api/hr/interview-slots/zoom-meeting-setup?application_id={application.id}&admin_id={hr_admin.id}")
        else:
            print("ERROR: Failed to send HR meeting link email")
            
    except Exception as e:
        print(f"ERROR: {e}")
    finally:
        db.close()
    
    print("\n" + "=" * 60)
    print("Test completed!")
    print("=" * 60)

if __name__ == "__main__":
    test_hr_meeting_link()
