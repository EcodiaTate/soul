import json
import os
import random

# --- Import OpenAI, Gemini, and Anthropic SDKs or use HTTP requests
import openai
import anthropic
from google.generativeai import GenerativeModel  # Example, update as needed

from core.prompts import (
    processing_prompt,
    peer_review_prompt,
    contextualization_prompt,
    consensus_prompt,
)
from core.value_vector import (
    get_value_names,
    get_value_schema_version,
    get_value_importances,
    FIXED_EMOTION_AXES,
)

# ---- Config
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
OPENAI_EMBED_MODEL = os.environ.get("OPENAI_EMBED_MODEL", "text-embedding-ada-002")
OPENAI_LLM_MODEL = os.environ.get("OPENAI_LLM_MODEL", "gpt-3.5-turbo")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-1.5-pro")
ANTHROPIC_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-3-opus-20240229")

# --- Helper for LLM dispatch ---
def run_llm(prompt, agent=None, purpose=None, model=None):
    """
    Multi-backend LLM runner.
    - Embedding/context: GPT
    - Chat/agent/peer: Claude
    - Consensus/CE: Gemini
    """
    backend = (purpose or "").lower()
    response = None

    # Embedding/context compression: GPT
    if backend in ["embedding", "context", "compress"]:
        print(f"[llm_tools] OpenAI GPT ({OPENAI_EMBED_MODEL}) for context/embedding.")
        openai.api_key = OPENAI_API_KEY
        # Simulate embedding as not all OpenAI accounts have embeddings endpoint
        return [random.uniform(-1, 1) for _ in range(1536)]

    # Agent mesh/persona/peer review: Claude
    elif backend in ["agent", "chat", "peer_review", "mesh"]:
        print(f"[llm_tools] Claude ({ANTHROPIC_MODEL}) for agent/peer review.")
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        msg = client.messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=512,
            temperature=0.0,
            system=prompt,
            messages=[{"role": "user", "content": prompt}]
        )
        text = msg.content[0].text if msg.content and msg.content[0].text else ""
        try:
            response = json.loads(text)
        except Exception:
            response = _dev_parse_json_from_anything(text)
        return response

    # Consensus/CE: Gemini
    elif backend in ["consensus", "ce", "consciousness", "rational_synthesis"]:
        print(f"[llm_tools] Gemini ({GEMINI_MODEL}) for consensus/CE.")
        model = GenerativeModel(GEMINI_MODEL)
        out = model.generate_content(prompt)
        text = out.text if hasattr(out, "text") else str(out)
        try:
            response = json.loads(text)
        except Exception:
            response = _dev_parse_json_from_anything(text)
        return response

    # Default fallback: OpenAI GPT
    else:
        print(f"[llm_tools] OpenAI GPT ({OPENAI_LLM_MODEL}) for fallback/default.")
        openai.api_key = OPENAI_API_KEY
        completion = openai.ChatCompletion.create(
            model=OPENAI_LLM_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=512,
        )
        text = completion.choices[0].message.content
        try:
            response = json.loads(text)
        except Exception:
            response = _dev_parse_json_from_anything(text)
        return response

def _dev_parse_json_from_anything(text):
    """
    Dev fallback: try to find JSON in raw string.
    """
    import re
    match = re.search(r'(\{[\s\S]*\})', text)
    if match:
        try:
            return json.loads(match.group(1))
        except Exception:
            pass
    return {}

# --- Contextual compression (uses GPT) ---
def compress_text(raw_text):
    prompt = contextualization_prompt(raw_text)
    result = run_llm(prompt, purpose="context")
    return result

# --- Value vector extraction (Agent mesh: Claude) ---
def llm_extract_value_vector(text, agent="unknown"):
    value_axes = get_value_names()
    schema_version = get_value_schema_version()
    prompt = processing_prompt("", text, value_axes)
    out = run_llm(prompt, agent=agent, purpose="agent")
    if isinstance(out, dict):
        if "value_vector" in out:
            return {k: float(max(0.0, min(1.0, out["value_vector"].get(k, 0.0))) ) for k in value_axes}
        return {k: float(max(0.0, min(1.0, out.get(k, 0.0))) ) for k in value_axes}
    return {k: 0.5 for k in value_axes}

# --- Emotion vector extraction (Claude) ---
def run_llm_emotion_vector(event, agent="unknown"):
    axes = list(FIXED_EMOTION_AXES)
    prompt = f"Extract emotion vector for: {event.get('raw_text','')}"
    out = run_llm(prompt, agent=agent, purpose="agent")
    if isinstance(out, dict):
        return {k: float(max(0.0, min(1.0, out.get(k, 0.0))) ) for k in axes}
    return {k: 0.5 for k in axes}

# --- Peer review (Claude) ---
def llm_peer_review(agent_prior, peer_outputs, value_axes, emotion_axes, agent="unknown"):
    prompt = peer_review_prompt(
        get_ecodia_identity(),
        agent_prior,
        peer_outputs,
        value_axes,
        emotion_axes
    )
    return run_llm(prompt, agent=agent, purpose="peer_review")

# --- Consensus/CE synthesis (Gemini) ---
def llm_consensus(agent_rationales, value_axes):
    prompt = consensus_prompt(
        get_ecodia_identity(),
        agent_rationales,
        value_axes
    )
    return run_llm(prompt, purpose="consensus")

# --- Build value vector prompt (for LLM) ---
def build_llm_value_vector_prompt(text, axes=None, version=None):
    axes = axes or get_value_names()
    desc = "\n".join([f"- {ax}" for ax in axes])
    prompt = f"""Analyze the following statement for value expression. For each value, score from 0 (not present) to 1 (maximal). Output JSON:

Values:
{desc}

Input: {text}
Return a JSON object with keys as value names and values as scores (0-1).
"""
    return prompt

__all__ = [
    "run_llm",
    "llm_extract_value_vector",
    "run_llm_emotion_vector",
    "compress_text",
    "build_llm_value_vector_prompt",
    "llm_peer_review",
    "llm_consensus"
]
