import os
from huggingface_hub import InferenceClient

def cleantext(client,text):
    completion = client.chat.completions.create(
            model="deepseek-ai/DeepSeek-R1-0528",
            messages=[
                {
                    "role": "user",
                    "content": "give me a more cleaned up version of this text extracted from a cv just order it without any extra information or comments and with out wasting any informations  : " + text,
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
