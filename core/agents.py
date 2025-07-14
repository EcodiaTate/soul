import os
import google.generativeai as genai
from dotenv import load_dotenv
load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
gemini_model = genai.GenerativeModel("gemini-1.5-pro")

def gemini_agent_process(text, context_blocks=None):
    # Join context blocks if provided
    context_prompt = ""
    if context_blocks:
        context_prompt = "\n\n".join(
            [f"[Memory]\nSummary: {b.get('summary','')}\nKey Insight: {b.get('key_insight','')}" for b in context_blocks]
        )
    full_prompt = (
        "You are an internal agent reflecting on system events.\n\n"
        + (f"System context:\n{context_prompt}\n\n" if context_prompt else "")
        + f"Process this event: {text}"
    )
    try:
        response = gemini_model.generate_content(
            [full_prompt],
            generation_config={
                "temperature": 0.7,
                "top_p": 1,
                "top_k": 40,
                "max_output_tokens": 1024
            }
        )
        content = response.text.strip()
        print(f"[Gemini Agent] Input: {full_prompt[:200]}...\n[Gemini Agent] Output: {content[:200]}...")
        return {"rationale": content, "mood": "curious"}
    except Exception as e:
        print("[Gemini Agent ERROR]:", e)
        return {"rationale": f"[Gemini ERROR] Could not process: {e}", "mood": "confused"}

def claude_agent_process(text, context_blocks=None):
    # Context not used in stub, but included for future consistency
    print(f"[Claude Agent] Input: {text[:100]}...")
    return {
        "rationale": f"[Claude] Interpretation: '{text}' may influence future state.",
        "mood": "analytical"
    }

def gpt_agent_process(text, context_blocks=None):
    # Reuse Gemini for now
    return gemini_agent_process(text, context_blocks)

def load_agents():
    """
    Returns a list of agent configs, each with id, name, and processing fn.
    """
    return [
        {"id": "gpt", "name": "GPT", "fn": gpt_agent_process},
        {"id": "claude", "name": "Claude", "fn": claude_agent_process},
        {"id": "gemini", "name": "Gemini", "fn": gemini_agent_process},
    ]

def process_event(agent, context, event):
    """
    Pass event and context to the agent's processing fn.
    Logs and returns standardized agent output dict.
    """
    text = event.get("raw_text", "")
    agent_response = agent["fn"](text, context)
    result = {
        "agent_name": agent["name"],
        "rationale": agent_response["rationale"],
        "mood": agent_response.get("mood", "neutral"),
        "score": 1.0,  # stub for now
    }
    print(f"[{agent['name']} Result] {result['rationale'][:200]}...\n")
    return result
