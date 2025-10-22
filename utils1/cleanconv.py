import json
import requests
import os
import sys
from sqlalchemy.orm import Session, joinedload
from utils1.transfull import full_transcription_and_emotion_analysis

# Add the parent directory to the path so we can import database modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from databasehr.models import Application, Job, ProfileCandidat, JobSkill
from databasehr.database import SessionLocal


def clean_conversation(audio1, audio2, video, application_id):
    # Replace with your actual file path    
    # Extract conversation
    conversation = full_transcription_and_emotion_analysis(audio1, audio2, video, "HR", "Candidate")
    # Print the conversation
    print("Extracted Conversation:")
    print("=" * 50)
    print(conversation)
    print(type(conversation))
    conversation_text = "\n".join(
        [f"{entry['speaker']}: {entry['text']}" for entry in conversation]
    )
    url = "https://gaxopin551.app.n8n.cloud/webhook/clean-conv"
    
    response = requests.post(url, json=conversation_text)
    
    print("Status Code:", response.status_code)
    response_text = response.text
    
    

    final_return = analyze_conversation_detailed(response_text, application_id)
    
    print("Final Return:")
    print(final_return)
    
    # Return both the conversation and the analysis
    combined_result = {
        "conversation": conversation,
        "analysis": final_return
    }
    
    print("Combined Result:")
    print(combined_result)
    return combined_result

    

def analyze_conversation_detailed(conversation, application_id):
    db = SessionLocal()
    try:
        # Fetch application with candidate profile and job info
        App = db.query(Application).options(
            joinedload(Application.job).joinedload(Job.company),
            joinedload(Application.candidate_profile).joinedload(ProfileCandidat.contact)
        ).filter(Application.id == application_id).first() 
        
        skills = (
            db.query(JobSkill)
            .filter(JobSkill.job_id == App.job.id)
            .all()
        )

        # Convert to list of dicts or just names
        skills_list = [
            {
                "skill_name": skill.skill_name,
                "skill_level": skill.skill_level,
                "is_required": skill.is_required
            }
            for skill in skills
        ]

        if not App:
            print(f"Application {application_id} not found")
            return []
        
        print("Application fetched:")
        print(f"  - Application ID: {App.id}")
        print(f"  - Status: {App.status}")
        
        if App.job:
            print(f"  - Job Title: {App.job.title}")
            print(f"  - Company: {App.job.company.company_name if App.job.company else 'N/A'}")
        
        if App.candidate_profile:
            print(f"  - Candidate Name: {App.candidate_profile.name}")
            print(f"  - Candidate Email: {App.candidate_profile.contact.email if App.candidate_profile.contact else 'N/A'}")
            url = "https://gaxopin551.app.n8n.cloud/webhook/analyze-conv"
            
            payload = {
                "conversation": conversation,
                "job" : {
                    "title": App.job.title if App.job else "",
                    "description": App.job.description if App.job else "",
                    "requirements": App.job.requirements if App.job else "",
                    "responsibilities": App.job.responsibilities if App.job else "",
                    "skills": skills_list
                },
                "candidate": {
                    "name": App.candidate_profile.name if App.candidate_profile else "",
                    "title": App.candidate_profile.title if App.candidate_profile else "",
                    "experience": App.candidate_profile.yearOfExperience if App.candidate_profile else "",
                    "education": App.candidate_profile.education if App.candidate_profile else {},
                    "languages": App.candidate_profile.languages if App.candidate_profile else {},
                    "certificates": App.candidate_profile.certificates if App.candidate_profile else {},
                    "skills": App.candidate_profile.skills if App.candidate_profile else {},
                }
                
            }
            
            response = requests.post(url, json=payload)
            print("Status Code 2:", response.status_code)
            response_text = response.text
            print("Response text:", response_text)
            
            try:
                # Parse the JSON response first
                response_data = json.loads(response_text)
                print("Parsed response data:", response_data)
                
                # Access the content from the parsed JSON
                content = response_data[0]['choices'][0]['message']['content']
                print("Content:", content)
                
                # Parse the content if it's a JSON string
                if isinstance(content, str):
                    content = json.loads(content)
                
                # Select only the requested keys
                result = {
                    key: content.get(key, '')
                    for key in ['Overall_Recommendation', 'Strengths', 'Weaknesses', 'Skills_fit', 'Behavioral', 'Final_verdict']
                }
                
                print("Final result:", result)
                return result
                
            except (json.JSONDecodeError, KeyError, IndexError) as e:
                print(f"Error parsing response: {e}")
                print(f"Response text was: {response_text}")
                return []


        
    except Exception as e:
        print(f"Error fetching application data: {e}")
        return []
    finally:
        db.close()