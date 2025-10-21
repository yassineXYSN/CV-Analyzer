import json
import requests
from testfull import full_transcription_and_emotion_analysis


def extract_conversation_from_json(file_path):
    """
    Extracts conversation text from a JSON file with emotion analysis data.
    
    Args:
        file_path (str): Path to the JSON file
        
    Returns:
        str: The complete conversation as a single string
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
        
        conversation_parts = []
        
        for entry in data:
            speaker = entry.get('speaker', 'Unknown Speaker')
            text = entry.get('text', '')
            emotion = entry.get('emotion', 'neutral')
            conversation_parts.append(f"{speaker}({emotion}): {text}")
        
        conversation = '\n'.join(conversation_parts)
        return conversation
        
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
        return ""
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON format in file '{file_path}'.")
        return ""
    except Exception as e:
        print(f"Error reading file: {e}")
        return ""

# Example usage
def clean_conversation(audio1, audio2, video):
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
    return response.text


print(clean_conversation(r"C:\Users\yassine\Documents\Zoom\2025-10-12 18.10.27 Mouhamed Yassine Chtourou's Zoom Meeting\Audio Record\audioMouhamedYassineC11624140658.m4a", r"C:\Users\yassine\Documents\Zoom\2025-10-12 18.10.27 Mouhamed Yassine Chtourou's Zoom Meeting\Audio Record\audioYoussefDammak21624140658.m4a", r"C:\Users\yassine\Documents\Zoom\2025-10-12 18.10.27 Mouhamed Yassine Chtourou's Zoom Meeting\video1624140658.mp4"))