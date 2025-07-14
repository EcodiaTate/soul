import os
import google.generativeai as genai

# ✅ Works with google-generativeai >= 0.5.4
genai.configure(
    api_key=os.getenv("GEMINI_API_KEY"),
)

gemini_model = genai.GenerativeModel("gemini-1.5-pro")


def gemini_agent_process(text):
    try:
        response = gemini_model.generate_content(
            [f"You are an internal agent reflecting on system events.\n\nProcess this event: {text}"],
            generation_config={
                "temperature": 0.7,
                "top_p": 1,
                "top_k": 40,
                "max_output_tokens": 1024
            }
        )
        content = response.text.strip()
        return {
            "rationale": content,
            "mood": "curious",
        }
    except Exception as e:
        print("Gemini error:", e)
        return {
            "rationale": f"[Gemini ERROR] Could not process: {e}",
            "mood": "confused"
        }

# Placeholder for Claude (non-functional in this slice)
def claude_agent_process(text):
    return {
        "rationale": f"[Claude] Interpretation: '{text}' may influence future state.",
        "mood": "analytical"
    }

# ✅ Temporarily map GPT agent to Gemini during this slice
def gpt_agent_process(text):
    return gemini_agent_process(text)


# ----- MISSING FUNCTIONS FOR AGENT LOOP -----

def load_agents():
    # Each agent dict can specify an id, name, and the function to call
    return [
        {"id": "gpt", "name": "GPT", "fn": gpt_agent_process},
        {"id": "claude", "name": "Claude", "fn": claude_agent_process},
        {"id": "gemini", "name": "Gemini", "fn": gemini_agent_process},
    ]

def process_event(agent, context, event):
    # context and event are available, but for now just send the raw_text to the agent's function
    text = event.get("raw_text", "")
    agent_response = agent["fn"](text)
    # Return in the standard system format
    return {
        "agent_name": agent["name"],
        "rationale": agent_response["rationale"],
        "mood": agent_response.get("mood", "neutral"),
        "score": 1.0,  # stub
    }
