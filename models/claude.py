# models/claude.py
import os
import anthropic

class ClaudeWrapper:
    def __init__(self, model="claude-3-opus-20240229", api_key=None):
        self.model = model
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.client = anthropic.Anthropic(api_key=self.api_key)

    def __call__(self, prompt, temperature=0.7, max_tokens=1024, system_prompt=None):
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        response = self.client.messages.create(
            model=self.model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return response.content[0].text.strip()
