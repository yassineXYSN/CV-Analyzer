import json
import requests


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
if __name__ == "__main__":
    # Replace with your actual file path
    file_path = "conversation_emotion_analysis.json"
    
    # Extract conversation
    conversation_text = extract_conversation_from_json(file_path)
    
    # Print the conversation
    print("Extracted Conversation:")
    print("=" * 50)
    print(conversation_text)
    
    url = "https://gaxopin551.app.n8n.cloud/webhook-test/clean-conv"
    
    response = requests.post(url, json=conversation_text)
    
    print("Status Code:", response.status_code)
    print("Response:", response.text)