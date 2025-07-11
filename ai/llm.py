# ai/llm.py

import os
import openai
try: from google.generativeai import GenerativeModel
except ImportError: GenerativeModel = None
try: import anthropic
except ImportError: anthropic = None
import json

openai.api_key = os.environ.get("OPENAI_API_KEY")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

def openai_llm(prompt, model="gpt-4", temperature=0.6):
    response = openai.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are Ecodia's soul, creative and meta-cognitive."},
            {"role": "user", "content": prompt}
        ],
        temperature=temperature,
    )
    out = response.choices[0].message.content
    try: return json.loads(out)
    except Exception: return out

def gemini_llm(prompt, model="gemini-1.5-pro-latest", temperature=0.6):
    if not GenerativeModel or not GEMINI_API_KEY:
        raise RuntimeError("Gemini not available or not installed.")
    model = GenerativeModel(model, api_key=GEMINI_API_KEY)
    response = model.generate_content(prompt)
    try: return json.loads(response.text)
    except Exception: return response.text

def claude_llm(prompt, model="claude-3-opus-20240229", temperature=0.6):
    if not anthropic or not ANTHROPIC_API_KEY:
        raise RuntimeError("Claude not available or not installed.")
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    response = client.messages.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
        max_tokens=2048,
    )
    out = response.content[0].text
    try: return json.loads(out)
    except Exception: return out

LLM_AGENTS = [
    {"name": "openai_gpt4", "llm_func": openai_llm},
    {"name": "gemini", "llm_func": gemini_llm},
    {"name": "claude", "llm_func": claude_llm},
]
