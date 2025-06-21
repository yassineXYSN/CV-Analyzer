import os
from huggingface_hub import InferenceClient
from dotenv import load_dotenv
import json
load_dotenv()

def generate_summary(text,img_text):
    client = InferenceClient(
        provider="novita",
        api_key=os.getenv("SUMMARY_DATA_GENERATOR_TOKEN"),
        timeout=300,
    )
    if isinstance(img_text, list):
        img_text = "\n".join(img_text)
    completion = client.chat.completions.create(
            model="deepseek-ai/DeepSeek-R1-0528-Qwen3-8B",
            messages=[
                {
                    "role": "user",
                    "content": 
                    """
                     You are an expert HR recruiter analyzing CVs to decide if a candidate is a good fit for demanding roles. Analyze the following CV critically and generate a complete, honest, no-fluff summary paragraph for HR use.

                        ⚠ Important:

                        Do NOT omit any potentially relevant information.

                        Include both strengths and weaknesses, gaps, irrelevant experience, job hopping, achievements, soft skills, hard skills, certifications, education, language, projects, leadership roles, etc.

                        Be brutally honest: If experience is weak, outdated, or irrelevant — say it.

                        Write in  a paragraph.

                        Do NOT include any personal information like name, contact details,birthdate , or location.
                        Do NOT include any subjective opinions or comments.
                        Do NOT include any information that is not present in the CV.
                        here is the CV text: """ + text + """
                        if you find something you can add from this you can add it (NB: this is the text parsed from the images it can be a bit glitchy or it might not cantain any information): """ + img_text
                }
            ],
        )
    msg = completion.choices[0].message.content.strip()
    return  msg[msg.find("</think>")+9:]

def generate_json(text):
    client = InferenceClient(
        provider="novita",
        api_key=os.getenv("JSON_DATA_GENERATOR_TOKEN"),
        timeout=600,
    )
    completion = client.chat.completions.create(
            model="deepseek-ai/DeepSeek-R1-0528-Qwen3-8B",
            messages=[
                {
                    "role": "user",
                    "content": 
                    """
                    Extract the following structured information from the provided text and return it as a JSON object. Only extract the relevant information, and do not include any extra comments or explanations. The JSON format should follow this exact structure:

                    {
                    "name": "",
                    "title": "",
                    yearsOfExperience: "",
                    "contact": {
                        "email": "",
                        "phone": "",
                        "linkedin": "",
                        "address": ""
                    },
                    "profile": "",
                    "education": [
                        {
                        "institution": "",
                        "degree": "",
                        "years": ""
                        }
                    ],
                    "languages": [],
                    "certificates": [],
                    "skills": []
                    }
                    Please respond only with the JSON output, no extra text or explanation.

                    if any of the fields are not present in the text, put unvailable in the field.
                    Here is the text:

                     """ + text 
                }
            ],
        )
    msg = completion.choices[0].message.content.strip()
    return  json.loads(msg[msg.find("</think>")+9:])

def generate_good_points(text):
    client = InferenceClient(
        provider="novita",
        api_key=os.getenv("JSON_DATA_GENERATOR_TOKEN"),
        timeout=300,
    )
    completion = client.chat.completions.create(
            model="deepseek-ai/DeepSeek-R1-0528-Qwen3-8B",
            messages=[
                {
                    "role": "user",
                    "content": 
                    """
                    You are an expert HR professional. Analyze the following CV text and extract only the strong points of the candidate. Focus on skills, achievements, education, certifications, work experience, and any other strengths that would make this candidate a good fit for a job.

                    Return the strong points as a bullet-point list, without adding extra comments or interpretation.

                    CV Text:""" + text
                }
            ],
        )
    msg = completion.choices[0].message.content.strip()
    return  msg[msg.find("</think>")+9:]

def generate_weak_points(text):
    client = InferenceClient(
        provider="novita",
        api_key=os.getenv("JSON_DATA_GENERATOR_TOKEN"),
        timeout=300,
    )
    completion = client.chat.completions.create(
            model="deepseek-ai/DeepSeek-R1-0528-Qwen3-8B",
            messages=[
                {
                    "role": "user",
                    "content": 
                    """
                    *You are an expert HR professional and CV reviewer. Analyze the following CV text and extract only the weak points, missing information, or areas that could be improved.

                    Focus on things like missing skills, lack of achievements, employment gaps, vague descriptions, irrelevant details, or poor formatting if present.

                    Return the weaknesses as a bullet-point list, clearly and objectively, without adding extra comments or explanations.

                    CV Text: """ + text
                }
            ],
        )
    msg = completion.choices[0].message.content.strip()
    return  msg[msg.find("</think>")+9:]

def generate_categorie_scores(text):
    client = InferenceClient(
        provider="novita",
        api_key=os.getenv("JSON_DATA_GENERATOR_TOKEN"),
        timeout=300,
    )
    completion = client.chat.completions.create(
            model="deepseek-ai/DeepSeek-R1-0528-Qwen3-8B",
            messages=[
                {
                    "role": "user",
                    "content": 
                    """
                    "You are an expert HR professional and recruiter. Analyze the following CV text and assign a score (from 0 to 100) for each of the following categories:

                    Work Experience (Relevance, achievements, responsibilities)

                    Skills & Technical Expertise (Hard skills, technical abilities, proficiency)

                    Education (Level of education, relevance to job roles)

                    Certifications & Training (Relevance and value of certifications or courses)

                    Soft Skills & Leadership (Communication, leadership, teamwork)

                    Overall Structure & Presentation (Clarity, organization, grammar, formatting)

                    Provide the result in the following JSON format:

                    json
                    Copy
                    Edit
                    {
                    "Work Experience": score,
                    "Skills & Technical Expertise": score,
                    "Education": score,
                    "Certifications & Training": score,
                    "Soft Skills & Leadership": score,
                    "Overall Structure & Presentation": score
                    }
                    CV Text:""" + text
                }
            ],
        )
    msg = completion.choices[0].message.content.strip()
    return  msg[msg.find("</think>")+9:]

def generate_improvements(text,strong,weak,scores):
    client = InferenceClient(
        provider="novita",
        api_key=os.getenv("JSON_DATA_GENERATOR_TOKEN"),
        timeout=300,
    )
    completion = client.chat.completions.create(
            model="deepseek-ai/DeepSeek-R1-0528-Qwen3-8B",
            messages=[
                {
                    "role": "user",
                    "content": 
                    """
                    "You are an expert CV reviewer. Below is a CV text along with:

                    A list of its strong points

                    A list of its weak points

                    Evaluation scores across different categories

                    Based on this information, provide a clear, actionable list of key improvements the candidate should make to strengthen their CV. Focus on improving weak points, increasing the scores, and enhancing overall presentation.
                    Return the improvements as a concise bullet-point list. Avoid generic advice; focus on specific improvements based on this particular CV.

                    CV Text:
                    """ + text + """

                    Strong Points:
                    """ + strong + """

                    Weak Points:
                    """ + weak +  """

                    Scores:

                    json
                    """ + scores + """
                    Generate: → Bullet-point list of specific, actionable key improvements. """
                }
            ],
        )
    msg = completion.choices[0].message.content.strip()
    return  msg[msg.find("</think>")+9:]