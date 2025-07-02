from sqlalchemy import Column, Integer, String, ForeignKey, JSON, Text, DateTime, Numeric, Enum, Date, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
from datetime import datetime
import enum

class EmploymentType(enum.Enum):
    CDI = "CDI"
    CDD = "CDD"
    STAGE = "STAGE"
    FREELANCE = "FREELANCE"
    ALTERNANCE = "ALTERNANCE"

class JobStatus(enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    CLOSED = "CLOSED"


class Contact(Base):
    __tablename__ = "contact"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(Text)
    phone = Column(Text)
    linkedin = Column(Text)
    address = Column(Text)

class AnalyseCandidat(Base):
    __tablename__ = "analyse_candidat"
    id = Column(Integer, primary_key=True, index=True)
    analyse = Column(Text)

class ProfileCandidat(Base):
    __tablename__ = "profile_candidat"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(Text)
    title = Column(Text)
    profile = Column(Text)
    contact_id = Column(Integer, ForeignKey("contact.id"))
    analyse_id = Column(Integer, ForeignKey("analyse_candidat.id"))
    education = Column(JSON)
    languages = Column(JSON)
    certificates = Column(JSON)
    skills = Column(JSON)

    contact = relationship("Contact")
    analyse = relationship("AnalyseCandidat")

class HrAdmin(Base):
    __tablename__ = "hr_admins"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    role = Column(Enum('super_admin', 'hr_admin', 'hr_manager', name='admin_role'), default='hr_admin')
    is_active = Column(Integer, default=1)
    last_login = Column(DateTime)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class Company(Base):
    __tablename__ = "companies"
    id = Column(Integer, primary_key=True, index=True)
    company_name = Column(String(255), nullable=False)
    industry = Column(String(100))
    company_size = Column(Enum('1-10', '11-50', '51-200', '201-1000', '1000+', name='company_size_enum'))
    founded_year = Column(Integer)
    description = Column(Text)
    logo_url = Column(String(500))
    address = Column(Text)
    phone = Column(String(20))
    email = Column(String(255))
    website = Column(String(255))
    linkedin_url = Column(String(255))
    twitter_url = Column(String(255))
    facebook_url = Column(String(255))
    setup_completed = Column(Integer, default=0)
    created_by = Column(Integer, ForeignKey("hr_admins.id"))
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class Department(Base):
    __tablename__ = "departments"
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    manager_name = Column(String(255))
    color = Column(String(7), default='#e74c3c')
    budget = Column(Numeric(15, 2))
    is_active = Column(Integer, default=1)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    company = relationship("Company")

class Employee(Base):
    __tablename__ = "employees"
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"))
    employee_id = Column(String(50))
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    phone = Column(String(20))
    address = Column(Text)
    date_of_birth = Column(Date)
    position = Column(String(100), nullable=False)
    hire_date = Column(Date)
    salary = Column(Numeric(10, 2))
    employment_type = Column(Enum('CDI', 'CDD', 'Stage', 'Freelance', 'Consultant', name='employment_type_enum'), default='CDI')
    status = Column(Enum('active', 'inactive', 'terminated', 'on_leave', name='employee_status_enum'), default='active')
    skills = Column(JSON)
    performance_rating = Column(Numeric(3, 2))
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    company = relationship("Company")
    department = relationship("Department")

class Job(Base):
    __tablename__ = "jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    requirements = Column(Text)
    responsibilities = Column(Text)
    employment_type = Column(Enum('CDI', 'CDD', 'Stage', 'Freelance', name='job_employment_type'), nullable=False)
    salary_min = Column(Numeric(10, 2))
    salary_max = Column(Numeric(10, 2))
    currency = Column(String(3), default='EUR')
    priority = Column(Enum('low', 'normal', 'urgent', name='job_priority'), default='normal')
    status = Column(Enum('draft', 'active', 'paused', 'closed', 'filled', name='job_status'), default='draft')
    assigned_employee_id = Column(Integer, ForeignKey("employees.id"))
    deadline = Column(Date)
    start_date = Column(Date)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    views_count = Column(Integer, default=0)
    applications_count = Column(Integer, default=0)
    
    # Relationships
    company = relationship("Company")
    department = relationship("Department")
    assigned_employee = relationship("Employee")

class JobSkill(Base):
    __tablename__ = "job_skills"
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)
    skill_name = Column(String(100), nullable=False)
    skill_level = Column(Enum('beginner', 'intermediate', 'advanced', 'expert', name='skill_level'), default='intermediate')
    is_required = Column(Integer, default=1)
    
    job = relationship("Job")

class Application(Base):
    __tablename__ = "applications"
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)
    candidate_profile_id = Column(Integer, ForeignKey("profile_candidat.id"), nullable=False)
    application_date = Column(DateTime, default=datetime.utcnow)
    status = Column(Enum('pending', 'reviewed', 'interview_scheduled', 'interview_completed', 'accepted', 'rejected', 'withdrawn'), default='pending')
    hr_rating = Column(Numeric(3, 2))
    hr_notes = Column(Text)
    interview_date = Column(DateTime)
    interview_notes = Column(Text)
    reviewed_by = Column(Integer, ForeignKey("hr_admins.id"))
    reviewed_at = Column(DateTime)
    decision_date = Column(DateTime)
    decision_reason = Column(Text)
    source = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), nullable=False, unique=True)
    password_hash = Column(String(255))
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    google_id = Column(String(255), unique=True)
    profile_picture = Column(String(500))
    is_active = Column(Integer, default=1)
    is_verified = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# Session model for remember me functionality
class UserSession(Base):
    __tablename__ = "user_sessions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    session_token = Column(String(255), nullable=False, unique=True)
    expires_at = Column(DateTime, nullable=False)
    is_remember_me = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User")

# Helper functions for job operations
def get_jobs_with_pagination(page=1, per_page=9, search_query=None, location=None, category=None, employment_type=None, salary_min=None, salary_max=None):
    """Get jobs with pagination and filters"""
    from database import SessionLocal
    from sqlalchemy import and_, or_, desc
    import math
    
    db = SessionLocal()
    try:
        # Base query with joins to get company information
        query = db.query(Job).join(Company).join(Department).filter(Job.status == 'active')
        
        # Apply filters
        if search_query:
            search_filter = or_(
                Job.title.ilike(f"%{search_query}%"),
                Job.description.ilike(f"%{search_query}%"),
                Job.requirements.ilike(f"%{search_query}%"),
                Company.company_name.ilike(f"%{search_query}%")
            )
            query = query.filter(search_filter)
        
        if location:
            query = query.filter(Company.address.ilike(f"%{location}%"))
        
        if category:
            query = query.filter(
                or_(
                    Job.description.ilike(f"%{category}%"),
                    Department.name.ilike(f"%{category}%")
                )
            )
        
        if employment_type:
            query = query.filter(Job.employment_type == employment_type)
        
        if salary_min:
            query = query.filter(Job.salary_min >= salary_min)
        
        if salary_max:
            query = query.filter(Job.salary_max <= salary_max)
        
        # Order by created_at desc (newest first)
        query = query.order_by(desc(Job.created_at))
        
        # Get total count
        total_jobs = query.count()
        
        # Calculate pagination
        total_pages = math.ceil(total_jobs / per_page)
        offset = (page - 1) * per_page
        
        # Get jobs for current page
        jobs = query.offset(offset).limit(per_page).all()
        
        # Convert to dict format for template
        jobs_data = []
        for job in jobs:
            # Get job skills
            job_skills = db.query(JobSkill).filter(JobSkill.job_id == job.id).all()
            skills_list = [skill.skill_name for skill in job_skills]
            
            job_dict = {
                'id': job.id,
                'title': job.title,
                'company_name': job.company.company_name if job.company else 'Entreprise Confidentielle',
                'company_logo': job.company.logo_url if job.company and job.company.logo_url else '🏢',
                'location': job.company.address if job.company and job.company.address else 'Non spécifié',
                'employment_type': job.employment_type,
                'salary_min': float(job.salary_min) if job.salary_min else None,
                'salary_max': float(job.salary_max) if job.salary_max else None,
                'currency': job.currency or 'EUR',
                'description': job.description,
                'requirements': job.requirements,
                'responsibilities': job.responsibilities,
                'tags': skills_list,
                'created_at': job.created_at,
                'views_count': job.views_count or 0,
                'applications_count': job.applications_count or 0,
                'department_name': job.department.name if job.department else 'Non spécifié',
                'priority': job.priority,
                'deadline': job.deadline,
                'start_date': job.start_date
            }
            jobs_data.append(job_dict)
        
        return {
            'jobs': jobs_data,
            'pagination': {
                'current_page': page,
                'total_pages': total_pages,
                'total_jobs': total_jobs,
                'per_page': per_page,
                'has_prev': page > 1,
                'has_next': page < total_pages,
                'prev_page': page - 1 if page > 1 else None,
                'next_page': page + 1 if page < total_pages else None
            }
        }
        
    except Exception as e:
        print(f"Error fetching jobs: {e}")
        return {
            'jobs': [],
            'pagination': {
                'current_page': 1,
                'total_pages': 0,
                'total_jobs': 0,
                'per_page': per_page,
                'has_prev': False,
                'has_next': False,
                'prev_page': None,
                'next_page': None
            }
        }
    finally:
        db.close()

def get_job_by_id(job_id):
    """Get a single job by ID"""
    from database import SessionLocal
    
    db = SessionLocal()
    try:
        job = db.query(Job).join(Company).join(Department).filter(Job.id == job_id).first()
        if job:
            # Increment view count
            job.views_count = (job.views_count or 0) + 1
            db.commit()
            
            # Get job skills
            job_skills = db.query(JobSkill).filter(JobSkill.job_id == job.id).all()
            skills_list = [{'name': skill.skill_name, 'level': skill.skill_level, 'required': bool(skill.is_required)} for skill in job_skills]
            
            return {
                'id': job.id,
                'title': job.title,
                'company_name': job.company.company_name if job.company else 'Entreprise Confidentielle',
                'company_logo': job.company.logo_url if job.company and job.company.logo_url else '🏢',
                'location': job.company.address if job.company and job.company.address else 'Non spécifié',
                'employment_type': job.employment_type,
                'salary_min': float(job.salary_min) if job.salary_min else None,
                'salary_max': float(job.salary_max) if job.salary_max else None,
                'currency': job.currency or 'EUR',
                'description': job.description,
                'requirements': job.requirements,
                'responsibilities': job.responsibilities,
                'skills': skills_list,
                'created_at': job.created_at,
                'views_count': job.views_count,
                'applications_count': job.applications_count,
                'deadline': job.deadline,
                'start_date': job.start_date,
                'department_name': job.department.name if job.department else 'Non spécifié',
                'priority': job.priority,
                'company_info': {
                    'name': job.company.company_name,
                    'industry': job.company.industry,
                    'size': job.company.company_size,
                    'website': job.company.website,
                    'description': job.company.description
                } if job.company else None
            }
        return None
    except Exception as e:
        print(f"Error fetching job {job_id}: {e}")
        return None
    finally:
        db.close()

