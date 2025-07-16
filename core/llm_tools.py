# core/llm_tools.py — Multi-LLM Prompt Orchestrator (Lazy Client Init)
import os
from core.logging_engine import log_action
from random import choice
from time import sleep

# --- Model Configs ---
MODEL_SETTINGS = {
    "gpt": {
        "model": "gpt-4",
        "max_tokens": 1024,
        "temperature": 0.7
    },
    "claude": {
        "model": "claude-3-opus-20240229",
        "temperature": 0.7
    },
    "gemini": {
        "model": "models/gemini-pro",
        "temperature": 0.7
    }
}

def _get_openai():
    import openai
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        raise RuntimeError("OPENAI_API_KEY not set")
    openai.api_key = key
    return openai

def _get_anthropic():
    import anthropic
    key = os.getenv("ANTHROPIC_API_KEY")
    if not key:
        raise RuntimeError("ANTHROPIC_API_KEY not set")
    return anthropic.Anthropic(api_key=key)

def _get_gemini_model():
    import google.generativeai as genai
    key = os.getenv("GOOGLE_API_KEY")
    if not key:
        raise RuntimeError("GOOGLE_API_KEY not set")
    genai.configure(api_key=key)
    return genai.GenerativeModel(MODEL_SETTINGS["gemini"]["model"])

# --- Base Prompt Utility ---
def _safe_prompt(model_id: str, prompt: str, system_prompt: str = None, temperature: float = 0.7) -> str:
    """Unified handler for all model prompts with fallback logging."""
    try:
        if model_id == "gpt":
            return _prompt_openai(prompt, system_prompt, temperature)
        elif model_id == "claude":
            return _prompt_claude(prompt, system_prompt, temperature)
        elif model_id == "gemini":
            return _prompt_gemini(prompt, system_prompt)
    except Exception as e:
        log_action("llm_tools", "prompt_error", f"{model_id} failed: {e}")
        return f"[{model_id} ERROR]"

# --- Model-Specific Wrappers ---
def _prompt_openai(prompt, system_prompt=None, temperature=0.7):
    openai = _get_openai()
    messages = [{"role": "system", "content": system_prompt}] if system_prompt else []
    messages.append({"role": "user", "content": prompt})
    response = openai.ChatCompletion.create(
        model=MODEL_SETTINGS["gpt"]["model"],
        messages=messages,
        max_tokens=MODEL_SETTINGS["gpt"]["max_tokens"],
        temperature=temperature
    )
    return response["choices"][0]["message"]["content"].strip()

def _prompt_claude(prompt, system_prompt=None, temperature=0.7):
    client = _get_anthropic()
    msg = client.messages.create(
        model=MODEL_SETTINGS["claude"]["model"],
        max_tokens=1024,
        temperature=temperature,
        system=system_prompt or "",
        messages=[{"role": "user", "content": prompt}]
    )
    # NOTE: structure may differ by Anthropic version, adapt if needed
    return msg.content[0].text.strip()

def _prompt_gemini(prompt, system_prompt=None):
    gemini_model = _get_gemini_model()
    chat = gemini_model.start_chat()
    intro = f"{system_prompt}\n" if system_prompt else ""
    response = chat.send_message(f"{intro}{prompt}")
    return response.text.strip()

# --- Public API ---
def prompt_gpt(prompt: str, system_prompt: str = None, temperature: float = 0.7) -> str:
    return _safe_prompt("gpt", prompt, system_prompt, temperature)

def prompt_claude(prompt: str, system_prompt: str = None, temperature: float = 0.7) -> str:
    return _safe_prompt("claude", prompt, system_prompt, temperature)

def prompt_gemini(prompt: str, context: dict = None) -> str:
    sys_prompt = context.get("system_prompt") if context else None
    return _safe_prompt("gemini", prompt, sys_prompt)

# --- Advanced ---
def select_best_response(responses: list[str], context: str = None) -> str:
    """Score and choose best response from list using Claude or fallback."""
    if not responses:
        return ""
    if len(responses) == 1:
        return responses[0]
    joined = "\n---\n".join([f"Response {i+1}:\n{r}" for i, r in enumerate(responses)])
    prompt = (
        "Given the following LLM responses, choose the best one based on coherence, originality, "
        "and alignment with context:\n\n"
        f"{joined}\n\nReturn the best response text."
    )
    return prompt_claude(prompt, system_prompt=context or "You are a consensus AI referee.")

def run_redundant_prompt(prompt: str, temperature: float = 0.7) -> dict:
    """Send prompt to all models and return all responses."""
    results = {}
    for model_id in ["gpt", "claude", "gemini"]:
        try:
            out = _safe_prompt(model_id, prompt, temperature=temperature)
            results[model_id] = out
            sleep(0.5)
        except Exception as e:
            log_action("llm_tools", "redundant_error", f"{model_id} failed: {e}")
            results[model_id] = f"[{model_id} ERROR]"
    return results
