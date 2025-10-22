import json
import requests
from utils1.transfull import full_transcription_and_emotion_analysis


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

