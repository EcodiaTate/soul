# models/gemini.py
import os
import google.generativeai as genai

class GeminiWrapper:
    def __init__(self, model="gemini-pro", api_key=None):
        self.model = model
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        genai.configure(api_key=self.api_key)

    def __call__(self, prompt, temperature=0.7, max_tokens=1024, system_prompt=None):
        model = genai.GenerativeModel(self.model)
        full_prompt = prompt
        if system_prompt:
            full_prompt = system_prompt + "\n" + prompt
        response = model.generate_content(full_prompt)
        return response.text.strip() if hasattr(response, "text") else str(response)
