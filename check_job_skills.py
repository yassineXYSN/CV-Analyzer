#!/usr/bin/env python3
"""
Script to check which jobs have skills in the job_skills table
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from databasehr.database import SessionLocal
from databasehr.models import Job, JobSkill

def check_job_skills():
    """Check which jobs have skills"""
    print("🔍 Checking job skills in database...")
    
    db = SessionLocal()
    try:
        # Get all jobs with their skills
        jobs_with_skills = db.query(Job).join(JobSkill).all()
        jobs_without_skills = db.query(Job).outerjoin(JobSkill).filter(JobSkill.id.is_(None)).all()
        
        print(f"\n📋 Jobs WITH skills ({len(jobs_with_skills)}):")
        for job in jobs_with_skills:
            skills = db.query(JobSkill).filter(JobSkill.job_id == job.id).all()
            print(f"   - Job ID: {job.id}, Title: '{job.title}'")
            for skill in skills:
                print(f"     • {skill.skill_name} ({skill.skill_level}) - Required: {skill.is_required}")
        
        print(f"\n⚠️  Jobs WITHOUT skills ({len(jobs_without_skills)}):")
        for job in jobs_without_skills:
            print(f"   - Job ID: {job.id}, Title: '{job.title}'")
        
        print(f"\n💡 To fix the 'Aucune question générée' error:")
        print("   1. Make sure the job you're testing has skills in the job_skills table")
        print("   2. Skills should have is_required = 1")
        print("   3. The quiz generation will only work for jobs with required skills")
        
    except Exception as e:
        print(f"❌ Error checking job skills: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    check_job_skills()
