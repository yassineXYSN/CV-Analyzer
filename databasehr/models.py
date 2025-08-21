from sqlalchemy import Column, Integer, String, ForeignKey, JSON, Text, DECIMAL, Boolean, DateTime, Date, Enum,TIMESTAMP
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from databasehr.database import Base

# Modèles existants (Contact, AnalyseCandidat, ProfileCandidat)
class Contact(Base):
    __tablename__ = "contact"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255))
    phone = Column(String(50))
    linkedin = Column(String(255))
    address = Column(Text)

class AnalyseCandidat(Base):
    __tablename__ = "analyse_candidat"
    id = Column(Integer, primary_key=True, index=True)
    analyse = Column(Text)

class ProfileCandidat(Base):
    __tablename__ = "profile_candidat"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255))
    title = Column(String(255))
    profile = Column(Text)
    contact_id = Column(Integer, ForeignKey("contact.id"))
    analyse_id = Column(Integer, ForeignKey("analyse_candidat.id"))
    education = Column(JSON)
    languages = Column(JSON)
    certificates = Column(JSON)
    skills = Column(JSON)

    contact = relationship("Contact")
    analyse = relationship("AnalyseCandidat")

# NOUVEAUX MODÈLES HR
class HRAdmin(Base):
    __tablename__ = "hr_admins"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    role = Column(Enum('super_admin', 'recruiter', 'department_head'), default='recruiter')
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)  # Nouveau champ
    last_login = Column(DateTime)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class Company(Base):
    __tablename__ = "companies"
    
    id = Column(Integer, primary_key=True, index=True)
    company_name = Column(String(255), nullable=False)
    industry = Column(String(100))
    company_size = Column(Enum('1-10', '11-50', '51-200', '201-1000', '1000+'))
    founded_year = Column(DateTime)
    description = Column(Text)
    logo_url = Column(String(500))
    
    # Coordonnées
    address = Column(Text)
    phone = Column(String(20))
    email = Column(String(255))
    website = Column(String(255))
    
    # Réseaux sociaux
    linkedin_url = Column(String(255))
    twitter_url = Column(String(255))
    facebook_url = Column(String(255))
    
    # Métadonnées
    setup_completed = Column(Integer, default=0)
    created_by = Column(Integer, ForeignKey("hr_admins.id"))
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class AdminCompanyAccess(Base):
    __tablename__ = "admin_company_access"
    
    id = Column(Integer, primary_key=True, index=True)
    admin_id = Column(Integer, ForeignKey("hr_admins.id"), nullable=False)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    access_level = Column(Enum('owner', 'admin', 'viewer'), default='admin')
    granted_at = Column(DateTime, default=func.now())
    granted_by = Column(Integer, ForeignKey("hr_admins.id"))
    


class Department(Base):
    __tablename__ = "departments"
    
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    manager_id = Column(Integer)
    color = Column(String(7), default='#e74c3c')
    budget = Column(DECIMAL(15,2))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class Employee(Base):
    __tablename__ = "employees"
    
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"))
    employee_id = Column(String(50))
    
    # Informations personnelles
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    phone = Column(String(20))
    address = Column(Text)
    date_of_birth = Column(Date)
    
    # Informations professionnelles
    position = Column(String(100), nullable=False)
    hire_date = Column(Date)
    salary = Column(DECIMAL(10,2))
    employment_type = Column(Enum('CDI', 'CDD', 'Stage', 'Freelance', 'Consultant'), default='CDI')
    status = Column(Enum('active', 'inactive', 'terminated', 'on_leave'), default='active')
    
    # Compétences et performance
    skills = Column(JSON)
    performance_rating = Column(DECIMAL(3,2))
    
    # Métadonnées
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    candidate_profile_id = Column(Integer, ForeignKey("profile_candidat.id"))
    profile = relationship("ProfileCandidat")

class Job(Base):
    __tablename__ = "jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)
    
    # Informations du poste
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    requirements = Column(Text)
    responsibilities = Column(Text)
    
    # Détails contractuels
    employment_type = Column(Enum('CDI', 'CDD', 'Stage', 'Freelance'), nullable=False)
    salary_min = Column(DECIMAL(10,2))
    salary_max = Column(DECIMAL(10,2))
    currency = Column(String(3), default='EUR')
    
    # Gestion du poste
    priority = Column(Enum('low', 'normal', 'urgent'), default='normal')
    status = Column(Enum('draft', 'active', 'paused', 'closed', 'filled'), default='draft')
    assigned_employee_id = Column(Integer, ForeignKey("employees.id"))
    
    # Dates importantes
    deadline = Column(Date)
    start_date = Column(Date)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Statistiques
    applications_count = Column(Integer, default=0)
    
    # Relationships
    department = relationship("Department")

class JobSkill(Base):
    __tablename__ = "job_skills"
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)
    skill_name = Column(String(100), nullable=False)
    skill_level = Column(Enum('beginner', 'intermediate', 'advanced', 'expert'), default='intermediate')
    is_required = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    
    # Relationship
    job = relationship("Job", backref="job_skills")

class Application(Base):
    __tablename__ = "applications"
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)
    candidate_profile_id = Column(Integer, ForeignKey("profile_candidat.id"), nullable=False)
    
    # Informations de candidature
    application_date = Column(DateTime, default=func.now())
    status = Column(Enum('pending', 'reviewed', 'interview_scheduled', 'interview_completed', 'accepted', 'rejected', 'withdrawn'), default='pending')
    
    # Évaluation
    hr_rating = Column(DECIMAL(3,2))
    hr_notes = Column(Text)
    interview_date = Column(DateTime)
    interview_notes = Column(Text)
    
    # Suivi
    reviewed_by = Column(Integer, ForeignKey("hr_admins.id"))
    reviewed_at = Column(DateTime)
    decision_date = Column(DateTime)
    decision_reason = Column(Text)
    
    # NOUVEAUX CHAMPS DE RECOMMANDATION
    is_recommended = Column(Boolean, default=False)
    recommended_by_admin_id = Column(Integer, ForeignKey("hr_admins.id"))
    recommendation_comment = Column(Text)
    recommendation_priority = Column(Enum('normal', 'high', 'urgent'), default='normal')
    recommendation_date = Column(DateTime)
    
    # Métadonnées
    source = Column(String(100))
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relations
    job = relationship("Job")
    candidate_profile = relationship("ProfileCandidat")
    reviewed_by_admin = relationship("HRAdmin", foreign_keys=[reviewed_by])
    recommended_by_admin = relationship("HRAdmin", foreign_keys=[recommended_by_admin_id])

    # Relationships
    job = relationship("Job")
    candidate_profile = relationship("ProfileCandidat")

# NOUVEAU MODÈLE POUR L'ACTIVITÉ RÉCENTE
class ActivityLog(Base):
    __tablename__ = "activity_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    admin_id = Column(Integer, ForeignKey("hr_admins.id"), nullable=False)
    
    # Type d'action et entité concernée
    action_type = Column(Enum('create', 'update', 'delete', 'login', 'logout'), nullable=False)
    entity_type = Column(Enum('department', 'employee', 'job', 'user', 'company', 'application'), nullable=False)
    entity_id = Column(Integer)  # ID de l'entité concernée
    
    # Description de l'activité
    description = Column(Text, nullable=False)
    details = Column(JSON)  # Détails supplémentaires en JSON
    
    # Métadonnées
    ip_address = Column(String(45))  # Pour IPv4 et IPv6
    user_agent = Column(Text)
    created_at = Column(DateTime, default=func.now())
    
    # Relations
    company = relationship("Company")
    admin = relationship("HRAdmin")

class AdminPermissions(Base):
    __tablename__ = "admin_permissions"
    
    id = Column(Integer, primary_key=True, index=True)
    admin_id = Column(Integer, ForeignKey("hr_admins.id"), nullable=False)
    can_add_department = Column(Boolean, default=False)
    can_manage_applications = Column(Boolean, default=False)
    can_recommend_candidates = Column(Boolean, default=False)
    # Relations
    admin = relationship("HRAdmin")
    
class AdminDepartments(Base):
    __tablename__ = "admin_departments"

    id = Column(Integer, primary_key=True, index=True)
    admin_id = Column(Integer, ForeignKey("hr_admins.id"), nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)
    # Relations
    admin = relationship("HRAdmin")
    department = relationship("Department")
