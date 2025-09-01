from sqlalchemy import Column, Integer, String, ForeignKey, JSON, Text, DECIMAL, Boolean, DateTime, Date, Enum, Numeric
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

    user = relationship("User", back_populates="profile", uselist=False)


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
    
    verification_token = Column(String(255), nullable=True)
    token_expires = Column(DateTime, nullable=True)

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
    status = Column(Enum('pending', 'reviewed', 'interview_scheduled', 'interview_completed', 'accepted', 'rejected', 'withdrawn','accepted_pending_validation'), default='pending')
    
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
    
    # NOUVEAUX CHAMPS DE VALIDATION DES COMPÉTENCES
    skills_validated = Column(Boolean, default=False)
    skills_validated_by = Column(Integer, ForeignKey("hr_admins.id"))
    skills_validated_at = Column(DateTime)
    skills_validated_notes = Column(Text)
    
    # Métadonnées
    source = Column(String(100))
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relations
    job = relationship("Job")
    candidate_profile = relationship("ProfileCandidat")
    reviewed_by_admin = relationship("HRAdmin", foreign_keys=[reviewed_by])
    recommended_by_admin = relationship("HRAdmin", foreign_keys=[recommended_by_admin_id])
    skills_validated_by_admin = relationship("HRAdmin", foreign_keys=[skills_validated_by])

    # Relationships
    job = relationship("Job")
    candidate_profile = relationship("ProfileCandidat")
    
    compatibility_score = Column(Numeric(5, 2), comment="Compatibility score between candidate and job (0-100)")
    compatibility_reason = Column(Text, comment="Detailed reason for compatibility score from AI analysis")
    n8n_webhook_triggered = Column(Boolean, default=False, comment="Flag to track if n8n webhook was triggered")

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

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), nullable=False, unique=True)
    password_hash = Column(String(255))
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    google_id = Column(String(255), unique=True)
    profile_picture = Column(String(500))
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    profile_id = Column(Integer, ForeignKey("profile_candidat.id"))
    verification_token = Column(String(255))
    verification_token_expires = Column(DateTime)
    
    # Relations
    profile = relationship("ProfileCandidat", back_populates="user")
    

class Notification(Base):
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    type = Column(String(50), nullable=False)
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    application_id = Column(Integer, ForeignKey("applications.id"), nullable=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=True)
    status = Column(String(50), nullable=True)
    company_name = Column(String(200), nullable=True)
    job_title = Column(String(200), nullable=True)
    admin_name = Column(String(100), nullable=True)
    
    # Relations
    user = relationship("User")
    application = relationship("Application")
    job = relationship("Job")

class Quiz(Base):
    __tablename__ = "quizzes"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    time_limit	 = Column(Integer, nullable=False)
    total_questions = Column(Integer, default=0)
    
    # Relations
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=True)
    candidate_id = Column(Integer, ForeignKey("profile_candidat.id"), nullable=True)
    created_by_admin_id = Column(Integer, ForeignKey("hr_admins.id"), nullable=False)
    
    # Status and metadata
    status = Column(Enum('draft', 'active', 'completed', 'archived'), default='draft')
    n8n_webhook_url = Column(String(500))
    n8n_response = Column(JSON)
    n8n_webhook_triggered = Column(Boolean, default=False)
    webhook_error = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    job = relationship("Job")
    candidate = relationship("ProfileCandidat")
    created_by = relationship("HRAdmin")

class QuizSkill(Base):
    __tablename__ = "quiz_skills"
    
    id = Column(Integer, primary_key=True, index=True)
    quiz_id = Column(Integer, ForeignKey("quizzes.id"), nullable=False)
    skill_name = Column(String(100), nullable=False)
    questions_count = Column(Integer, nullable=False)
    difficulty = Column(Enum('easy', 'medium', 'hard', 'expert'), nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    quiz = relationship("Quiz", backref="skills")

class QuizQuestion(Base):
    __tablename__ = "quiz_questions"
    
    id = Column(Integer, primary_key=True, index=True)
    quiz_id = Column(Integer, ForeignKey("quizzes.id"), nullable=False)
    skill = Column(String(100), nullable=False)
    question_text = Column(Text, nullable=False)
    
    # Question options and answers
    options = Column(JSON)  # For multiple choice questions
    correct_answer = Column(Text, nullable=False)
    explanation = Column(Text)
    
    # Order and metadata
    question_order = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    quiz = relationship("Quiz", backref="questions")

class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"
    
    id = Column(Integer, primary_key=True, index=True)
    quiz_id = Column(Integer, ForeignKey("quizzes.id"), nullable=False)
    candidate_id = Column(Integer, ForeignKey("profile_candidat.id"), nullable=False)
    
    # Attempt details
    started_at = Column(DateTime, default=func.now())
    completed_at = Column(DateTime)
    time_taken_seconds = Column(Integer)
    status = Column(Enum('in_progress', 'completed', 'abandoned', 'expired'), default='in_progress')
    
    # Scoring
    total_score = Column(DECIMAL(5,2), default=0.00)
    max_possible_score = Column(DECIMAL(5,2), default=0.00)
    percentage_score = Column(DECIMAL(5,2), default=0.00)
    
    # Metadata
    ip_address = Column(String(45))
    user_agent = Column(Text)
    browser_info = Column(JSON)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    quiz = relationship("Quiz")
    candidate = relationship("ProfileCandidat")

class QuizAnswer(Base):
    __tablename__ = "quiz_answers"
    
    id = Column(Integer, primary_key=True, index=True)
    attempt_id = Column(Integer, ForeignKey("quiz_attempts.id"), nullable=False)
    question_id = Column(Integer, ForeignKey("quiz_questions.id"), nullable=False)
    
    # Answer details
    answer_text = Column(Text)
    selected_options = Column(JSON)  # For multiple choice
    is_correct = Column(Boolean, default=False)
    points_earned = Column(DECIMAL(5,2), default=0.00)
    
    # Timing
    time_taken_seconds = Column(Integer)
    answered_at = Column(DateTime, default=func.now())
    
    # Relationships
    attempt = relationship("QuizAttempt", backref="answers")
    question = relationship("QuizQuestion")
