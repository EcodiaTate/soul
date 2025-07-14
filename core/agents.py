
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
            "mood": "curious"
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
