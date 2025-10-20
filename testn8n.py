import requests

payload = {
    "to": "yassinechtourou03@gmail.com",
    "subject": "subject",
    "html": "html_content",
    "text": "text_content",
    "wait": 60
}

url = "https://gaxopin551.app.n8n.cloud/webhook/send-emails"

try:
    response = requests.post(url, json=payload, timeout=2)
    print("Request sent successfully:", response.status_code)
except requests.exceptions.Timeout:
    print("✅ Request timed out (expected) — continuing without waiting.")
except requests.exceptions.RequestException as e:
    print("⚠️ Request failed:", e)