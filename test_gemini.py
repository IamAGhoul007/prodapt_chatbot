import os
from dotenv import load_dotenv
from google import genai
load_dotenv()
client = genai.Client()
response = client.models.embed_content(
    model='text-embedding-004',
    contents='What is the meaning of life?',
)
print("Success:", response)
