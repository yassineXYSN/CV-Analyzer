#!/usr/bin/env python3
"""
Test script for interview notification emails
Run this to test all email notifications in the interview system
"""

import sys
import os
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from databasehr.database import SessionLocal
from databasehr.models import Application, Job, HRAdmin, Company, Department, InterviewSlot, SlotStatus
from databaseclient.models import ProfileCandidat, Contact, User
from utils1.interview_notifications import InterviewNotificationService

def create_test_data():
    """Create test data for email testing"""
    print("Creating test data...")
    
    db = SessionLocal()
    
    try:
        # Create test company
        company = db.query(Company).filter(Company.company_name == "Test Company").first()
        if not company:
            company = Company(
                company_name="Test Company",
                description="Test company for email notifications",
                website="https://testcompany.com",
                industry="Technology"
            )
            db.add(company)
            db.commit()
            print("SUCCESS: Created test company")
        
        # Create test HR admin
        hr_admin = db.query(HRAdmin).filter(HRAdmin.email == "yassinechtourou03@gmail.com").first()
        if not hr_admin:
            hr_admin = HRAdmin(
                first_name="Test",
                last_name="HR Admin",
                email="yassinechtourou03@gmail.com",
                password_hash="hashed_password",
                role="admin"
            )
            db.add(hr_admin)
            db.commit()
            print("SUCCESS: Created test HR admin")
        
        # Create test department
        department = db.query(Department).filter(Department.name == "Test Department").first()
        if not department:
            department = Department(
                company_id=company.id,
                name="Test Department",
                description="Test department for email notifications"
            )
            db.add(department)
            db.commit()
            print("SUCCESS: Created test department")
        
        # Create test job
        job = db.query(Job).filter(Job.title == "Test Developer Position").first()
        if not job:
            job = Job(
                title="Test Developer Position",
                description="Test job for email notifications",
                company_id=company.id,
                department_id=department.id,
                employment_type="CDI",
                salary_min=50000,
                salary_max=80000,
                status="active"
            )
            db.add(job)
            db.commit()
            print("SUCCESS: Created test job")
        
        # Create test user first
        user = db.query(User).filter(User.email == "yassinechtourou03@gmail.com").first()
        if not user:
            user = User(
                email="yassinechtourou03@gmail.com",
                password_hash="test_password_hash",
                first_name="Test",
                last_name="Candidate",
                is_active=True,
                is_verified=True
            )
            db.add(user)
            db.flush()  # Get the user ID
            print("SUCCESS: Created test user")
        
        # Create test candidate profile
        candidate_profile = db.query(ProfileCandidat).filter(ProfileCandidat.name == "Test Candidate").first()
        if not candidate_profile:
            # Create contact first
            contact = Contact(
                email="yassinechtourou03@gmail.com",
                phone="+1234567890",
                linkedin="https://linkedin.com/in/testcandidate",
                address="Test Address"
            )
            db.add(contact)
            db.flush()  # Get the contact ID
            
            # Create candidate profile
            candidate_profile = ProfileCandidat(
                name="Test Candidate",
                title="Software Developer",
                profile="Test candidate profile for email notifications",
                contact_id=contact.id,
                user_id=user.id,  # Link to user
                yearOfExperience=3
            )
            db.add(candidate_profile)
            db.commit()
            print("SUCCESS: Created test candidate profile")
        
        # Create test application
        application = db.query(Application).filter(
            Application.candidate_profile_id == candidate_profile.id,
            Application.job_id == job.id
        ).first()
        
        if not application:
            # Set interview time to 2 hours from now for testing
            interview_time = datetime.now() + timedelta(hours=2)
            
            application = Application(
                candidate_profile_id=candidate_profile.id,
                job_id=job.id,
                user_id=user.id,  # Add the user ID
                status="interview_scheduled",
                interview_date=interview_time,
                interview_time=interview_time.strftime('%H:%M'),
                interview_type="Entretien confirmé",
                application_date=datetime.now(),
                recommended_by_admin_id=hr_admin.id,  # Add the HR admin ID
                recommendation_comment="Test application for email notifications"  # Add recommendation comment
            )
            db.add(application)
            db.commit()
            print("SUCCESS: Created test application")
        
        # Create test interview slot
        slot = db.query(InterviewSlot).filter(
            InterviewSlot.application_id == application.id
        ).first()
        
        if not slot:
            slot = InterviewSlot(
                job_id=job.id,
                application_id=application.id,
                recruiter_id=hr_admin.id,
                start_time=interview_time,
                end_time=interview_time + timedelta(hours=1),
                status=SlotStatus.RESERVED,
                is_confirmed=True,
                confirmed_at=datetime.now(),
                confirmed_by=hr_admin.id
            )
            db.add(slot)
            db.commit()
            print("SUCCESS: Created test interview slot")
        
        return application.id, hr_admin.id, candidate_profile.id, job.id
        
    except Exception as e:
        print(f"ERROR: Error creating test data: {e}")
        db.rollback()
        return None, None, None, None
    finally:
        db.close()

def test_all_notifications():
    """Test all interview notification emails"""
    print("Testing Interview Notification Emails")
    print("=" * 50)
    
    # Create test data
    application_id, hr_id, candidate_id, job_id = create_test_data()
    
    if not application_id:
        print("ERROR: Failed to create test data")
        return
    
    print(f"Test Application ID: {application_id}")
    print(f"Test HR ID: {hr_id}")
    print(f"Test Candidate ID: {candidate_id}")
    print(f"Test Job ID: {job_id}")
    print()
    
    # Initialize notification service
    notification_service = InterviewNotificationService()
    
    # Test 1: HR notification when candidate chooses time
    print("TEST: Test 1: HR notification when candidate chooses time")
    print("-" * 50)
    try:
        db = SessionLocal()
        result = notification_service.send_candidate_choice_notification_to_hr(application_id)
        if result:
            print("SUCCESS: HR choice notification sent successfully")
        else:
            print("ERROR: Failed to send HR choice notification")
        db.close()
    except Exception as e:
        print(f"ERROR: Error sending HR choice notification: {e}")
    
    print()
    
    # Test 2: 24-hour reminder (both HR and candidate)
    print("TEST: Test 2: 24-hour reminder (HR and candidate)")
    print("-" * 50)
    try:
        db = SessionLocal()
        result = notification_service.send_24h_reminder(application_id)
        if result:
            print("SUCCESS: 24h reminder sent successfully")
        else:
            print("ERROR: Failed to send 24h reminder")
        db.close()
    except Exception as e:
        print(f"ERROR: Error sending 24h reminder: {e}")
    
    print()
    
    # Test 3: 20-minute HR reminder
    print("TEST: Test 3: 20-minute HR reminder")
    print("-" * 50)
    try:
        db = SessionLocal()
        result = notification_service.send_20min_hr_reminder(application_id)
        if result:
            print("SUCCESS: 20min HR reminder sent successfully")
        else:
            print("ERROR: Failed to send 20min HR reminder")
        db.close()
    except Exception as e:
        print(f"ERROR: Error sending 20min HR reminder: {e}")
    
    print()
    
    # Test 4: 15-minute candidate reminder
    print("TEST: Test 4: 15-minute candidate reminder")
    print("-" * 50)
    try:
        db = SessionLocal()
        result = notification_service.send_15min_candidate_reminder(application_id)
        if result:
            print("SUCCESS: 15min candidate reminder sent successfully")
        else:
            print("ERROR: Failed to send 15min candidate reminder")
        db.close()
    except Exception as e:
        print(f"ERROR: Error sending 15min candidate reminder: {e}")
    
    print()
    
    # Test 5: 5-minute HR meeting link
    print("TEST: Test 5: 5-minute HR meeting link")
    print("-" * 50)
    try:
        db = SessionLocal()
        result = notification_service.send_5min_hr_meeting_link(application_id)
        if result:
            print("SUCCESS: 5min HR meeting link sent successfully")
        else:
            print("ERROR: Failed to send 5min HR meeting link")
        db.close()
    except Exception as e:
        print(f"ERROR: Error sending 5min HR meeting link: {e}")
    
    print()
    
    # Test 6: Meeting time candidate link
    print("TEST: Test 6: Meeting time candidate link")
    print("-" * 50)
    try:
        db = SessionLocal()
        result = notification_service.send_meeting_time_candidate_link(application_id)
        if result:
            print("SUCCESS: Meeting time candidate link sent successfully")
        else:
            print("ERROR: Failed to send meeting time candidate link")
        db.close()
    except Exception as e:
        print(f"ERROR: Error sending meeting time candidate link: {e}")
    
    print()
    print("All email tests completed!")
    print("=" * 50)
    print("Check your email inboxes for the test emails:")
    print("   - HR email: yassinechtourou03@gmail.com")
    print("   - Candidate email: yassinechtourou03@gmail.com")
    print()
    print("Note: Make sure your SMTP settings are configured in environment variables:")
    print("   - SMTP_SERVER")
    print("   - SMTP_PORT") 
    print("   - SMTP_USERNAME")
    print("   - SMTP_PASSWORD")
    print("   - FROM_EMAIL")

def cleanup_test_data():
    """Clean up test data"""
    print("Cleaning up test data...")
    
    db = SessionLocal()
    try:
        # Delete test application and related data
        application = db.query(Application).filter(Application.candidate_profile_id == db.query(ProfileCandidat).filter(ProfileCandidat.name == "Test Candidate").first().id).first()
        if application:
            # Delete interview slots
            db.query(InterviewSlot).filter(InterviewSlot.application_id == application.id).delete()
            # Delete application
            db.delete(application)
        
        # Delete test candidate profile and contact
        candidate = db.query(ProfileCandidat).filter(ProfileCandidat.name == "Test Candidate").first()
        if candidate:
            # Delete the contact associated with the candidate
            if candidate.contact_id:
                contact = db.query(Contact).filter(Contact.id == candidate.contact_id).first()
                if contact:
                    db.delete(contact)
            db.delete(candidate)
        
        # Delete test user
        user = db.query(User).filter(User.email == "yassinechtourou03@gmail.com").first()
        if user:
            db.delete(user)
        
        # Delete test job
        job = db.query(Job).filter(Job.title == "Test Developer Position").first()
        if job:
            db.delete(job)
        
        # Delete test department
        department = db.query(Department).filter(Department.name == "Test Department").first()
        if department:
            db.delete(department)
        
        # Delete test HR admin
        hr_admin = db.query(HRAdmin).filter(HRAdmin.email == "yassinechtourou03@gmail.com").first()
        if hr_admin:
            db.delete(hr_admin)
        
        # Delete test company
        company = db.query(Company).filter(Company.company_name == "Test Company").first()
        if company:
            db.delete(company)
        
        db.commit()
        print("SUCCESS: Test data cleaned up successfully")
        
    except Exception as e:
        print(f"ERROR: Error cleaning up test data: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test interview notification emails")
    parser.add_argument("--cleanup", action="store_true", help="Clean up test data after testing")
    parser.add_argument("--cleanup-only", action="store_true", help="Only clean up test data")
    
    args = parser.parse_args()
    
    if args.cleanup_only:
        cleanup_test_data()
    else:
        test_all_notifications()
        
        if args.cleanup:
            print("\n" + "=" * 50)
            cleanup_test_data()
        else:
            print("\nTIP: To clean up test data, run: python test_interview_notifications.py --cleanup")
