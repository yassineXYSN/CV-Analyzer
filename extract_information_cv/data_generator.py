import os
from huggingface_hub import InferenceClient
from dotenv import load_dotenv
import json
load_dotenv()

def generate_summary(client,text):
    completion = client.chat.completions.create(
            model="deepseek-ai/DeepSeek-R1-0528",
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
                        here is the CV text: """ + text
                }
            ],
        )
    msg = completion.choices[0].message.content.strip()
    return  msg[msg.find("</think>")+9:]

def generate_json(client,text):
    completion = client.chat.completions.create(
            model="deepseek-ai/DeepSeek-R1-0528",
            messages=[
                {
                    "role": "user",
                    "content": 
                    """
                    Extract the following structured information from the provided text and return it as a JSON object. Only extract the relevant information, and do not include any extra comments or explanations. The JSON format should follow this exact structure:

                    {
                    "name": "",
                    "title": "",
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
                    "skills": [],
                    "hobbies": []
                    }
                    Please respond only with the JSON output, no extra text or explanation.

                    if any of the fields are not present in the text, put unvailable in the field.
                    Here is the text:

                     """ + text 
                }
            ],
        )
    msg = completion.choices[0].message.content.strip()
    msg =  msg[msg.find("</think>")+9:]
    try:
        data = json.loads(msg)
    except json.JSONDecodeError as e:
        print("Error parsing JSON:", e)
    return data

def intialize_client():
    client = InferenceClient(
        provider="novita",
        api_key=os.getenv("HF_TOKEN"),
        timeout=300,
    )
    return client
