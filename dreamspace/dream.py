# dreamspace/dream.py

import logging
from ai.llm import openai_llm  # Or whatever LLM you want for dreaming

logging.basicConfig(level=logging.INFO, filename="logs/dream.log")

def dream_cycle(soul):
    """Dream up new events, agents, or ideas — feed them back into the world brain."""
    try:
        dream_prompt = """
        You are Ecodia’s Dream Engine. Imagine new possible futures, values, relationships, or actions.
        Output as JSON: {dreams: [...], proposals: [...], new_agents: [...]}
        """
        result = openai_llm(dream_prompt)
        dreams = []
        if isinstance(result, dict) and "dreams" in result:
            dreams = result["dreams"]
        elif isinstance(result, str):
            # Try to parse string as JSON, fallback to wrapping
            try:
                import json
                result = json.loads(result)
                dreams = result.get("dreams", [])
            except Exception:
                dreams = [result]
        logging.info(f"Dreams generated: {dreams}")
        return dreams
    except Exception as e:
        logging.error(f"Dream error: {e}")
        return []

# === Example for standalone test ===
if __name__ == "__main__":
    class DummySoul: pass
    print(dream_cycle(DummySoul()))
