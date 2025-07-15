# llm_tools.py — LLM Stub for Build Compatibility

def run_llm(prompt, agent=None):
    """
    Stubbed LLM runner. Returns fake JSON-like string for testing.
    """
    print(f"[llm_tools] Running LLM for agent '{agent}':\n{prompt}")
    return """
    {
        "compassion": 0.85,
        "curiosity": 0.9,
        "logic": 0.78,
        "playfulness": 0.62,
        "urgency": 0.4
    }
    """  # This simulates an OpenAI-like LLM JSON string response


def llm_extract_value_vector(text, agent="unknown"):
    """
    Calls stubbed LLM and parses the response into a usable dict.
    """
    prompt = build_llm_value_vector_prompt(text)
    raw = run_llm(prompt, agent=agent)

    import json
    try:
        vector = json.loads(raw)
    except Exception:
        vector = {"compassion": 0.5, "logic": 0.5}
    return vector


def run_llm_emotion_vector(event):
    """
    Returns a static fake emotion vector. Replace with real LLM call later.
    """
    return {
        "joy": 0.3,
        "anger": 0.2,
        "fear": 0.1,
        "love": 0.6,
        "surprise": 0.4
    }


def build_llm_value_vector_prompt(text, axes=None, version=None):
    """
    Returns a dummy prompt string. In production, this would be a real prompt template.
    """
    return f"Analyze the following statement for value expression:\n\n{text}\n\nReturn a JSON object of value weights."
