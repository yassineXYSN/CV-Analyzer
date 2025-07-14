import requests
import time

API_KEY = "962e317e6e204907ac73857fafa4cdce"
file_path = "8b4c2a73-8e25-4da3-a1c2-c936eb6ee06a.webm"

headers = {'authorization': API_KEY}

# Étape 1 : Uploader le fichier
def upload_audio(path):
    with open(path, 'rb') as f:
        response = requests.post(
            'https://api.assemblyai.com/v2/upload',
            headers=headers,
            data=f
        )
    if response.status_code != 200:
        raise Exception(f"Erreur upload: {response.status_code} - {response.text}")
    url = response.json()['upload_url']
    # Ajouter extension selon ton fichier local, par exemple .weba ou mieux .webm
    if not url.endswith(('.mp3', '.wav', '.webm', '.weba')):
        url += '.weba'  # ou .webm si possible
    return url


# Étape 2 : Demander la transcription avec analyse des émotions
def request_transcription(audio_url):
    transcript_request = {
        "audio_url": audio_url,
        "sentiment_analysis": True,
        "auto_punctuation": True,
        "language_detection": True
    }
    response = requests.post(
        'https://api.assemblyai.com/v2/transcript',
        json=transcript_request,
        headers=headers
    )
    resp_json = response.json()
    print("Status code:", response.status_code)
    print("Response JSON:", resp_json)
    if 'id' not in resp_json:
        raise Exception(f"Erreur API transcription: {resp_json.get('error', 'clé id absente')}")
    return resp_json['id']

# Étape 3 : Vérifier l’état et récupérer les résultats
def get_transcription_result(transcript_id):
    url = f"https://api.assemblyai.com/v2/transcript/{transcript_id}"
    while True:
        response = requests.get(url, headers=headers)
        data = response.json()
        if data['status'] == 'completed':
            print("✅ Transcription :", data['text'])
            print("\n🎭 Émotions détectées :")
            for result in data.get("sentiment_analysis_results", []):
                print(f" - \"{result['text']}\" ➤ {result['sentiment']}")
            break
        elif data['status'] == 'error':
            print("❌ Erreur :", data['error'])
            break
        else:
            print("⏳ En attente... (status =", data['status'], ")")
            time.sleep(5)

# ---- Lancer le test
upload_url = upload_audio(file_path)
print("✅ Audio uploadé :", upload_url)

transcript_id = request_transcription(upload_url)
print("🆔 ID de transcription :", transcript_id)

get_transcription_result(transcript_id)
