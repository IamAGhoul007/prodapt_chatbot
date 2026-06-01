from google import genai
from google.genai import types
import os
from dotenv import load_dotenv

load_dotenv()
client = genai.Client()

def get_weather(location: str) -> str:
    """Gets the weather for a location."""
    return f"The weather in {location} is 72 degrees."

chat = client.chats.create(
    model="gemini-2.5-flash",
    config=types.GenerateContentConfig(
        tools=[get_weather]
    )
)

response = chat.send_message("What is the weather in Austin?")
print(response.text)
