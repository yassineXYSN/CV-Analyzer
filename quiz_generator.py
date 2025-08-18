import os
import json
import random
import uuid
import re
import time
import requests
from datetime import datetime
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from huggingface_hub import InferenceClient

load_dotenv()

# Configuration
# Use the provided token directly
HF_ACCESS_TOKEN = "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"

# Use the same model as in data_generator.py
HF_MODEL = "deepseek-ai/DeepSeek-R1-0528-Qwen3-8B"


def query_deepseek(prompt):
    """Query the DeepSeek model using huggingface_hub.InferenceClient"""
    try:
        client = InferenceClient(
            model=HF_MODEL,
            token=HF_ACCESS_TOKEN,
            timeout=120,  # Increased timeout
        )
        completion = client.chat.completions.create(
            model=HF_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.8,  # Increased temperature for more randomization
            max_tokens=4000  # Increased to prevent truncation
        )
        return completion
    except Exception as e:
        print(f"Error querying DeepSeek: {e}")
        return None

class QuizGenerator:
    def __init__(self):
        self.question_types = ["technique", "comportemental", "culturel"]
    
    def _fail_with_error(self, message: str) -> None:
        """Raise an error with the given message"""
        raise ValueError(f"Quiz generation failed: {message}")

    def _parse_quiz_response(self, content: str, job_title: str = "") -> Dict[str, Any]:
        """Parse the raw response from the AI model into a structured quiz
        
        Args:
            content: Raw content from the AI model
            job_title: The job title for the quiz (used for fallback title)
            
        Returns:
            Dict containing the parsed quiz data
            
        Raises:
            ValueError: If the content cannot be parsed into a valid quiz
        """
        if not content or not content.strip():
            raise ValueError("Empty response from AI model")
            
        content = content.strip()
        
        def try_parse_json(json_str: str) -> Optional[Dict]:
            """Helper to attempt JSON parsing with error details"""
            try:
                # Clean up common JSON issues
                json_str = json_str.strip()
                
                # Remove markdown code block markers if present
                if json_str.startswith('```'):
                    json_str = re.sub(r'^```(?:json)?\s*', '', json_str, flags=re.IGNORECASE)
                    json_str = re.sub(r'\s*```$', '', json_str)
                
                # Fix common JSON syntax issues
                json_str = json_str.replace('\n', ' ').replace('\r', '')
                json_str = re.sub(r',\s*([}\]])', r'\1', json_str)  # Remove trailing commas
                json_str = re.sub(r'([{\[,])\s*([}\],])', r'\1null\2', json_str)  # Add null for empty values
                
                # Try to parse the cleaned JSON
                parsed = json.loads(json_str)
                
                # Basic validation of the parsed structure
                if isinstance(parsed, dict):
                    if 'questions' in parsed and not isinstance(parsed['questions'], list):
                        return None
                    return parsed
                elif isinstance(parsed, list):
                    # Handle case where response is just an array of questions
                    return {
                        'quiz_title': f"QCM - {job_title}" if job_title else "QCM",
                        'job_title': job_title or "",
                        'questions': parsed
                    }
                return None
                
            except (json.JSONDecodeError, TypeError, AttributeError) as e:
                print(f"JSON parse error: {e}")
                return None
        
        # Try different parsing strategies in order of preference
        parsing_attempts = [
            # 1. Try parsing as direct JSON
            lambda: try_parse_json(content),
            
            # 2. Try extracting JSON from markdown code blocks
            lambda: try_parse_json(re.search(r'```(?:json)?\s*(.*?)\s*```', content, re.DOTALL).group(1) 
                                 if re.search(r'```(?:json)?\s*\{', content, re.DOTALL) else None),
            
            # 3. Try finding any JSON object in the content
            lambda: try_parse_json(re.search(r'\{(?:[^{}]|\{(?:[^{}]|\{[^{}]*\})*\})*\}', content, re.DOTALL).group(0)
                                 if re.search(r'\{.*\}', content, re.DOTALL) else None),
            
            # 4. Try extracting questions using regex as last resort
            lambda: {
                'quiz_title': f"QCM - {job_title}" if job_title else "QCM",
                'job_title': job_title or "",
                'questions': self.extract_questions_with_regex(content)
            } if self.extract_questions_with_regex(content) else None
        ]
        
        # Try each parsing strategy until one works
        parsed_data = None
        for attempt in parsing_attempts:
            try:
                parsed_data = attempt()
                if parsed_data and (isinstance(parsed_data, dict) and 'questions' in parsed_data):
                    # Validate questions structure
                    if not isinstance(parsed_data['questions'], list):
                        continue
                    if parsed_data['questions'] and all(
                        isinstance(q, dict) and 'question' in q and 'options' in q and 'correct_answer' in q
                        for q in parsed_data['questions']
                    ):
                        return parsed_data
            except Exception as e:
                print(f"Parsing attempt failed: {e}")
                continue
        
        # If we get here, all parsing attempts failed
        error_msg = (
            "Failed to parse AI response. The model did not return valid JSON or questions.\n"
            f"Response preview: {content[:300]}..."
        )
        print(error_msg)
        raise ValueError(error_msg)

    def _create_fallback_quiz(self, job_title: str, num_questions: int = 5) -> Dict[str, Any]:
        """Create a simple fallback quiz when AI generation fails"""
        print("⚠️  Using fallback quiz generator")
        
        fallback_questions = [
            {
                "question": f"What is your experience with {job_title} role?",
                "options": {
                    "A": "Less than 1 year",
                    "B": "1-3 years",
                    "C": "3-5 years",
                    "D": "More than 5 years"
                },
                "correct_answer": "B",
                "difficulty": "easy",
                "skill_related": "General Experience"
            },
            {
                "question": "Rate your problem-solving skills from 1-5",
                "options": {
                    "A": "1 - Novice",
                    "B": "2 - Basic",
                    "C": "3 - Intermediate",
                    "D": "4 - Advanced",
                    "E": "5 - Expert"
                },
                "correct_answer": "C",
                "difficulty": "easy",
                "skill_related": "Problem Solving"
            },
            {
                "question": "How do you handle tight deadlines?",
                "options": {
                    "A": "Prioritize tasks and work efficiently",
                    "B": "Request for deadline extension",
                    "C": "Work overtime if needed",
                    "D": "All of the above"
                },
                "correct_answer": "D",
                "difficulty": "medium",
                "skill_related": "Time Management"
            }
        ]
        
        # Ensure we don't exceed available questions
        questions = fallback_questions[:min(num_questions, len(fallback_questions))]
        
        return {
            "quiz_title": f"{job_title} - Technical Assessment",
            "job_title": job_title,
            "questions": questions,
            "is_fallback": True  # Flag to indicate this is a fallback quiz
        }

    def _generate_skill_quiz(self, job_title: str, skill: Dict, job_description: str = "", 
                           num_questions: int = 5, past_questions: List = None) -> Dict[str, Any]:
        """Generate a quiz for a specific skill"""
        if past_questions is None:
            past_questions = []
            
        skill_name = skill.get('skill_name', 'Unknown Skill')
        skill_level = skill.get('skill_level', 'Intermediate')
        
        print(f"🔄 Generating {skill_level} level quiz for skill: {skill_name}")
        
        # Create a more specific prompt for the skill
        prompt = (
            f"Generate a {skill_level} level multiple choice quiz about {skill_name} "
            f"for a {job_title} position. "
            f"Job Description: {job_description[:500]}\n\n"
            f"Create exactly {num_questions} questions with 4 options each. "
            "Each question should be challenging and relevant to the skill level. "
            "Format the response as a JSON object with 'questions' array containing objects with: "
            "'question', 'options' (object with A,B,C,D keys), 'correct_answer' (letter), "
            "'difficulty' (easy/medium/hard), and 'explanation' (why the answer is correct)."
            "\n\nRespond with ONLY the JSON, no other text or markdown formatting."
        )
        
        response = query_deepseek(prompt)
        if not response:
            raise ValueError("Failed to get response from AI model")
            
        content = response.choices[0].message.content if hasattr(response.choices[0].message, 'content') else str(response.choices[0].message)
        
        if not content or not content.strip():
            raise ValueError("Empty content in AI response")
            
        try:
            # Try to parse the response as JSON
            quiz_data = json.loads(content)
            
            # If we get here, parsing succeeded, but let's validate the structure
            if not isinstance(quiz_data, dict) or 'questions' not in quiz_data:
                raise ValueError("Invalid quiz format in response")
                
            # Ensure we have the required fields
            quiz_data['quiz_title'] = f"{skill_name} ({skill_level})"
            quiz_data['job_title'] = job_title
            quiz_data['skill_name'] = skill_name
            quiz_data['skill_level'] = skill_level
            quiz_data['is_fallback'] = False
            
            return quiz_data
            
        except json.JSONDecodeError:
            # If parsing as JSON fails, try to extract JSON from the response
            print("⚠️  Could not parse response as JSON, attempting to extract...")
            try:
                # Try to find JSON in the response
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    quiz_data = json.loads(json_match.group(0))
                    if not isinstance(quiz_data, dict) or 'questions' not in quiz_data:
                        raise ValueError("Could not find valid quiz data in response")
                        
                    quiz_data['quiz_title'] = f"{skill_name} ({skill_level})"
                    quiz_data['job_title'] = job_title
                    quiz_data['skill_name'] = skill_name
                    quiz_data['skill_level'] = skill_level
                    quiz_data['is_fallback'] = False
                    return quiz_data
                raise
            except Exception as e:
                print(f"⚠️  Could not extract quiz data: {str(e)}")
                raise ValueError("Could not parse quiz data from AI response")

    def generate_recruitment_quiz(self, job_title: str, required_skills_with_levels: List[Dict], 
                               job_description: str = "", questions_per_skill: int = 5, 
                               past_questions: Optional[list] = None) -> Dict[str, Any]:
        """
        Generate skill-specific quizzes for a job position
        
        Args:
            job_title: The job title/position
            required_skills_with_levels: List of dicts with skill_name, skill_level, is_required
            job_description: Job description for context
            questions_per_skill: Number of questions to generate per skill
            past_questions: List of previously used questions to avoid (optional)
            
        Returns:
            Dictionary containing quizzes organized by skill
        """
        if past_questions is None:
            past_questions = []
            
        print(f"\n📊 Generating quizzes for job: {job_title}")
        print(f"📋 Required Skills: {[s['skill_name'] for s in required_skills_with_levels]}")
        
        quizzes = {
            'job_title': job_title,
            'job_description': job_description,
            'skills_quizzes': [],
            'generated_at': str(datetime.now())
        }
        
        # Generate a quiz for each required skill
        for skill in required_skills_with_levels:
            if not skill.get('is_required', True):
                continue
                
            try:
                skill_quiz = self._generate_skill_quiz(
                    job_title=job_title,
                    skill=skill,
                    job_description=job_description,
                    num_questions=questions_per_skill,
                    past_questions=past_questions
                )
                
                if skill_quiz:
                    quizzes['skills_quizzes'].append(skill_quiz)
                    print(f"✅ Generated {len(skill_quiz.get('questions', []))} questions for {skill['skill_name']}")
                
            except Exception as e:
                print(f"⚠️  Skipping {skill.get('skill_name', 'unknown')} due to error: {str(e)}")
                continue
        
        return quizzes
        if num_returned == 0:
            quiz_data["warning"] = "Le QCM généré ne contient aucune question valide."
        elif num_returned < num_questions:
            quiz_data["warning"] = f"Le QCM généré contient seulement {num_returned} question(s) sur {num_questions} demandées."
        return quiz_data

    def generate_quiz(self, job_title: str, required_skills: List[str], candidate_skills: List[str], num_questions: int = 10, past_questions: Optional[list] = None, use_expert_prompt: bool = False) -> Dict[str, Any]:
        """
        Generate a QCM quiz based on job requirements (legacy method)
        """
        if past_questions is None:
            past_questions = []
        if use_expert_prompt:
            prompt = self._create_expert_quiz_prompt(job_title, required_skills, candidate_skills, num_questions, past_questions)
        else:
            prompt = self._create_quiz_prompt(job_title, required_skills, candidate_skills, num_questions)
        response = query_deepseek(prompt)
        content = response.choices[0].message.content if response and hasattr(response, 'choices') and response.choices else ""
        quiz_data = self._parse_quiz_response(content, job_title)
        
        # Apply randomization and deduplication
        quiz_data = self._randomize_and_deduplicate_quiz(quiz_data, past_questions)
        
        # Apply balanced skill distribution if multiple skills
        all_skills = required_skills + candidate_skills
        if len(all_skills) > 1:
            quiz_data = self._ensure_balanced_skill_distribution(quiz_data, all_skills)
        
        num_returned = len(quiz_data["questions"]) if "questions" in quiz_data else 0
        if num_returned == 0:
            quiz_data["warning"] = "Le QCM généré ne contient aucune question valide."
        elif num_returned < num_questions:
            quiz_data["warning"] = f"Le QCM généré contient seulement {num_returned} question(s) sur {num_questions} demandées."
        return quiz_data

    def _create_quiz_prompt(self, job_title: str, required_skills: List[str], candidate_skills: List[str], num_questions: int) -> str:
        """Create the prompt for quiz generation"""
        prompt = f"""Generate a quiz with {num_questions} questions for job title: {job_title}.
Required skills: {', '.join(required_skills)}
Candidate skills: {', '.join(candidate_skills)}

Respond ONLY with a valid JSON object with this structure:
{{
    \"quiz_title\": \"QCM - {job_title}\",
    \"job_title\": \"{job_title}\",
    \"questions\": [
        {{
            \"id\": 1,
            \"question\": \"Question text\",
            \"options\": {{\"A\": \"Option A\", \"B\": \"Option B\", \"C\": \"Option C\", \"D\": \"Option D\"}},
            \"correct_answer\": \"A\",
            \"explanation\": \"Explanation\",
            \"category\": \"technique\",
            \"skill_related\": \"Skill name\"
        }}
    ]
}}
Your response MUST start with '{' and end with '}'. Do NOT include any explanation, markdown, <think> blocks, or extra text. Output ONLY the JSON object, nothing else. If you do not know the answer, return an empty questions array in the JSON object."""
        return prompt

    def _create_expert_quiz_prompt(self, job_title: str, required_skills: List[str], candidate_skills: List[str], num_questions: int, past_questions: list) -> str:
        # If only one skill, make the prompt very explicit
        if len(required_skills + candidate_skills) == 1:
            skill = (required_skills + candidate_skills)[0]
            past_qs = '\n'.join([f'- {q}' for q in past_questions[:10]]) if past_questions else 'None'
            prompt = f"""
You are an expert AI quiz generator.

**Task:** Generate exactly {num_questions} unique, challenging multiple-choice questions (MCQs) that test the candidate's real-world knowledge and application of the following skill/competency:

SKILL: {skill}

**CRITICAL REQUIREMENTS FOR RANDOMIZATION & VARIETY:**
- Generate questions with HIGH VARIETY in difficulty levels, topics, and scenarios
- Use different question formats: theoretical, practical, scenario-based, problem-solving
- Vary the complexity: mix easy, medium, and hard questions
- Cover different aspects of the skill: basics, advanced concepts, real-world applications
- Use diverse contexts: different industries, scenarios, and use cases
- Ensure questions are COMPLETELY DIFFERENT from any previous questions

**PREVIOUSLY USED QUESTIONS TO AVOID:**
{past_qs}

**IMPORTANT REQUIREMENTS:**
- All questions must be directly and specifically about this skill.
- Do NOT include questions about other skills, general knowledge, or unrelated topics.
- Each question must have exactly 4 choices labeled A, B, C, and D.
- Provide the correct answer (label only: A, B, C, or D).
- Avoid trivia or generic soft-skill questions.
- Make the quiz harder depending on the job title: {job_title} and the candidate's experience.
- Ensure ALL questions and options are COMPLETE - do not truncate or leave incomplete sentences.
- Each question should be a complete, grammatically correct sentence ending with a question mark.
- Each option should be a complete, grammatically correct sentence or phrase.

**QUESTION VARIETY EXAMPLES:**
- Theoretical: "What is the fundamental principle behind..."
- Practical: "In a real-world scenario where you need to..."
- Problem-solving: "Given the following situation, how would you..."
- Best practice: "Which approach is considered best practice for..."
- Troubleshooting: "When encountering this error, what should you..."

**OUTPUT FORMAT (JSON array):**
[
  {{
    "question": "Complete question text ending with question mark?",
    "options": {{
      "A": "Complete option A text",
      "B": "Complete option B text", 
      "C": "Complete option C text",
      "D": "Complete option D text"
    }},
    "correct_answer": "A"
  }}
]

**CRITICAL:** Your response MUST start with '[' and end with ']'. Do NOT include any explanation, markdown, <think> blocks, or extra text. Output ONLY the JSON array, nothing else. Ensure all questions and options are complete and not truncated.
"""
            return prompt
        # Otherwise, use the original logic
        competencies = ', '.join(required_skills + candidate_skills)
        past_qs = '\n'.join([f'- {q}' for q in past_questions[:10]]) if past_questions else 'None'
        prompt = f"""
You are an expert AI quiz generator.

**Task:** Generate a unique set of {num_questions} multiple-choice questions (MCQs) based on the following competencies from a CV:

{competencies}

**CRITICAL REQUIREMENTS FOR RANDOMIZATION & VARIETY:**
- Generate questions with HIGH VARIETY in difficulty levels, topics, and scenarios
- Use different question formats: theoretical, practical, scenario-based, problem-solving
- Vary the complexity: mix easy, medium, and hard questions
- Cover different aspects of each skill: basics, advanced concepts, real-world applications
- Use diverse contexts: different industries, scenarios, and use cases
- Ensure questions are COMPLETELY DIFFERENT from any previous questions

**PREVIOUSLY USED QUESTIONS TO AVOID:**
{past_qs}

**Constraints:**
- At least {num_questions} questions must be generated.
- Each question must have exactly 4 choices labeled A, B, C, and D
- Provide the correct answer (label only: A, B, C, or D)
- Focus on professional, real-world scenarios when possible
- Avoid trivia or generic soft-skill questions
- Do not include any question that is not related to the job title or the competencies and skills
- Make the quiz harder depending on the job title and the competencies and experience of the candidate
- Questions must not be repetitive
- Ensure ALL questions and options are COMPLETE - do not truncate or leave incomplete sentences

**OUTPUT FORMAT (JSON array):**
[
  {{
    "question": "Complete question text ending with question mark?",
    "options": {{
      "A": "Complete option A text",
      "B": "Complete option B text",
      "C": "Complete option C text", 
      "D": "Complete option D text"
    }},
    "correct_answer": "C"
  }},
  ...
]

**CRITICAL:** Your response MUST start with '[' and end with ']'. Do NOT include any explanation, markdown, <think> blocks, or extra text. Output ONLY the JSON array, nothing else. Ensure all questions and options are complete and not truncated.
"""
        return prompt

    def _create_recruitment_quiz_prompt(self, job_title: str, required_skills_with_levels: List[Dict], job_description: str, num_questions: int, past_questions: list) -> str:
        """Create a prompt for generating a recruitment quiz."""
        
        # Format skills with levels
        skills_text = []
        for skill in required_skills_with_levels:
            skill_name = skill.get("skill_name", "")
            skill_level = skill.get("skill_level", "Intermediate").capitalize()
            is_required = skill.get("is_required", True)
            priority = "REQUIRED" if is_required else "PREFERRED"
            skills_text.append(f"- {skill_name} ({skill_level}) - {priority}")
        
        skills_formatted = "\n".join(skills_text) if skills_text else "No specific skills provided"
        
        # Format past questions to avoid
        past_qs = ""
        if past_questions:
            past_qs = "\n".join([f"- {q}" for q in past_questions[:5]])  # Limit to 5 to avoid token overflow
        else:
            past_qs = "None provided"

        # Create skill distribution
        total_skills = len(required_skills_with_levels)
        questions_per_skill = max(1, num_questions // max(1, total_skills))
        remaining_questions = num_questions - (questions_per_skill * total_skills)
        
        skill_distribution = []
        for i, skill in enumerate(required_skills_with_levels):
            count = questions_per_skill + (1 if i < remaining_questions else 0)
            if count > 0:
                skill_distribution.append(f"- {count} questions about {skill['skill_name']} ({skill.get('skill_level', 'Intermediate')})")
        
        skill_distribution_text = "\n".join(skill_distribution)
        
        prompt = f"""You are an expert technical recruiter creating a skills assessment quiz. 

**JOB POSITION:** {job_title}
**JOB DESCRIPTION:**
{job_description[:400] if job_description else 'Not provided'}

**REQUIRED SKILLS & LEVELS:**
{skills_formatted}

**QUIZ REQUIREMENTS:**
- Generate exactly {num_questions} multiple-choice questions
- Questions must be distributed as follows:
{skill_distribution_text}
- Each question must test a specific skill from the required skills list
- Difficulty must match the specified skill level
- No generic or soft-skill questions
- No questions about experience levels or years of experience

**QUESTION FORMAT:**
- Each question must have exactly 4 options (A, B, C, D)
- Only one correct answer per question
- Include clear, technical explanations
- Use realistic code examples where applicable
- Questions should be practical and job-relevant

**PREVIOUSLY USED QUESTIONS (AVOID THESE):**
{past_qs}

**RESPONSE FORMAT (STRICT JSON):**
{{
  "quiz_title": "Technical Assessment - {job_title}",
  "job_title": "{job_title}",
  "questions": [
    {{
      "id": 1,
      "question": "Specific technical question about a required skill?",
      "options": {{
        "A": "Option A (must be a complete answer)",
        "B": "Option B (must be a complete answer)",
        "C": "Option C (must be a complete answer)",
        "D": "Option D (must be a complete answer)"
      }},
      "correct_answer": "A",
      "explanation": "Clear explanation of why this is the correct answer",
      "skill_tested": "Exact skill name from required skills",
      "difficulty": "Beginner/Intermediate/Advanced/Expert"
    }}
  ]
}}

**CRITICAL INSTRUCTIONS:**
1. Your response MUST be valid JSON that follows the exact structure above
2. Start with '{{' and end with '}}'
3. Do not include any markdown formatting or code blocks
4. Do not include any text outside the JSON object
5. Escape all special characters in strings
6. Ensure all brackets and quotes are properly closed
7. All questions must be technical and test specific skills from the required skills list
8. Do NOT include any questions about:
   - Rating proficiency or skill levels
   - Years of experience
   - Generic soft skills
   - Company culture or work preferences

**EXAMPLES OF FORBIDDEN QUESTIONS:**
- "How many years of experience do you have with Python?"
- "Rate your SQL skills from 1 to 10"
- "What is your preferred work environment?"
- "How do you handle team conflicts?"

**EXAMPLES OF GOOD QUESTIONS:**
- "Which Python method is used to sort a list in place?"
- "What is the time complexity of a binary search algorithm?"
- "Which SQL query finds duplicate values in a table?"

**REMEMBER:**
- Generate exactly {num_questions} questions
- Follow the exact JSON format shown above
- Test only the specific skills listed in the required skills
- Make questions practical and job-relevant
- Include clear explanations for answers
- Ensure all questions have exactly 4 options (A, B, C, D)
- Only one correct answer per question
- No markdown or extra text in the response
- Escape all special characters
- Each question must specify the exact skill it's testing in the 'skill_tested' field
- Include a difficulty level for each question (Beginner/Intermediate/Advanced/Expert)

**CRITICAL:** Your response MUST be valid JSON that starts with '{{' and ends with '}}'. Do NOT include any explanation, markdown, or extra text. Output ONLY the JSON object, nothing else.

**FINAL REMINDER:**
- The response must be parseable as JSON
- No markdown code blocks (```json or ```)
- No additional text before or after the JSON
- All strings must be properly escaped
- All brackets and quotes must be properly closed
- Follow the exact structure shown in the example"""
        
        return prompt

    def _parse_quiz_response(self, content: str, job_title: str = "") -> Dict[str, Any]:
        """Parse the raw response from the AI model into a structured quiz
        
        Args:
            content: Raw content from the AI model
            job_title: The job title for the quiz (used for fallback title)
            
        Returns:
            Dict containing the parsed quiz data
            
        Raises:
            ValueError: If the content cannot be parsed into a valid quiz
        """
        import json
        import re
        from typing import Any, Dict, List, Optional, Union
        
        def clean_response(text: str) -> str:
            """Clean the response text by removing unwanted characters and formatting."""
            if not text:
                return ""
                
            # Remove any text before the first { or [
            first_char = min(
                [i for i in [text.find('{'), text.find('[')] if i != -1],
                default=0
            )
            if first_char > 0:
                text = text[first_char:]
                
            # Remove markdown code blocks and think blocks
            text = re.sub(r'```(?:json)?\s*([\s\S]*?)\s*```', r'\1', text)
            text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
            
            # Remove any remaining HTML tags
            text = re.sub(r'<[^>]+>', '', text)
            
            # Replace common JSON-breaking patterns
            text = text.replace('\n', ' ').replace('\r', '').strip()
            text = re.sub(r'\s+', ' ', text)  # Normalize whitespace
            
            # Fix common JSON formatting issues
            text = re.sub(r',\s*([}\]])', r'\1', text)  # Trailing commas
            text = re.sub(r'([{\[,])\s*([}\],])', r'\1null\2', text)  # Missing values
            
            return text.strip()
            
        def extract_json_blocks(text: str) -> List[str]:
            """Extract potential JSON blocks from text."""
            # Look for JSON objects
            json_objects = re.findall(r'\{(?:[^{}]|\{(?:[^{}]|\{[^{}]*\})*\})*\}', text)
            
            # Look for JSON arrays
            json_arrays = re.findall(r'\[(?:[^\[\]]|\[(?:[^\[\]]|\[[^\[\]]*\])*\])*\]', text)
            
            # Combine and deduplicate while preserving order
            seen = set()
            result = []
            for item in json_objects + json_arrays:
                if item not in seen:
                    seen.add(item)
                    result.append(item)
                    
            return result
            
        def try_parse_json(json_str: str) -> Optional[Union[Dict, List]]:
            """Attempt to parse a JSON string with multiple fallback strategies."""
            if not json_str or not isinstance(json_str, str):
                return None
                
            json_str = json_str.strip()
            if not json_str:
                return None
                
            # Try direct parsing first
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                pass
                
            # Try fixing common JSON issues
            try:
                # Handle single quotes
                fixed = json_str.replace("'", '"')
                return json.loads(fixed)
            except json.JSONDecodeError:
                pass
                
            # Try removing trailing commas
            try:
                fixed = re.sub(r',\s*([}\]])(?!\s*[{\[])', r'\1', json_str)
                return json.loads(fixed)
            except json.JSONDecodeError:
                pass
                
            # Try wrapping in array if it's not already
            if not (json_str.startswith('[') and json_str.endswith(']')):
                try:
                    return json.loads(f'[{json_str}]')
                except json.JSONDecodeError:
                    pass
                    
            return None
            
        # Clean the input content
        content = content.strip()
        if not content:
            raise ValueError("Empty response from AI model")
            
        # Try to parse the content directly first
        parsed = try_parse_json(content)
        
        # If direct parsing failed, try extracting JSON blocks
        if parsed is None:
            json_blocks = extract_json_blocks(content)
            for block in json_blocks:
                parsed = try_parse_json(block)
                if parsed is not None:
                    break
        
        # If we still don't have a parsed result, try regex extraction
        if parsed is None:
            questions = self.extract_questions_with_regex(content)
            if questions:
                return {
                    "quiz_title": f"QCM - {job_title}" if job_title else "QCM",
                    "job_title": job_title or "",
                    "questions": questions[:20],  # Limit to 20 questions
                    "warning": "Used regex fallback for question extraction"
                }
            else:
                raise ValueError("Failed to extract any questions from the response")
        
        # Handle different parsed structures
        quiz_data = {
            "quiz_title": f"QCM - {job_title}" if job_title else "QCM",
            "job_title": job_title or "",
            "questions": [],
            "warning": None
        }
        
        # Case 1: Response is a list of questions
        if isinstance(parsed, list):
            questions = parsed
        # Case 2: Response is a dictionary with a 'questions' key
        elif isinstance(parsed, dict) and 'questions' in parsed:
            quiz_data['quiz_title'] = parsed.get('quiz_title', quiz_data['quiz_title'])
            quiz_data['job_title'] = parsed.get('job_title', quiz_data['job_title'])
            questions = parsed['questions']
            if not isinstance(questions, list):
                questions = [questions]
        # Case 3: Response is a single question object
        elif isinstance(parsed, dict):
            questions = [parsed]
        else:
            questions = []
        
        # Process and validate questions
        valid_questions = []
        for question in questions:
            if not isinstance(question, dict):
                continue
                
            # Extract and clean question text
            qtext = str(question.get('question', '')).strip()
            if not qtext or len(qtext) < 10:  # Skip empty or very short questions
                continue
                
            # Process options
            options = question.get('options', [])
            if isinstance(options, dict):
                # Convert dict to list, preserving order if possible
                if all(k.upper() in ['A', 'B', 'C', 'D'] for k in options.keys()):
                    options = [options.get(k, '') for k in ['A', 'B', 'C', 'D']]
                else:
                    options = list(options.values())
            elif not isinstance(options, list):
                options = []
                
            # Clean and validate options
            options = [str(opt).strip() for opt in options if str(opt).strip()]
            if len(options) < 2:  # Need at least 2 options
                continue
                
            # Process correct answer
            correct_answer = question.get('correct_answer', 0)
            if isinstance(correct_answer, str):
                # Convert letter to index (A->0, B->1, etc.)
                if correct_answer.upper() in ['A', 'B', 'C', 'D']:
                    correct_answer = ord(correct_answer.upper()) - ord('A')
                else:
                    correct_answer = 0
            
            # Ensure correct_answer is within bounds
            correct_answer = max(0, min(int(correct_answer), len(options) - 1))
            
            # Add the question
            valid_questions.append({
                'id': str(uuid.uuid4()),
                'question': qtext,
                'options': options[:4],  # Max 4 options
                'correct_answer': correct_answer,
                'explanation': str(question.get('explanation', '')).strip(),
                'difficulty': str(question.get('difficulty', 'medium')).lower(),
                'category': str(question.get('category', 'technique')).lower(),
                'skill_related': str(question.get('skill_related', 'General'))
            })
            
            # Limit to 20 questions max
            if len(valid_questions) >= 20:
                break
        
        if not valid_questions:
            # Last resort: try regex extraction
            questions = self.extract_questions_with_regex(content)
            if questions:
                quiz_data['questions'] = questions[:20]
                quiz_data['warning'] = "Used regex fallback for question extraction"
                return quiz_data
            raise ValueError("No valid questions found in the response")
        
        quiz_data['questions'] = valid_questions
        return quiz_data
    
    def extract_questions_with_regex(self, text: str) -> List[Dict[str, Any]]:
        """Extract questions from raw text using regex patterns
        
        Args:
            text: Raw text response from the AI model
            
        Returns:
            List of question dictionaries with standard format
        """
        if not text or not isinstance(text, str):
            return []
        
        questions = []
        
        # Common patterns for extracting questions and answers
        question_patterns = [
            # Pattern 1: Numbered questions with lettered options (1. Question... A) ... B) ...)
            {
                'pattern': r'(?P<number>\d+)\.\s*(?P<question>.+?)\n'
                         r'(?P<options>(?:[A-D][.)]\s*.+?\n){4})'

                         r'(?:[^\w]*(?:Correct|Answer|Réponse|Right|Solution)[^\w]*(?:is|est|:)?[^\w]*(?P<answer>[A-D]))?',
                'option_regex': r'[A-D][.)]\s*(.+)',
                'answer_map': {'A': 0, 'B': 1, 'C': 2, 'D': 3}
            },
            
            # Pattern 2: Questions with markdown-style options
            {
                'pattern': r'(?:Q\d+[:.]?|\*\*Q\d+\*\*)[\s\*]*(?P<question>.+?)\n'
                         r'(?P<options>(?:[-*]\s*[A-D][.)]?\s*.+?\n){4})'

                         r'(?:[^\w]*(?:Correct|Answer|Réponse|Right|Solution)[^\w]*(?:is|est|:)?[^\w]*(?P<answer>[A-D]))?',
                'option_regex': r'[-*]\s*[A-D][.)]?\s*(.+)',
                'answer_map': {'A': 0, 'B': 1, 'C': 2, 'D': 3}
            },
            
            # Pattern 3: JSON-like format (as fallback)
            {
                'pattern': r'(?:question|q)["\s:]+(.+?)["\s]*,'

                         r'[\s\S]*?options[\s\S]*?\['

                         r'([\s\S]*?)\]',
                'option_regex': r'["\'](.+?)["\']',
                'answer_map': {'A': 0, 'B': 1, 'C': 2, 'D': 3}
            }
        ]
        
        for pattern_info in question_patterns:
            try:
                for match in re.finditer(pattern_info['pattern'], text, re.IGNORECASE | re.DOTALL):
                    try:
                        # Extract question text
                        question_text = match.group('question').strip()
                        question_text = re.sub(r'^["\']|["\']$', '', question_text)  # Remove surrounding quotes
                        
                        if not question_text or len(question_text) < 10:  # Skip very short questions
                            continue
                            
                        # Extract options
                        options_text = match.group('options')
                        options = []
                        option_matches = re.finditer(pattern_info['option_regex'], options_text, re.MULTILINE)
                        
                        for opt_match in option_matches:
                            option_text = opt_match.group(1).strip() if len(opt_match.groups()) > 0 else opt_match.group(0).strip()
                            option_text = re.sub(r'^[^\w\s]+', '', option_text)  # Clean up option text
                            if option_text:
                                options.append(option_text)
                        
                        if len(options) < 2:  # Skip if we didn't get enough options
                            continue
                            
                        # Determine correct answer (default to first option if not specified)
                        correct_answer = match.group('answer').upper() if match.groupdict().get('answer') else 'A'
                        correct_index = pattern_info['answer_map'].get(correct_answer, 0)
                        
                        # Skip if this question is too similar to one we already have
                        is_duplicate = False
                        for q in questions:
                            if self._calculate_similarity(question_text, q['question']) > 0.8:
                                is_duplicate = True
                                break
                        if is_duplicate:
                            continue
                        
                        # Ensure we have exactly 4 options (duplicate last option if needed)
                        while len(options) < 4 and len(options) > 0:
                            options.append(options[-1])
                        
                        questions.append({
                            'id': str(uuid.uuid4()),
                            'question': question_text,
                            'options': options[:4],  # Ensure exactly 4 options
                            'correct_answer': min(correct_index, len(options) - 1),  # Ensure index is in range
                            'explanation': 'Auto-generated from text response',
                            'difficulty': 'medium',
                            'category': 'technique',
                            'skill_related': 'General'
                        })
                        
                        # Limit to 20 questions max to avoid excessive processing
                        if len(questions) >= 20:
                            break
                            
                    except (IndexError, KeyError, AttributeError) as e:
                        print(f"Error parsing question with regex: {e}")
                        continue
                
                if questions:  # If we found questions with this pattern, stop trying others
                    break
                    
            except Exception as e:
                print(f"Error processing pattern: {e}")
                continue
                
        return questions
    
    def evaluate_quiz(self, quiz_data: Dict[str, Any], answers: Dict[str, str]) -> Dict[str, Any]:
        """
        Evaluate quiz answers and calculate score
        Args:
            quiz_data: The quiz data structure
            answers: Dictionary mapping question_id to selected_answer
        Returns:
            Dictionary with evaluation results
        """
        total_questions = len(quiz_data["questions"])
        correct_answers = 0
        detailed_results = []
        skill_scores = {}  # skill_name -> {correct: int, total: int}
        skill_mapping = quiz_data.get("skill_mapping", {})
        for i, question in enumerate(quiz_data["questions"], 1):
            question_id = i  # Use the index as question ID
            correct_answer = question["correct_answer"]
            user_answer = answers.get(str(question_id), "")
            is_correct = user_answer.upper() == correct_answer.upper()
            if is_correct:
                correct_answers += 1
            # Skill association
            skill = skill_mapping.get(str(question_id), question.get("skill_related", ""))
            if skill:
                if skill not in skill_scores:
                    skill_scores[skill] = {"correct": 0, "total": 0}
                skill_scores[skill]["total"] += 1
                if is_correct:
                    skill_scores[skill]["correct"] += 1
            detailed_results.append({
                "question_id": question_id,
                "question": question["question"],
                "options": question["options"],
                "user_answer": user_answer,
                "correct_answer": correct_answer,
                "is_correct": is_correct,
                "explanation": question.get("explanation", ""),
                "category": question.get("category", "technique"),
                "skill_related": skill
            })
        # Per-skill scores
        per_skill_percentages = []
        for skill, score_data in skill_scores.items():
            total = score_data["total"]
            correct = score_data["correct"]
            percent = (correct / total * 100) if total > 0 else 0
            per_skill_percentages.append(percent)
        # Final score: average of per-skill percentages (if any), else fallback to total
        if per_skill_percentages:
            final_score = sum(per_skill_percentages) / len(per_skill_percentages)
        else:
            final_score = (correct_answers / total_questions) * 100 if total_questions > 0 else 0
        # Category scores (unchanged)
        category_scores = {}
        for result in detailed_results:
            category = result["category"]
            if category not in category_scores:
                category_scores[category] = {"correct": 0, "total": 0}
            category_scores[category]["total"] += 1
            if result["is_correct"]:
                category_scores[category]["correct"] += 1
        for category in category_scores:
            total = category_scores[category]["total"]
            correct = category_scores[category]["correct"]
            category_scores[category] = (correct / total * 100) if total > 0 else 0
        return {
            "total_score": final_score,
            "correct_answers": correct_answers,
            "total_questions": total_questions,
            "category_scores": category_scores,
            "detailed_results": detailed_results,
            "quiz_title": quiz_data["quiz_title"],
            "job_title": quiz_data["job_title"],
            "per_skill_scores": skill_scores
        } 
    
    def _randomize_and_deduplicate_quiz(self, quiz_data: Dict[str, Any], past_questions: List[str]) -> Dict[str, Any]:
        """
        Randomize questions and options, and remove duplicates
        """
        if not quiz_data or "questions" not in quiz_data:
            return quiz_data
        
        questions = quiz_data["questions"]
        if not questions:
            return quiz_data
        
        # Remove duplicates based on question text
        seen_questions = set()
        unique_questions = []
        
        for question in questions:
            if not isinstance(question, dict) or "question" not in question:
                continue
            
            question_text = question["question"].strip().lower()
            
            # Check if this question is too similar to past questions
            is_duplicate = False
            for past_q in past_questions:
                if self._calculate_similarity(question_text, past_q.strip().lower()) > 0.8:
                    is_duplicate = True
                    break
            
            # Check if this question is too similar to already added questions
            for seen_q in seen_questions:
                if self._calculate_similarity(question_text, seen_q) > 0.8:
                    is_duplicate = True
                    break
            
            if not is_duplicate and question_text not in seen_questions:
                seen_questions.add(question_text)
                unique_questions.append(question)
        
        # Randomize question order
        random.shuffle(unique_questions)
        
        # Randomize options for each question
        for question in unique_questions:
            if "options" in question and isinstance(question["options"], dict):
                options = question["options"]
                correct_answer = question.get("correct_answer", "A")
                
                # Get option keys and values
                option_keys = list(options.keys())
                option_values = list(options.values())
                
                # Shuffle the values
                random.shuffle(option_values)
                
                # Create new options dict with shuffled values
                new_options = {}
                for i, key in enumerate(option_keys):
                    new_options[key] = option_values[i]
                
                # Update correct answer to match the new position
                if correct_answer in options:
                    old_value = options[correct_answer]
                    for key, value in new_options.items():
                        if value == old_value:
                            question["correct_answer"] = key
                            break
                
                question["options"] = new_options
        
        quiz_data["questions"] = unique_questions
        
        # Assign proper question IDs after randomization
        for i, question in enumerate(quiz_data["questions"], 1):
            question["id"] = i
        
        return quiz_data
    
    def _ensure_balanced_skill_distribution(self, quiz_data: Dict[str, Any], skills: List[str]) -> Dict[str, Any]:
        """
        Ensure questions are balanced across different skills when multiple skills are provided
        """
        if not quiz_data or "questions" not in quiz_data or len(skills) <= 1:
            return quiz_data
        
        questions = quiz_data["questions"]
        if not questions:
            return quiz_data
        
        # Count questions per skill
        skill_counts = {skill: 0 for skill in skills}
        skill_questions = {skill: [] for skill in skills}
        
        for question in questions:
            if not isinstance(question, dict) or "question" not in question:
                continue
            
            question_text = question["question"].lower()
            
            # Find which skill this question belongs to
            assigned_skill = None
            for skill in skills:
                if skill.lower() in question_text:
                    assigned_skill = skill
                    break
            
            if assigned_skill:
                skill_counts[assigned_skill] += 1
                skill_questions[assigned_skill].append(question)
            else:
                # If no specific skill found, assign to the skill with least questions
                min_skill = min(skill_counts, key=skill_counts.get)
                skill_counts[min_skill] += 1
                skill_questions[min_skill].append(question)
        
        # Rebalance if needed
        target_per_skill = len(questions) // len(skills)
        balanced_questions = []
        
        for skill in skills:
            skill_qs = skill_questions[skill]
            if len(skill_qs) < target_per_skill:
                # Add more questions for this skill
                needed = target_per_skill - len(skill_qs)
                # Generate additional questions for this skill
                additional_quiz = self.generate_quiz(
                    job_title=quiz_data.get("job_title", "Job"),
                    required_skills=[],
                    candidate_skills=[skill],
                    num_questions=needed,
                    past_questions=[],
                    use_expert_prompt=True
                )
                if additional_quiz and "questions" in additional_quiz:
                    skill_qs.extend(additional_quiz["questions"][:needed])
            
            balanced_questions.extend(skill_qs)
        
        # Shuffle the final balanced questions
        random.shuffle(balanced_questions)
        
        # Update question IDs
        for i, question in enumerate(balanced_questions, 1):
            question["id"] = i
        
        quiz_data["questions"] = balanced_questions
        return quiz_data
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate similarity between two texts using simple word overlap
        """
        if not text1 or not text2:
            return 0.0
        
        # Clean and split texts
        words1 = set(re.findall(r'\w+', text1.lower()))
        words2 = set(re.findall(r'\w+', text2.lower()))
        
        if not words1 or not words2:
            return 0.0
        
        # Calculate Jaccard similarity
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union if union > 0 else 0.0 