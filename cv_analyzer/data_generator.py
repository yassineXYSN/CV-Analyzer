import os
from huggingface_hub import InferenceClient

def generate_summary(client,text):
    completion = client.chat.completions.create(
            model="deepseek-ai/DeepSeek-R1-0528",
            messages=[
                {
                    "role": "user",
                    "content": "Generate a summary containing every important information from this text for a job interview :"+text,
                }
            ],
        )
    msg = completion.choices[0].message.content.strip()
    return  msg[msg.find("</think>")+9:]



def intialize_client():
    client = InferenceClient(
        provider="novita",
        api_key=os.getenv("HF_TOKEN"),
    )
    return client
