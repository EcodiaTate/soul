import os
from openai import OpenAI
# Initialize OpenAI client with your API key
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
print("Loaded OpenAI key:", os.getenv("OPENAI_API_KEY")[:10], "...")

def gpt_agent_process(text):
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are an internal agent reflecting on system events."},
            {"role": "user", "content": f"Process this event: {text}"}
        ]
    )
    content = response.choices[0].message.content.strip()
    return {
        "rationale": content,
        "mood": "reflective"
    }

def gemini_agent_process(text):
    return {
        "rationale": f"[Gemini] Insight: '{text}' seems meaningful.",
        "mood": "curious"
    }

def claude_agent_process(text):
    return {
        "rationale": f"[Claude] Interpretation: '{text}' may influence future state.",
        "mood": "analytical"
    }
