import os
import requests
from urllib.parse import urlparse

def download_fer2013_model():
    """Download a pre-trained FER2013 emotion detection model"""
    
    # Create models directory
    if not os.path.exists('models'):
        os.makedirs('models')
    
    # Model URLs (you can use any of these pre-trained models)
    model_urls = [
        {
            'name': 'fer2013_mini_XCEPTION.102-0.66.hdf5',
            'url': 'https://github.com/oarriaga/face_classification/raw/master/trained_models/emotion_models/fer2013_mini_XCEPTION.102-0.66.hdf5',
            'description': 'Mini XCEPTION model trained on FER2013'
        },
        {
            'name': 'fer2013_big_XCEPTION.54-0.66.hdf5', 
            'url': 'https://github.com/oarriaga/face_classification/raw/master/trained_models/emotion_models/fer2013_big_XCEPTION.54-0.66.hdf5',
            'description': 'Big XCEPTION model trained on FER2013'
        }
    ]
    
    print("Available pre-trained emotion detection models:")
    for i, model in enumerate(model_urls):
        print(f"{i+1}. {model['name']} - {model['description']}")
    
    choice = input("Enter model number to download (1-2): ").strip()
    
    try:
        model_idx = int(choice) - 1
        if 0 <= model_idx < len(model_urls):
            model = model_urls[model_idx]
            model_path = f"models/{model['name']}"
            
            if os.path.exists(model_path):
                print(f"Model {model['name']} already exists!")
                return model_path
            
            print(f"Downloading {model['name']}...")
            response = requests.get(model['url'], stream=True)
            response.raise_for_status()
            
            with open(model_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            print(f"Successfully downloaded {model['name']}")
            return model_path
        else:
            print("Invalid choice!")
            return None
            
    except (ValueError, requests.RequestException) as e:
        print(f"Error downloading model: {e}")
        return None

if __name__ == "__main__":
    download_fer2013_model()
