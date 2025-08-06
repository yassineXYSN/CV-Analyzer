import os
import requests
import json
import random
import uuid
import re
import datetime
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from huggingface_hub import InferenceClient

load_dotenv()

# Remove old API_URL and headers
# API_URL = "https://router.huggingface.co/novita/v3/openai/chat/completions"
# headers = {
#     "Authorization": f"Bearer {os.environ.get('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', '')}",
# }

# Use the provided access token directly
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
    
    def generate_quiz(self, job_title: str, required_skills: List[str], candidate_skills: List[str], num_questions: int = 10, past_questions: Optional[list] = None, use_expert_prompt: bool = False) -> Dict[str, Any]:
        """
        Generate a QCM quiz based on job requirements and candidate skills
        Args:
            job_title: The job title/position
            required_skills: List of skills required for the job
            candidate_skills: List of skills the candidate has
            num_questions: Number of questions to generate
            past_questions: List of previously used questions to avoid (optional)
            use_expert_prompt: If True, use the expert prompt; else use the default prompt
        Returns:
            Dictionary containing quiz data
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

**Output Format (JSON array):**
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

**Output Format (JSON array):**
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

    def _parse_quiz_response(self, content: str, job_title: str) -> Dict[str, Any]:
        import json
        import re
        import logging

        def clean_response(text):
            # Remove <think>...</think> blocks
            text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
            # Remove markdown code blocks
            text = re.sub(r'```json|```', '', text)
            # Remove everything before the first { or [
            first_brace = min([i for i in [text.find('{'), text.find('[')] if i != -1], default=0)
            if first_brace > 0:
                text = text[first_brace:]
            return text.strip()

        def extract_json_block(text):
            text = clean_response(text)
            # Try to find a JSON object
            obj_match = re.search(r'\{[\s\S]*\}', text)
            if obj_match:
                return obj_match.group(0)
            # Try to find a JSON array
            arr_match = re.search(r'\[[\s\S]*\]', text)
            if arr_match:
                return arr_match.group(0)
            raise ValueError("No JSON object or array found in model response")

        def repair_json_string(json_str):
            # Remove <think>...</think> and markdown
            json_str = re.sub(r'<think>.*?</think>', '', json_str, flags=re.DOTALL)
            json_str = json_str.replace('```json', '').replace('```', '')
            # Replace smart quotes and single quotes with double quotes
            json_str = json_str.replace('“', '"').replace('”', '"').replace("‘", "'").replace("’", "'")
            json_str = re.sub(r"'", '"', json_str)
            # Remove trailing commas
            json_str = re.sub(r',\s*([}\]])', r'\1', json_str)
            # Remove any non-JSON lines (lines that don't start with [ or { or ")
            json_str = '\n'.join([line for line in json_str.splitlines() if line.strip().startswith(('"', '{', '[', ']', '}'))])
            # Attempt to close unterminated arrays/objects
            open_braces = json_str.count('{')
            close_braces = json_str.count('}')
            if open_braces > close_braces:
                json_str += '}' * (open_braces - close_braces)
            open_brackets = json_str.count('[')
            close_brackets = json_str.count(']')
            if open_brackets > close_brackets:
                json_str += ']' * (open_brackets - close_brackets)
            json_str = json_str.strip()
            return json_str

        def extract_questions_with_regex(text):
            # More robust regex patterns to extract questions
            questions = []
            
            # Pattern 1: Look for question blocks with options
            question_patterns = [
                r'\{[^\{\}]*?"question"\s*:\s*"[^"]*".*?"options"\s*:\s*\{[^\}]*\}.*?\}',
                r'\{[^\{\}]*?"question"\s*:\s*"[^"]*".*?"correct_answer"\s*:\s*"[ABCD]".*?\}',
                r'"question"\s*:\s*"([^"]*)"[^}]*"options"\s*:\s*\{([^\}]*)\}[^}]*"correct_answer"\s*:\s*"([ABCD])"'
            ]
            
            for pattern in question_patterns:
                matches = re.findall(pattern, text, re.DOTALL | re.IGNORECASE)
                for match in matches:
                    try:
                        if isinstance(match, tuple):
                            # Handle tuple matches
                            question_text = match[0] if len(match) > 0 else ""
                            options_text = match[1] if len(match) > 1 else ""
                            correct_answer = match[2] if len(match) > 2 else "A"
                            
                            # Parse options
                            options = {}
                            option_matches = re.findall(r'"([ABCD])"\s*:\s*"([^"]*)"', options_text)
                            for opt_key, opt_val in option_matches:
                                if opt_val and opt_val.strip():
                                    options[opt_key] = opt_val.strip()
                            
                            # Ensure we have 4 options
                            for key in ["A", "B", "C", "D"]:
                                if key not in options:
                                    options[key] = f"Option {key}"
                            
                            if question_text and len(options) == 4:
                                questions.append({
                                    "question": question_text,
                                    "options": options,
                                    "correct_answer": correct_answer
                                })
                        else:
                            # Handle string matches
                            repaired = repair_json_string(match)
                            q = json.loads(repaired)
                            if "question" in q and q["question"].strip():
                                # Ensure options exist
                                if "options" not in q or not isinstance(q["options"], dict) or len(q["options"]) != 4:
                                    q["options"] = {"A": "Option A", "B": "Option B", "C": "Option C", "D": "Option D"}
                                if "correct_answer" not in q or q["correct_answer"] not in q["options"]:
                                    q["correct_answer"] = "A"
                                questions.append(q)
                    except Exception as e:
                        continue
            
            # Pattern 2: Look for simple question-answer pairs
            simple_pattern = r'(\d+\.\s*[^?]+\?)\s*([A-D]\.\s*[^\n]+)\s*([A-D]\.\s*[^\n]+)\s*([A-D]\.\s*[^\n]+)\s*([A-D]\.\s*[^\n]+)'
            simple_matches = re.findall(simple_pattern, text, re.DOTALL)
            
            for match in simple_matches:
                try:
                    question_text = match[0].strip()
                    options = {}
                    for i, option in enumerate(match[1:5]):
                        if option.strip():
                            options[chr(65 + i)] = option.strip()
                    
                    # Ensure we have 4 options
                    for key in ["A", "B", "C", "D"]:
                        if key not in options:
                            options[key] = f"Option {key}"
                    
                    if question_text and len(options) == 4:
                        questions.append({
                            "question": question_text,
                            "options": options,
                            "correct_answer": "A"  # Default to A
                        })
                except Exception as e:
                    continue
            
            return questions

        quiz_data = {
            "quiz_title": f"QCM - {job_title}",
            "job_title": job_title,
            "questions": [],
            "warning": None
        }
        warning_msgs = []
        try:
            json_str = extract_json_block(content)
            try:
                parsed = json.loads(json_str)
            except Exception:
                # Try to repair and parse again
                json_str = repair_json_string(json_str)
                parsed = json.loads(json_str)
            # If it's a list, wrap in object
            if isinstance(parsed, list):
                parsed = {
                    "quiz_title": f"QCM - {job_title}",
                    "job_title": job_title,
                    "questions": parsed
                }
            if "questions" not in parsed or not parsed["questions"]:
                warning_msgs.append("No questions found after parsing. Raw response may be invalid.")
            else:
                # Fill missing fields with placeholders
                all_questions = []
                for question in parsed["questions"]:
                    # Fix question text - be more lenient
                    qtext = question.get("question", "")
                    if not qtext or str(qtext).strip() == "":
                        continue  # skip completely empty questions
                    
                    # Clean up question text - remove trailing incomplete sentences
                    qtext = str(qtext).strip()
                    if qtext.endswith("...") or qtext.endswith(".") == False:
                        # Try to complete the question or use as is
                        if len(qtext) > 10:  # If question has substantial content, keep it
                            pass
                        else:
                            continue
                    
                    # Fix options - be more lenient
                    valid_options = {}
                    options = question.get("options", {})
                    
                    # Handle different option formats
                    if isinstance(options, dict):
                        for key in ["A", "B", "C", "D"]:
                            val = options.get(key, "")
                            if val and str(val).strip():
                                # Clean up option text
                                clean_val = str(val).strip()
                                if clean_val and clean_val not in ["...", "option a", "option b", "option c", "option d"]:
                                    valid_options[key] = clean_val
                    elif isinstance(options, list) and len(options) >= 4:
                        # Handle array format
                        for i, val in enumerate(options[:4]):
                            if val and str(val).strip():
                                valid_options[chr(65 + i)] = str(val).strip()
                    
                    # If we don't have 4 valid options, create placeholder options
                    if len(valid_options) < 4:
                        for key in ["A", "B", "C", "D"]:
                            if key not in valid_options:
                                valid_options[key] = f"Option {key}"
                    
                    # Ensure we have exactly 4 options
                    if len(valid_options) == 4:
                        question["options"] = valid_options
                        # Fix correct_answer
                        if "correct_answer" not in question or question["correct_answer"] not in valid_options:
                            question["correct_answer"] = "A"
                        all_questions.append(question)
                
                quiz_data["questions"] = all_questions
        except Exception as e:
            warning_msgs.append(f"Error parsing quiz response: {e}")
            # Fallback: try to extract and repair individual questions
            questions = extract_questions_with_regex(content)
            if questions:
                quiz_data["questions"] = questions
                warning_msgs.append("Quiz generated from regex extraction due to parsing error.")
            else:
                warning_msgs.append("No questions found after all attempts. Returning empty quiz.")
        if warning_msgs:
            quiz_data["warning"] = " ".join(warning_msgs)
        
        # If no questions were generated, add a placeholder question
        if not quiz_data["questions"]:
            quiz_data["questions"] = [{
                "id": 1,
                "question": f"Question placeholder pour {job_title}",
                "options": {
                    "A": "Option A",
                    "B": "Option B", 
                    "C": "Option C",
                    "D": "Option D"
                },
                "correct_answer": "A",
                "explanation": "Question générée automatiquement en raison d'une erreur de génération.",
                "category": "technique",
                "skill_related": job_title
            }]
            if quiz_data["warning"]:
                quiz_data["warning"] += " Une question placeholder a été ajoutée."
            else:
                quiz_data["warning"] = "Aucune question valide générée. Une question placeholder a été ajoutée."
        
        return quiz_data
    
    def _fallback_quiz(self, job_title):
        # You can customize this fallback quiz as needed
        return {
            "quiz_title": f"QCM - {job_title}",
            "job_title": job_title,
            "questions": [
                {
                    "id": 1,
                    "question": "What is Python?",
                    "options": {"A": "A snake", "B": "A programming language", "C": "A car", "D": "A fruit"},
                    "correct_answer": "B",
                    "explanation": "Python is a popular programming language.",
                    "category": "technique",
                    "skill_related": "Python"
                },
                {
                    "id": 2,
                    "question": "Which HTML tag is used for the largest heading?",
                    "options": {"A": "<h6>", "B": "<heading>", "C": "<h1>", "D": "<head>"},
                    "correct_answer": "C",
                    "explanation": "<h1> is the largest heading tag.",
                    "category": "technique",
                    "skill_related": "HTML"
                }
            ]
        }
    
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