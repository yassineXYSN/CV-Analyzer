import os
from huggingface_hub import InferenceClient

from dotenv import load_dotenv
load_dotenv()


def cleantext(text):
    client = InferenceClient(
        provider="novita",
        api_key=os.getenv("TEXT_CLEANER_TOKEN") ,
        timeout=300,
    )
    completion = client.chat.completions.create(
            model="deepseek-ai/DeepSeek-R1-0528-Qwen3-8B",
            messages=[
                {
                    "role": "user",
                    "content": "give me a more cleaned up version of this text extracted from a cv just order it without any extra information or comments and with out wasting any informations  : " + text,
                }
            ],
        )
    msg = completion.choices[0].message.content.strip()
    return  msg[msg.find("</think>")+9:]