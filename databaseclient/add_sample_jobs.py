from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
import sys
import os

# Add the parent directory to the path to import models
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from databaseclient.models import Job, Company, Department, JobSkill
from database import DATABASE_URL
from datetime import datetime, date

# Create engine and session
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def add_sample_jobs():
    db = SessionLocal()
    try:

        # Get existing companies
        companies = db.query(Company).all()
        if not companies:
            print("No companies found. Please create companies first.")
            return

        # Create sample departments if they don't exist
        for company in companies:
            existing_depts = db.query(Department).filter(Department.company_id == company.id).count()
            if existing_depts == 0:
                # Create sample departments
                departments_data = [
                    {"name": "Développement", "description": "Équipe de développement logiciel", "color": "#3b82f6"},
                    {"name": "Data & Analytics", "description": "Équipe d'analyse de données", "color": "#10b981"},
                    {"name": "Design", "description": "Équipe de design et UX", "color": "#f59e0b"},
                    {"name": "Marketing", "description": "Équipe marketing et communication", "color": "#ef4444"},
                    {"name": "Ressources Humaines", "description": "Équipe RH", "color": "#8b5cf6"}
                ]
                
                for dept_data in departments_data:
                    department = Department(
                        company_id=company.id,
                        name=dept_data["name"],
                        description=dept_data["description"],
                        color=dept_data["color"],
                        is_active=1
                    )
                    db.add(department)
                
                db.commit()
                print(f"Created departments for company: {company.company_name}")

        # Get departments for job creation
        departments = db.query(Department).all()
        if not departments:
            print("No departments found. Cannot create jobs.")
            return

        # Sample job data
        sample_jobs = [
            {
                "title": "Développeur Full Stack Python/React",
                "description": "Nous recherchons un développeur full stack expérimenté pour rejoindre notre équipe dynamique. Vous travaillerez sur des projets innovants utilisant Python/Django pour le backend et React pour le frontend.",
                "requirements": "• 3+ années d'expérience en développement web\n• Maîtrise de Python et Django\n• Expérience avec React et JavaScript moderne\n• Connaissance des bases de données relationnelles\n• Expérience avec Git et les méthodologies Agile",
                "responsibilities": "• Développer et maintenir des applications web\n• Collaborer avec l'équipe de design pour implémenter les interfaces\n• Optimiser les performances des applications\n• Participer aux code reviews\n• Mentorer les développeurs juniors",
                "employment_type": "CDI",
                "salary_min": 45000,
                "salary_max": 65000,
                "department_name": "Développement"
            },
            {
                "title": "Data Scientist Senior",
                "description": "Rejoignez notre équipe data pour analyser de grandes quantités de données et développer des modèles prédictifs qui impactent directement nos décisions business.",
                "requirements": "• Master en Data Science, Statistiques ou domaine similaire\n• 4+ années d'expérience en analyse de données\n• Maîtrise de Python (pandas, scikit-learn, TensorFlow)\n• Expérience avec SQL et bases de données\n• Connaissance des outils de visualisation (Tableau, Power BI)",
                "responsibilities": "• Analyser des datasets complexes\n• Développer des modèles de machine learning\n• Créer des dashboards et rapports\n• Présenter les insights aux équipes métier\n• Optimiser les algorithmes existants",
                "employment_type": "CDI",
                "salary_min": 55000,
                "salary_max": 75000,
                "department_name": "Data & Analytics"
            },
            {
                "title": "Designer UX/UI",
                "description": "Nous cherchons un designer créatif pour concevoir des expériences utilisateur exceptionnelles et des interfaces intuitives pour nos produits digitaux.",
                "requirements": "• 3+ années d'expérience en design UX/UI\n• Maîtrise de Figma, Sketch ou Adobe XD\n• Portfolio démontrant des projets web et mobile\n• Connaissance des principes d'accessibilité\n• Expérience en recherche utilisateur",
                "responsibilities": "• Concevoir des wireframes et prototypes\n• Réaliser des tests utilisateurs\n• Créer des design systems cohérents\n• Collaborer avec les équipes de développement\n• Analyser les métriques d'usage",
                "employment_type": "CDI",
                "salary_min": 40000,
                "salary_max": 55000,
                "department_name": "Design"
            },
            {
                "title": "Responsable Marketing Digital",
                "description": "Pilotez notre stratégie marketing digital et développez notre présence en ligne pour accroître notre visibilité et générer des leads qualifiés.",
                "requirements": "• 5+ années d'expér ience en marketing digital\n• Maîtrise des outils Google Ads, Facebook Ads\n• Expérience en SEO/SEA et analytics\n• Connaissance des outils d'automation marketing\n• Excellentes compétences rédactionnelles",
                "responsibilities": "• Développer la stratégie marketing digital\n• Gérer les campagnes publicitaires en ligne\n• Analyser les performances et ROI\n• Créer du contenu engageant\n• Manager l'équipe marketing junior",
                "employment_type": "CDI",
                "salary_min": 50000,
                "salary_max": 70000,
                "department_name": "Marketing"
            },
            {
                "title": "Stage - Développeur Frontend React",
                "description": "Opportunité de stage de 6 mois pour découvrir le développement frontend dans une équipe expérimentée. Formation et mentorat assurés.",
                "requirements": "• Étudiant en informatique (Bac+3/4/5)\n• Bases en HTML, CSS, JavaScript\n• Première expérience avec React souhaitée\n• Motivation et envie d'apprendre\n• Disponibilité 6 mois minimum",
                "responsibilities": "• Développer des composants React\n• Intégrer des maquettes design\n• Participer aux daily meetings\n• Apprendre les bonnes pratiques\n• Contribuer aux projets de l'équipe",
                "employment_type": "Stage",
                "salary_min": 800,
                "salary_max": 1200,
                "department_name": "Développement"
            },
            {
                "title": "Consultant Freelance - Expert DevOps",
                "description": "Mission freelance de 6 mois pour accompagner notre transformation DevOps et mettre en place une infrastructure cloud moderne.",
                "requirements": "• 5+ années d'expérience DevOps\n• Expertise AWS/Azure/GCP\n• Maîtrise Docker, Kubernetes\n• Expérience CI/CD (Jenkins, GitLab CI)\n• Connaissance Terraform, Ansible",
                "responsibilities": "• Concevoir l'architecture cloud\n• Mettre en place les pipelines CI/CD\n• Former les équipes internes\n• Optimiser les coûts infrastructure\n• Assurer la sécurité des déploiements",
                "employment_type": "Freelance",
                "salary_min": 600,
                "salary_max": 800,
                "department_name": "Développement"
            },
            {
                "title": "Analyste Business Intelligence",
                "description": "Transformez nos données en insights actionnables pour guider les décisions stratégiques de l'entreprise.",
                "requirements": "• 3+ années d'expérience en BI\n• Maîtrise SQL avancé\n• Expérience Power BI ou Tableau\n• Connaissance des entrepôts de données\n• Compétences en analyse statistique",
                "responsibilities": "• Créer des tableaux de bord\n• Analyser les KPIs business\n• Automatiser les rapports\n• Former les utilisateurs finaux\n• Optimiser les requêtes de données",
                "employment_type": "CDI",
                "salary_min": 42000,
                "salary_max": 58000,
                "department_name": "Data & Analytics"
            },
            {
                "title": "Chargé de Recrutement IT",
                "description": "Rejoignez notre équipe RH pour recruter les meilleurs talents tech et contribuer à la croissance de nos équipes techniques.",
                "requirements": "• 2+ années d'expérience en recrutement IT\n• Connaissance de l'écosystème tech\n• Maîtrise des outils de sourcing\n• Excellentes compétences relationnelles\n• Anglais courant",
                "responsibilities": "• Sourcer et qualifier les candidats\n• Mener les entretiens de pré-sélection\n• Gérer les processus de recrutement\n• Développer la marque employeur\n• Analyser les métriques de recrutement",
                "employment_type": "CDI",
                "salary_min": 35000,
                "salary_max": 45000,
                "department_name": "Ressources Humaines"
            }
        ]

        # Create jobs
        created_jobs = 0
        for job_data in sample_jobs:
            # Find a department that matches
            department = None
            for dept in departments:
                if dept.name == job_data["department_name"]:
                    department = dept
                    break
            
            if not department:
                # Use first available department
                department = departments[0]

            # Create job
            job = Job(
                company_id=department.company_id,
                department_id=department.id,
                title=job_data["title"],
                description=job_data["description"],
                requirements=job_data["requirements"],
                responsibilities=job_data["responsibilities"],
                employment_type=job_data["employment_type"],
                salary_min=job_data["salary_min"],
                salary_max=job_data["salary_max"],
                currency="EUR",
                priority="normal",
                status="active",
                deadline=date(2025, 12, 31),
                views_count=0,
                applications_count=0
            )
            
            db.add(job)
            db.flush()  # Get the job ID
            
            # Add some sample skills for each job
            skills_by_job_type = {
                "Développeur": ["Python", "React", "Django", "JavaScript", "Git"],
                "Data": ["Python", "SQL", "Machine Learning", "Tableau", "Statistics"],
                "Designer": ["Figma", "UX Design", "Prototyping", "User Research", "Adobe Creative"],
                "Marketing": ["Google Ads", "SEO", "Analytics", "Content Marketing", "Social Media"],
                "Stage": ["HTML", "CSS", "JavaScript", "React", "Git"],
                "Consultant": ["AWS", "Docker", "Kubernetes", "CI/CD", "Terraform"],
                "Analyste": ["SQL", "Power BI", "Data Analysis", "Excel", "Statistics"],
                "Chargé": ["Recruitment", "HR", "Sourcing", "Interview", "Talent Acquisition"]
            }
            
            # Find matching skills
            job_skills = []
            for job_type, skills in skills_by_job_type.items():
                if job_type.lower() in job_data["title"].lower():
                    job_skills = skills[:4]  # Take first 4 skills
                    break
            
            if not job_skills:
                job_skills = ["Communication", "Teamwork", "Problem Solving"]
            
            # Add skills to job
            for skill_name in job_skills:
                skill = JobSkill(
                    job_id=job.id,
                    skill_name=skill_name,
                    skill_level="intermediate",
                    is_required=1
                )
                db.add(skill)
            
            created_jobs += 1

        db.commit()
        print(f"Successfully created {created_jobs} sample jobs with skills!")
        
        # Print summary
        total_jobs = db.query(Job).count()
        total_companies = db.query(Company).count()
        total_departments = db.query(Department).count()
        
        print(f"\nDatabase Summary:")
        print(f"- Companies: {total_companies}")
        print(f"- Departments: {total_departments}")
        print(f"- Jobs: {total_jobs}")
        print(f"- Job Skills: {db.query(JobSkill).count()}")

    except Exception as e:
        print(f"Error creating sample jobs: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    add_sample_jobs()
