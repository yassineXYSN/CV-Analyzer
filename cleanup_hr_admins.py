#!/usr/bin/env python3
"""
Clean up HR admins with old email addresses
"""

import os
import sys

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from databasehr.database import SessionLocal
from databasehr.models import HRAdmin

def cleanup_hr_admins():
    """Clean up HR admins with old email addresses"""
    print("Cleaning up HR admins...")
    
    db = SessionLocal()
    try:
        # Find and delete HR admins with old email addresses
        old_hr_admins = db.query(HRAdmin).filter(
            HRAdmin.email.in_(["hr@testcompany.com", "yassinchtourou03@gmail.com"])
        ).all()
        
        print(f"Found {len(old_hr_admins)} HR admins to delete:")
        for hr_admin in old_hr_admins:
            print(f"  - {hr_admin.email} (ID: {hr_admin.id})")
            db.delete(hr_admin)
        
        db.commit()
        print("SUCCESS: HR admins cleaned up successfully")
        
    except Exception as e:
        print(f"ERROR: Failed to clean up HR admins: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    cleanup_hr_admins()
