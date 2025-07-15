"""
agents.py — 120% God Mode
Value/Emotion Vectors, Audit, Schema, Trace, and Meta-Reflection Engine

Core: Agent cognition, registry, serialization, audit logging, and lifecycle for Soul-OS.
Every agent run logs all fields (schema, value vector, rationale, emotion, causal trace, audit log, etc).
"""

import uuid
import json
import os
from datetime import datetime, timezone

from core.value_vector import (
    llm_extract_value_vector,
    score_value_vector,
    get_value_schema_version
)
from core.memory_engine import evaluate_event, _llm_emotion_vector  # Emotion engine stub

# --- Agent Registry & Static Config ---
AGENT_REGISTRY = {}

def register_agent(name, agent_func, description=None, persona=None, model_type=None):
    AGENT_REGISTRY[name] = {
        "func": agent_func,
        "description": description or "",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "persona": persona or "",
        "model_type": model_type or "LLM",
        "log_path": None,  # Optionally assign per-agent log file
        "memory_vector_profile": {},  # For future context shaping
        "parent": None,    # Lineage support
        "children": []
    }

# --- Serialization Utilities ---

COMPLEX_FIELDS = {
    "value_vector", "emotion_vector", "audit_log", "causal_trace", "rationale", "action_plan"
}
def serialize_agent_response(resp: dict) -> dict:
    """
    Ensures all complex fields are json-serialized for Neo4j.
    Always call before storing in DB!
    """
    result = {}
    for k, v in resp.items():
        if k in COMPLEX_FIELDS and isinstance(v, (dict, list)):
            result[k] = json.dumps(v)
        else:
            result[k] = v
    return result

def deserialize_agent_response(resp: dict) -> dict:
    """
    Parses any json-stringified dict/list fields back into native Python objects.
    """
    d = dict(resp)
    for k in COMPLEX_FIELDS:
        if k in d and isinstance(d[k], str):
            try:
                d[k] = json.loads(d[k])
            except Exception:
                pass  # It was already a native type or malformed; leave as-is
    return d

# --- Main Agent Logic ---

def agent_reason(event, agent_name, context=None, log=True):
    """
    The one-call agent cognition routine.
    Handles agent selection, full extraction/serialization, audit logging, and meta-data.
    Returns agent response dict.
    """
    agent = AGENT_REGISTRY.get(agent_name)
    if not agent:
        raise ValueError(f"Agent '{agent_name}' not registered!")

    # 1. Run agent-specific logic (LLM, rules, etc)
    result = agent["func"](event, context=context)
    if not isinstance(result, dict):
        raise ValueError("Agent must return dict with at least 'rationale' and 'score'.")

    # 2. Value Vector extraction (if not provided)
    value_vec = result.get("value_vector")
    if not value_vec:
        try:
            value_vec = llm_extract_value_vector(event.get("raw_text", ""), agent=agent_name)
        except Exception as e:
            print(f"[agents] Value vector extraction failed for agent {agent_name}: {e}")
            value_vec = {}

    # 3. Schema Version
    schema_version = get_value_schema_version()

    # 4. Emotion Vector (if not provided)
    emotion_vec = result.get("emotion_vector")
    if not emotion_vec:
        try:
            emotion_vec = _llm_emotion_vector(event)
        except Exception as e:
            print(f"[agents] Emotion vector extraction failed for agent {agent_name}: {e}")
            emotion_vec = {}

    # 5. Structured Extraction & Defaults
    rationale = result.get("rationale", f"No rationale provided by {agent_name}.")
    score = float(result.get("score", 1.0))
    action_plan = result.get("action_plan", None)
    causal_trace = result.get("causal_trace", [])
    agent_priority = float(result.get("agent_priority", 0.0))
    user_pinned = bool(result.get("user_pinned", False))

    # Audit log entry
    audit_entry = {
        "rationale": rationale,
        "value_vector": value_vec,
        "emotion_vector": emotion_vec,
        "score": score,
        "schema_version": schema_version,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    audit_log = result.get("audit_log", [])
    audit_log = audit_log + [audit_entry]

    # Meta-agent response object
    agent_response = {
        "id": str(uuid.uuid4()),
        "agent_name": agent_name,
        "model_type": agent.get("model_type", "LLM"),
        "persona": agent.get("persona", ""),
        "rationale": rationale,
        "score": score,
        "action_plan": action_plan,
        "value_vector": value_vec,
        "value_schema_version": schema_version,
        "emotion_vector": emotion_vec,
        "causal_trace": causal_trace + [event.get("id")],
        "agent_priority": agent_priority,
        "user_pinned": user_pinned,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "audit_log": audit_log
    }

    if log:
        print(f"[agents] {agent_name} ({agent.get('model_type')}) Score {score:.2f} | Schema v{schema_version} | Event {event.get('id')}")
    return agent_response

# --- Example Agent Definitions ---

def llm_agent(event, context=None):
    """
    LLM agent template (stub).
    Replace this with LLM API call + persona/context system prompt as needed.
    """
    import random
    rationale = "This is a stub LLM agent rationale."
    score = round(random.uniform(0.1, 0.99), 3)
    action_plan = None
    # Optional: Provide value_vector, emotion_vector, etc.
    return {
        "rationale": rationale,
        "score": score,
        "action_plan": action_plan,
        # Let core pipeline extract value/emotion vectors by default
    }

# Register core agents (stub, real agents to be wired in)
register_agent(
    "LLM-Stub",
    llm_agent,
    description="Stub agent for demo/testing.",
    persona="Objective, reflective LLM test agent",
    model_type="Stub"
)

# --- Multi-Agent Mesh Execution ---

def run_all_agents(event, context=None):
    """
    Runs all registered agents on the event and returns responses.
    """
    responses = []
    for agent_name in AGENT_REGISTRY:
        resp = agent_reason(event, agent_name, context)
        responses.append(resp)
    return responses

# --- Traceability & Introspection ---

def explain_agent(agent_name):
    """
    Returns full metadata and description for agent.
    """
    agent = AGENT_REGISTRY.get(agent_name)
    if not agent:
        return f"Agent '{agent_name}' is not registered."
    return {
        "name": agent_name,
        "description": agent.get("description", ""),
        "created_at": agent.get("created_at"),
        "model_type": agent.get("model_type"),
        "persona": agent.get("persona"),
        "func_doc": agent["func"].__doc__,
        "log_path": agent.get("log_path")
    }

def list_agents():
    """
    Returns a summary list of all registered agents and their personas.
    """
    return [
        {
            "name": name,
            "model_type": agent["model_type"],
            "persona": agent["persona"],
            "description": agent["description"],
            "created_at": agent["created_at"]
        }
        for name, agent in AGENT_REGISTRY.items()
    ]

# --- Agent Log File Integration (optional) ---

def write_agent_log(agent_name, data):
    """
    Append agent logs to disk (if enabled in config).
    """
    agent = AGENT_REGISTRY.get(agent_name)
    if not agent or not agent.get("log_path"):
        return
    path = agent["log_path"]
    try:
        with open(path, "a") as f:
            f.write(json.dumps(data) + "\n")
    except Exception as e:
        print(f"[agents] Failed to write agent log for {agent_name}: {e}")

# --- Example usage (in pipeline): ---
# event = {"id": "evt-1", "raw_text": "I lied to protect my friend."}
# response = agent_reason(event, "LLM-Stub")
# all_responses = run_all_agents(event)

# --- End God Mode agents.py ---

