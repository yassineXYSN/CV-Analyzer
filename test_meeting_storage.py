#!/usr/bin/env python3
"""
Test Meeting Storage in Database
This script verifies that meeting URLs are properly stored in the database.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from databasehr.database import SessionLocal
from databasehr.models import Application

def test_meeting_storage():
    """Test that meeting URLs are stored in the database"""
    print("=" * 60)
    print("Testing Meeting Storage in Database")
    print("=" * 60)
    
    try:
        db = SessionLocal()
        
        # Get application 38 (or any application you want to test)
        application = db.query(Application).filter(Application.id == 38).first()
        
        if not application:
            print("❌ Application 38 not found")
            return
        
        print(f"📋 Application Details:")
        print(f"   ID: {application.id}")
        print(f"   Candidate: {application.candidate_profile.name if application.candidate_profile else 'N/A'}")
        print(f"   Job: {application.job.title if application.job else 'N/A'}")
        print(f"   Company: {application.job.company.company_name if application.job and application.job.company else 'N/A'}")
        
        print(f"\n🔗 Meeting URLs:")
        print(f"   Start URL (Host): {application.google_calendar_event_id or 'Not set'}")
        print(f"   Join URL (Participant): {application.google_meet_link or 'Not set'}")
        
        if application.google_calendar_event_id and application.google_meet_link:
            print("\n✅ SUCCESS: Meeting URLs are stored!")
            
            # Test if URLs are valid Zoom links
            if "zoom.us" in application.google_calendar_event_id:
                print("✅ Start URL appears to be a valid Zoom link")
            else:
                print("⚠️  Start URL doesn't appear to be a Zoom link")
                
            if "zoom.us" in application.google_meet_link:
                print("✅ Join URL appears to be a valid Zoom link")
            else:
                print("⚠️  Join URL doesn't appear to be a Zoom link")
        else:
            print("\n❌ Meeting URLs are not stored")
            print("   This means the create-meet endpoint hasn't been called yet")
        
        db.close()
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
    
    print("\n" + "=" * 60)
    print("Test completed!")
    print("=" * 60)

if __name__ == "__main__":
    test_meeting_storage()
