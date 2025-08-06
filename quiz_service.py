from typing import List, Dict, Any, Optional, cast
from database import SessionLocal
from models import QuizAttempt
from databaseclient.models import ProfileCandidat
from quiz_generator import QuizGenerator
import json
import datetime

class QuizService:
    def __init__(self):
        self.generator = QuizGenerator()
    
    def generate_quiz_for_candidate(self, candidate_id: int, job_title: str, num_questions: int = 10) -> Optional[List[Dict[str, Any]]]:
        """
        Generate a list of quizzes for a specific candidate, one per skill.
        Each quiz is stored as a separate QuizAttempt and returned as a list.
        """
        db = SessionLocal()
        try:
            # Get candidate profile
            candidate = db.query(ProfileCandidat).filter(ProfileCandidat.id == candidate_id).first()
            if not candidate:
                raise ValueError("Candidate not found")
            
            # Extract skills from candidate profile
            candidate_skills = []
            skills_data = candidate.skills
            if isinstance(skills_data, str):
                try:
                    skills_data = json.loads(skills_data)
                except Exception:
                    skills_data = []
            if skills_data is not None:
                for skill in skills_data:
                    if isinstance(skill, str) and ':' in skill:
                        skill_name = skill.split(':')[0].strip()
                        candidate_skills.append(skill_name)
                    elif isinstance(skill, str):
                        candidate_skills.append(skill.strip())
            
            # Get past questions from previous quiz attempts for this candidate
            past_questions = self._get_past_questions_for_candidate(candidate_id, db)
            
            quizzes = []
            if not candidate_skills:
                # Fallback: one quiz for job title
                required_skills = self._get_required_skills_for_job(job_title)
                quiz_data = self.generator.generate_quiz(
                    job_title=job_title,
                    required_skills=required_skills,
                    candidate_skills=[],
                    num_questions=num_questions,
                    past_questions=past_questions,
                    use_expert_prompt=True
                )
                if not quiz_data or not quiz_data.get("questions"):
                    # Do not add fallback quiz
                    # raise error below if no quizzes
                    pass
                else:
                    quiz_attempt = QuizAttempt(
                        candidate_id=candidate_id,
                        job_title=job_title,
                        difficulty=None,
                        questions=quiz_data["questions"],
                        answers=None,
                        total_score=None,
                        category_scores=None,
                        detailed_results=None
                    )
                    db.add(quiz_attempt)
                    db.commit()
                    db.refresh(quiz_attempt)
                    quiz_data["quiz_id"] = quiz_attempt.id
                    quizzes.append(quiz_data)
            else:
                # One quiz per skill
                for skill in candidate_skills:
                    # Get past questions for this specific skill
                    skill_past_questions = [q for q in past_questions if skill.lower() in q.lower()]
                    
                    quiz = self.generator.generate_quiz(
                        job_title=job_title,
                        required_skills=[],
                        candidate_skills=[skill],
                        num_questions=5,
                        past_questions=skill_past_questions,
                        use_expert_prompt=True
                    )
                    
                    # Always include the quiz, even if it has no questions
                    if not quiz:
                        continue
                    
                    num_questions = len(quiz.get("questions", []))
                    if num_questions == 0:
                        # Add a warning message to the quiz
                        if "warning" not in quiz:
                            quiz["warning"] = f"Aucune question valide générée pour la compétence: {skill}"
                    
                    quiz_attempt = QuizAttempt(
                        candidate_id=candidate_id,
                        job_title=f"{job_title} - {skill}",
                        difficulty=None,
                        questions=quiz["questions"],
                        answers=None,
                        total_score=None,
                        category_scores=None,
                        detailed_results=None
                    )
                    db.add(quiz_attempt)
                    db.commit()
                    db.refresh(quiz_attempt)
                    quiz["quiz_id"] = quiz_attempt.id
                    quiz["skill"] = skill
                    quizzes.append(quiz)
            if not quizzes:
                raise RuntimeError("La génération du QCM a échoué. Veuillez réessayer.")
            return quizzes
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()
    
    def _get_past_questions_for_candidate(self, candidate_id: int, db) -> List[str]:
        """
        Get past questions from previous quiz attempts for this candidate
        """
        past_questions = []
        try:
            # Get all previous quiz attempts for this candidate
            attempts = db.query(QuizAttempt).filter(
                QuizAttempt.candidate_id == candidate_id
            ).all()
            
            for attempt in attempts:
                questions = attempt.questions
                if isinstance(questions, str):
                    try:
                        questions = json.loads(questions)
                    except Exception:
                        continue
                
                if isinstance(questions, list):
                    for question in questions:
                        if isinstance(question, dict) and 'question' in question:
                            past_questions.append(question['question'])
        except Exception:
            pass
        
        return past_questions
    
    def _get_required_skills_for_job(self, job_title: str) -> List[str]:
        """
        Get required skills based on job title
        This is a simplified mapping - you can expand this based on your needs
        """
        job_skills_mapping = {
            "développeur": ["Python", "JavaScript", "SQL", "Git", "API"],
            "data scientist": ["Python", "R", "SQL", "Machine Learning", "Statistics"],
            "data engineer": ["Python", "SQL", "Big Data", "ETL", "Cloud"],
            "devops": ["Linux", "Docker", "Kubernetes", "CI/CD", "Cloud"],
            "frontend": ["JavaScript", "React", "HTML", "CSS", "TypeScript"],
            "backend": ["Python", "Java", "SQL", "API", "Microservices"],
            "fullstack": ["JavaScript", "Python", "React", "Node.js", "SQL"],
            "mobile": ["React Native", "Flutter", "iOS", "Android", "API"],
            "ui/ux": ["Figma", "Adobe XD", "Prototyping", "User Research", "Design Systems"],
            "project manager": ["Agile", "Scrum", "Leadership", "Communication", "Risk Management"],
            "business analyst": ["Requirements Analysis", "SQL", "Excel", "Process Modeling", "Stakeholder Management"],
            "qa engineer": ["Testing", "Selenium", "JUnit", "Test Planning", "Bug Tracking"],
            "system administrator": ["Linux", "Windows Server", "Networking", "Security", "Backup"],
            "network engineer": ["Cisco", "Routing", "Switching", "Network Security", "Protocols"],
            "security engineer": ["Cybersecurity", "Penetration Testing", "SIEM", "Compliance", "Incident Response"]
        }
        
        # Find matching skills based on job title
        job_title_lower = job_title.lower()
        for key, skills in job_skills_mapping.items():
            if key in job_title_lower:
                return skills
        
        # Default skills for unknown job titles
        return ["Communication", "Teamwork", "Problem Solving", "Technical Skills", "Adaptability"]
    
    def get_quiz(self, quiz_id: int) -> Optional[Dict[str, Any]]:
        """
        Get quiz by ID
        """
        db = SessionLocal()
        try:
            quiz_attempt = db.query(QuizAttempt).filter(QuizAttempt.id == quiz_id).first()
            if not quiz_attempt:
                return None
            questions = quiz_attempt.questions
            if isinstance(questions, str):
                try:
                    questions = json.loads(questions)
                except Exception:
                    questions = []
            return {
                "quiz_id": quiz_attempt.id,
                "title": f"QCM - {quiz_attempt.job_title}",
                "job_title": quiz_attempt.job_title,
                "difficulty": quiz_attempt.difficulty,
                "questions": questions,
                "created_at": quiz_attempt.created_at.isoformat() if quiz_attempt.created_at is not None else None
            }
        finally:
            db.close()
    
    def submit_quiz_attempt(self, quiz_id: int, candidate_id: int, answers: Dict[int, str]) -> Dict[str, Any]:
        """
        Submit quiz answers and get evaluation results. Mark the quiz as completed.
        """
        db = SessionLocal()
        try:
            quiz_attempt = db.query(QuizAttempt).filter(QuizAttempt.id == quiz_id, QuizAttempt.candidate_id == candidate_id).first()
            if not quiz_attempt:
                raise ValueError("Quiz not found")
            
            quiz_data = {
                "quiz_title": f"QCM - {quiz_attempt.job_title}",
                "difficulty": quiz_attempt.difficulty,
                "job_title": quiz_attempt.job_title,
                "questions": quiz_attempt.questions
            }
            # Ensure answers dict keys are strings for JSON column and evaluation
            answers_str_keys = {str(k): v for k, v in answers.items()}
            evaluation = self.generator.evaluate_quiz(quiz_data, answers_str_keys)
            
            quiz_attempt.answers = cast(Any, answers_str_keys)
            quiz_attempt.total_score = evaluation["total_score"]
            quiz_attempt.category_scores = evaluation["category_scores"]
            quiz_attempt.detailed_results = evaluation["detailed_results"]
            setattr(quiz_attempt, 'completed_at', datetime.datetime.utcnow())
            db.commit()
            db.refresh(quiz_attempt)
            
            evaluation["attempt_id"] = quiz_attempt.id
            evaluation["quiz_title"] = quiz_data["quiz_title"]
            evaluation["job_title"] = quiz_data["job_title"]
            evaluation["difficulty"] = quiz_data["difficulty"]
            
            return evaluation
            
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()
    
    def get_candidate_quiz_history(self, candidate_id: int) -> List[Dict[str, Any]]:
        """
        Get quiz history for a candidate
        """
        db = SessionLocal()
        try:
            attempts = db.query(QuizAttempt).filter(
                QuizAttempt.candidate_id == candidate_id
            ).order_by(QuizAttempt.created_at.desc()).all()
            
            history = []
            for attempt in attempts:
                history.append({
                    "attempt_id": attempt.id,
                    "quiz_title": f"QCM - {attempt.job_title}",
                    "job_title": attempt.job_title,
                    "difficulty": attempt.difficulty,
                    "total_score": attempt.total_score,
                    "created_at": attempt.created_at.isoformat() if attempt.created_at is not None else None,
                    "category_scores": attempt.category_scores
                })
            
            return history
        finally:
            db.close()
    
    def get_quiz_statistics(self, quiz_id: int) -> Dict[str, Any]:
        """
        Get statistics for a specific quiz
        """
        db = SessionLocal()
        try:
            attempts = db.query(QuizAttempt).filter(QuizAttempt.id == quiz_id).all()
            
            if not attempts:
                return {"total_attempts": 0}
            
            scores = [a.total_score for a in attempts if a.total_score is not None]
            avg_score = sum(scores) / len(scores) if scores else 0
            
            return {
                "total_attempts": len(attempts),
                "average_score": avg_score
            }
        finally:
            db.close() 