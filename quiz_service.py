from typing import List, Dict, Any, Optional, cast
import uuid
from database import SessionLocal
from models import QuizAttempt, JobQuizAssignment
from databaseclient.models import ProfileCandidat
from databasehr.models import Job, JobSkill
from quiz_generator import QuizGenerator
import json
import datetime

class QuizService:
    def __init__(self):
        self.generator = QuizGenerator()
    
    def generate_quiz_for_candidate(self, candidate_id: int, job_title: str, num_questions: int = 10, job_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Generate a quiz for a candidate based on job requirements using AI model
        
        Args:
            candidate_id: ID of the candidate
            job_title: Job title/position
            num_questions: Number of questions to generate
            
        Returns:
            List of quiz questions
            
        Raises:
            ValueError: If quiz generation fails
        """
        db = SessionLocal()
        try:
            # Get candidate profile (optional: proceed without it if missing)
            candidate = db.query(ProfileCandidat).filter(ProfileCandidat.id == candidate_id).first()
            
            # Extract skills from candidate profile when available
            candidate_skills = []
            skills_data = candidate.skills if candidate else []
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
            if True:
                # Generate quiz using AI model (per required skill) based on Compétences Requises
                try:
                    print(f"\n🎯 Starting quiz generation for job: {job_title}")
                    print(f"📝 Number of questions requested: {num_questions}")
                    
                    # Get required skills with levels from job_skills table
                    print("\n🔍 Retrieving required skills...")
                    required_skills_with_levels = (
                        self._get_required_skills_for_job_id(job_id, db) if job_id is not None
                        else self._get_required_skills_for_job(job_title, db)
                    )
                    print(f"✅ Retrieved {len(required_skills_with_levels)} skills")
                    
                    # Log the skills being used for quiz generation
                    print("\n📋 Skills to be used for quiz generation:")
                    for skill in required_skills_with_levels:
                        print(f"   - {skill['skill_name']} (Level: {skill['skill_level']}, Required: {skill['is_required']})")
                    
                    # Generate quiz using the recruitment quiz method
                    print("\n🧠 Generating quiz questions...")
                    try:
                        quiz_data = self.generator.generate_recruitment_quiz(
                            job_title=job_title,
                            required_skills_with_levels=required_skills_with_levels,
                            questions_per_skill=num_questions,  # Changed from questions_per_skill to num_questions if needed
                            past_questions=past_questions
                        )
                        print("✅ Quiz generation completed successfully")
                    except Exception as gen_error:
                        print(f"❌ Error during quiz generation: {str(gen_error)}")
                        raise
                    
                    # Validate the generated quiz data
                    if not quiz_data:
                        raise ValueError("Quiz generation returned empty response")
                    if 'skills_quizzes' not in quiz_data or not isinstance(quiz_data['skills_quizzes'], list):
                        raise ValueError("Invalid quiz format: missing 'skills_quizzes' list")
                    if not quiz_data['skills_quizzes']:
                        raise ValueError("No skill quizzes were generated")

                    # Log quiz generation results
                    total_questions = sum(len(skill_quiz.get('questions', [])) for skill_quiz in quiz_data['skills_quizzes'])
                    print(f"\n📊 Quiz Generation Results:")
                    print(f"   - Total skills processed: {len(quiz_data['skills_quizzes'])}")
                    print(f"   - Total questions generated: {total_questions}")
                    for i, skill_quiz in enumerate(quiz_data['skills_quizzes'], 1):
                        skill_name = skill_quiz.get('skill_name', 'Unknown Skill')
                        questions = skill_quiz.get('questions', [])
                        print(f"   - {skill_name}: {len(questions)} questions")
                        
                except Exception as e:
                    error_msg = f"❌ Error generating quiz: {str(e)}"
                    print(error_msg)
                    import traceback
                    traceback.print_exc()
                    
                    # Log the exact error details for debugging
                    error_details = {
                        'error': str(e),
                        'job_title': job_title,
                        'num_questions': num_questions,
                        'skills_count': len(required_skills_with_levels) if 'required_skills_with_levels' in locals() else 0,
                        'past_questions_count': len(past_questions) if past_questions else 0
                    }
                    print("\n📋 Error Details:")
                    for key, value in error_details.items():
                        print(f"   - {key}: {value}")
                    
                    # Provide more specific error messages for common issues
                    if "API key" in str(e):
                        raise ValueError("Authentication failed. Please check your API key configuration.")
                    elif "rate limit" in str(e).lower():
                        raise ValueError("API rate limit exceeded. Please try again later.")
                    elif "timeout" in str(e).lower():
                        raise ValueError("Request timed out. The server is taking too long to respond.")
                    else:
                        raise ValueError("Failed to generate quiz questions. Please check the logs for details.")
                
                # Create one quiz attempt per skill and normalize questions
                for skill_quiz in quiz_data['skills_quizzes']:
                    questions = skill_quiz.get('questions', []) or []
                    if not isinstance(questions, list) or len(questions) == 0:
                        continue

                    # Normalize each question options to dict A-D and correct_answer to letter
                    normalized_questions = []
                    for idx, q in enumerate(questions, start=1):
                        if not isinstance(q, dict):
                            continue
                        qtext = str(q.get('question', '')).strip()
                        if not qtext:
                            continue
                        raw_options = q.get('options', [])
                        opts_list = []
                        if isinstance(raw_options, dict):
                            if all(k.upper() in ['A','B','C','D'] for k in raw_options.keys()):
                                opts_list = [raw_options.get(k, '') for k in ['A','B','C','D']]
                            else:
                                opts_list = list(raw_options.values())
                        elif isinstance(raw_options, list):
                            opts_list = raw_options
                        opts_list = [str(o).strip() for o in (opts_list or []) if str(o).strip()]
                        if len(opts_list) < 2:
                            continue
                        opts_list = opts_list[:4]
                        keys = ['A','B','C','D'][:len(opts_list)]
                        options = {k: v for k, v in zip(keys, opts_list)}

                        correct = q.get('correct_answer', 'A')
                        if isinstance(correct, int):
                            idx = max(0, min(correct, len(opts_list)-1))
                            correct = chr(ord('A') + idx)
                        else:
                            correct = str(correct).strip().upper()
                            if correct not in options:
                                try:
                                    idx = int(correct)
                                    idx = max(0, min(idx, len(opts_list)-1))
                                    correct = chr(ord('A') + idx)
                                except Exception:
                                    correct = 'A'

                        normalized_questions.append({
                            'id': idx,
                            'question': qtext,
                            'options': options,
                            'correct_answer': correct,
                            'explanation': str(q.get('explanation', '')).strip(),
                            'difficulty': str(q.get('difficulty', 'medium')).lower(),
                            'category': str(q.get('category', 'technique')).lower(),
                            'skill_related': str(q.get('skill_related', skill_quiz.get('skill_name','General')))
                        })

                    if not normalized_questions:
                        continue

                    quiz_attempt = QuizAttempt(
                        candidate_id=candidate_id,
                        job_title=job_title,
                        difficulty=None,
                        questions=normalized_questions,
                        answers=None,
                        total_score=None,
                        category_scores=None,
                        detailed_results=None
                    )
                    db.add(quiz_attempt)
                    db.commit()
                    db.refresh(quiz_attempt)

                    quizzes.append({
                        'quiz_id': quiz_attempt.id,
                        'skill': skill_quiz.get('skill_name') or job_title,
                        'job_title': job_title,
                        'questions': normalized_questions
                    })
            
            if not quizzes:
                raise ValueError("Failed to generate any quiz questions")
            
            return quizzes
        finally:
            db.close()

    def generate_job_based_quiz(self, job_id: int, candidate_id: int, num_questions: int = 15) -> Optional[Dict[str, Any]]:
        """
        Generate a quiz based on job requirements for a specific candidate
        """
        db = SessionLocal()
        try:
            # Get job and its required skills
            job = db.query(Job).filter(Job.id == job_id).first()
            if not job:
                raise ValueError("Job not found")
            
            # Get job skills with levels
            job_skills = db.query(JobSkill).filter(JobSkill.job_id == job_id).all()
            required_skills_with_levels = [
                {
                    "skill_name": skill.skill_name,
                    "skill_level": getattr(skill, 'skill_level', 'intermediate'),
                    "is_required": skill.is_required
                } 
                for skill in job_skills if skill.is_required
            ]
            required_skills = [skill.skill_name for skill in job_skills if skill.is_required]
            
            if not required_skills:
                # Fallback: use job title as skill if no specific skills found
                required_skills = [job.title]
            
            # Get candidate profile
            candidate = db.query(ProfileCandidat).filter(ProfileCandidat.id == candidate_id).first()
            if not candidate:
                raise ValueError("Candidate not found")
            
            # Get past questions from previous quiz attempts for this candidate and job
            past_questions = self._get_past_questions_for_candidate_and_job(candidate_id, job_id, db)
            
            # Generate quiz based on job requirements with skill levels
            max_retries = 2
            retry_count = 0
            quiz_data = None
            
            while retry_count <= max_retries and (not quiz_data or not quiz_data.get("questions")):
                try:
                    quiz_data = self.generator.generate_recruitment_quiz(
                        job_title=job.title,
                        required_skills_with_levels=required_skills_with_levels,
                        job_description=getattr(job, 'description', ''),
                        questions_per_skill=num_questions if retry_count == 0 else max(3, num_questions // 2),
                        past_questions=[] if retry_count > 0 else past_questions
                    )
                    
                    # Validate the response
                    if quiz_data and isinstance(quiz_data, dict) and "questions" in quiz_data:
                        if not isinstance(quiz_data["questions"], list):
                            raise ValueError("Invalid questions format in response")
                        if not quiz_data["questions"]:
                            raise ValueError("No questions generated")
                        break  # Success
                    
                except (json.JSONDecodeError, ValueError) as e:
                    print(f"Attempt {retry_count + 1} failed: {str(e)}")
                    if retry_count == max_retries:
                        raise ValueError(f"Failed to generate valid quiz after {max_retries + 1} attempts. Last error: {str(e)}")
                
                retry_count += 1
                if retry_count <= max_retries:
                    print(f"Retrying quiz generation (attempt {retry_count + 1})...")
            
            if not quiz_data or not quiz_data.get("questions"):
                raise ValueError(f"Failed to generate quiz for job '{job.title}' after multiple attempts.")
            
            # Create quiz attempt
            quiz_attempt = QuizAttempt(
                candidate_id=candidate_id,
                job_title=job.title,
                difficulty="job_based",
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
            quiz_data["job_id"] = job_id
            quiz_data["job_title"] = job.title
            
            return quiz_data
        finally:
            db.close()

    def assign_quiz_to_candidate(self, job_id: int, candidate_id: int, assigned_by: int, due_date: Optional[datetime.datetime] = None) -> Dict[str, Any]:
        """
        Assign a quiz to a candidate for a specific job
        """
        db = SessionLocal()
        try:
            # Check if quiz already assigned
            existing_assignment = db.query(JobQuizAssignment).filter(
                JobQuizAssignment.job_id == job_id,
                JobQuizAssignment.candidate_id == candidate_id,
                JobQuizAssignment.status == "assigned"
            ).first()
            
            if existing_assignment:
                raise ValueError("Quiz already assigned to this candidate for this job")
            
            # Create assignment
            assignment = JobQuizAssignment(
                job_id=job_id,
                candidate_id=candidate_id,
                assigned_by=assigned_by,
                due_date=due_date,
                status="assigned"
            )
            db.add(assignment)
            db.commit()
            db.refresh(assignment)
            
            return {
                "assignment_id": assignment.id,
                "job_id": job_id,
                "candidate_id": candidate_id,
                "assigned_at": assignment.assigned_at,
                "due_date": assignment.due_date,
                "status": assignment.status
            }
        finally:
            db.close()

    def get_assigned_quizzes_for_candidate(self, candidate_id: int) -> List[Dict[str, Any]]:
        """
        Get all quiz assignments for a candidate
        """
        db = SessionLocal()
        try:
            assignments = db.query(JobQuizAssignment).filter(
                JobQuizAssignment.candidate_id == candidate_id,
                JobQuizAssignment.status.in_(["assigned", "in_progress"])
            ).all()
            
            result = []
            for assignment in assignments:
                job = db.query(Job).filter(Job.id == assignment.job_id).first()
                result.append({
                    "assignment_id": assignment.id,
                    "job_id": assignment.job_id,
                    "job_title": job.title if job else "Unknown Job",
                    "title": f"Quiz - {job.title if job else 'Poste inconnu'}",
                    "description": f"Quiz assigné le {assignment.assigned_at.strftime('%d/%m/%Y')}",
                    "assigned_at": assignment.assigned_at,
                    "due_date": assignment.due_date,
                    "status": assignment.status
                })
            
            return result
        finally:
            db.close()

    def _get_past_questions_for_candidate(self, candidate_id: int, db) -> List[str]:
        """Get past questions for a candidate to avoid repetition"""
        past_attempts = db.query(QuizAttempt).filter(QuizAttempt.candidate_id == candidate_id).all()
        past_questions = []
        for attempt in past_attempts:
            if attempt.questions:
                for question in attempt.questions:
                    if isinstance(question, dict) and 'question' in question:
                        past_questions.append(question['question'])
        return past_questions

    def _get_past_questions_for_candidate_and_job(self, candidate_id: int, job_id: int, db) -> List[str]:
        """Get past questions for a candidate and specific job to avoid repetition"""
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            return []
        
        past_attempts = db.query(QuizAttempt).filter(
            QuizAttempt.candidate_id == candidate_id,
            QuizAttempt.job_title == job.title
        ).all()
        
        past_questions = []
        for attempt in past_attempts:
            if attempt.questions:
                for question in attempt.questions:
                    if isinstance(question, dict) and 'question' in question:
                        past_questions.append(question['question'])
        return past_questions

    def _get_required_skills_for_job(self, job_title: str, db) -> List[Dict]:
        """
        Get required skills for a job from the job_skills table
        
        Args:
            job_title: The title of the job to get skills for
            db: Database session
            
        Returns:
            List of dictionaries with skill_name, skill_level, and is_required
        """
        from databasehr.models import Job, JobSkill
        
        print(f"\n🔍 Looking up skills for job: {job_title}")
        
        try:
            # Find the job by exact title then fallback to ILIKE
            job = db.query(Job).filter(Job.title == job_title).order_by(Job.id.desc()).first()
            if not job:
                job = db.query(Job).filter(Job.title.ilike(f"%{job_title}%")).order_by(Job.created_at.desc()).first()
            if not job:
                raise ValueError(f"No job found with title matching: {job_title}")
            print(f"✅ Found job ID: {job.id}, Title: {job.title}")
            
            # Get all skills for this job
            skills = db.query(JobSkill).filter(JobSkill.job_id == job.id).all()
            print(f"📊 Found {len(skills)} skills for job ID {job.id}")
            
            # Format skills for quiz generation
            formatted_skills = []
            for skill in skills:
                try:
                    skill_data = {
                        'skill_name': str(skill.skill_name).strip(),
                        'skill_level': str(skill.skill_level).lower() if skill.skill_level else 'intermediate',
                        'is_required': bool(skill.is_required) if skill.is_required is not None else True
                    }
                    # Validate skill data
                    if not skill_data['skill_name']:
                        print(f"⚠️  Warning: Empty skill name found for job ID {job.id}")
                        continue
                        
                    # Ensure skill_level is valid
                    valid_levels = ['beginner', 'intermediate', 'advanced', 'expert']
                    if skill_data['skill_level'] not in valid_levels:
                        print(f"⚠️  Warning: Invalid skill level '{skill_data['skill_level']}' for skill '{skill_data['skill_name']}'. Defaulting to 'intermediate'")
                        skill_data['skill_level'] = 'intermediate'
                        
                    formatted_skills.append(skill_data)
                    print(f"   - {skill_data['skill_name']} ({skill_data['skill_level']}) {'(Required)' if skill_data['is_required'] else ''}")
                    
                except Exception as skill_error:
                    print(f"⚠️  Error processing skill: {str(skill_error)}")
                    print(f"    Skill data: {str(skill.__dict__) if hasattr(skill, '__dict__') else 'No skill data'}")
                    continue
            
            if not formatted_skills:
                raise ValueError(f"No valid required skills found for job: {job_title}")
                
            print(f"✅ Successfully processed {len(formatted_skills)} skills for quiz generation")
            return formatted_skills
            
        except Exception as e:
            error_msg = f"❌ Error in _get_required_skills_for_job: {str(e)}"
            print(error_msg)
            import traceback
            traceback.print_exc()
            raise

    def _get_required_skills_for_job_id(self, job_id: int, db) -> List[Dict]:
        """Return required skills (name, level, is_required) for a specific job id."""
        from databasehr.models import Job, JobSkill
        if job_id is None:
            raise ValueError("job_id is required")
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            raise ValueError(f"No job found with id: {job_id}")
        skills = db.query(JobSkill).filter(JobSkill.job_id == job.id).all()
        if not skills:
            raise ValueError(f"No skills found for job id: {job_id}")
        formatted_skills: List[Dict[str, Any]] = []
        for skill in skills:
            formatted_skills.append({
                'skill_name': str(skill.skill_name).strip(),
                'skill_level': str(skill.skill_level).lower() if skill.skill_level else 'intermediate',
                'is_required': bool(skill.is_required) if skill.is_required is not None else True
            })
        required = [s for s in formatted_skills if s['is_required']]
        if not required:
            raise ValueError(f"No required skills set for job id: {job_id}")
        return required
    
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