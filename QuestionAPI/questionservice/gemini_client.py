# gemini_client.py
from google import genai
from google.genai import types
import os

class GeminiClient:
    def __init__(self):
        self.client = genai.Client(api_key=os.getenv("gemini_api_key"))

    def generate_text(self, messages, system_instruction, model="gemini-2.0-flash"):
        response = self.client.models.generate_content(
            model=model,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction
            ),
            contents=messages
        )
        return response.text
