import requests

# The webhook URL from n8n
url = "https://yassine13.app.n8n.cloud/webhook-test/cv-upload"
print("Sending file to n8n...")

# Path to the PDF CV file
file_path = r"C:\Users\yassine\Documents\GitHub\Training\uploads\CV (2).pdf"

# Send file as multipart/form-data
with open(file_path, "rb") as f:
    
    files = {"CV": (r"C:\Users\yassine\Documents\GitHub\Training\uploads\CV (2).pdf", f, "application/pdf")}
    response = requests.post(url, files=files)

print("Status Code:", response.status_code)
print("Response:", response.text)
