"""
agents.py — Fully Dynamic God Mode
Value/Emotion Vectors, Audit, Schema, Trace, and Meta-Reflection Engine

Dynamically supports arbitrary agents, vector schema evolution, and audit fields.
Each agent can have its own persona, logic, logging, lineage, and custom metadata.
"""

import uuid
import json
from datetime import datetime, timezone
from core.llm_tools import run_llm_emotion_vector
from core.value_vector import (
    extract_and_score_value_vector,  
    get_value_schema_version
)

AGENT_REGISTRY = {}

def register_agent(
    name,
    agent_func,
    description=None,
    persona=None,
    model_type=None,
    log_path=None,
    extra_fields=None
):
    AGENT_REGISTRY[name] = {
        "func": agent_func,
        "description": description or "",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "persona": persona or "",
        "model_type": model_type or "LLM",
        "log_path": log_path,
        "memory_vector_profile": {},
        "parent": None,
        "children": [],
        **(extra_fields or {})
    }

COMPLEX_FIELDS = {
    "value_vector", "emotion_vector", "audit_log", "causal_trace",
    "rationale", "action_plan"
}

def serialize_agent_response(resp: dict) -> dict:
    result = {}
    for k, v in resp.items():
        if k in COMPLEX_FIELDS and isinstance(v, (dict, list)):
            result[k] = json.dumps(v)
        else:
            result[k] = v
    return result

def deserialize_agent_response(resp: dict) -> dict:
    d = dict(resp)
    for k in COMPLEX_FIELDS:
        if k in d and isinstance(d[k], str):
            try:
                d[k] = json.loads(d[k])
            except Exception:
                pass
    return d

def agent_reason(event, agent_name, context=None, log=True):
    """
    The dynamic agent cognition routine.
    Handles agent selection, extraction/serialization, audit logging, meta-data, and schema evolution.
    """
    agent = AGENT_REGISTRY.get(agent_name)
    if not agent:
        raise ValueError(f"Agent '{agent_name}' not registered!")

    context_block = event.get("context") or context
    if not context_block:
        raise ValueError("Missing compressed context block in event.")

    result = agent["func"](event, context=context_block)
    if not isinstance(result, dict):
        raise ValueError("Agent must return dict with at least 'rationale' and 'score'.")

    # Dynamically inject value vector (unless agent provides custom)
    value_vec = result.get("value_vector")
    if not value_vec:
        try:
            value_vec = extract_and_score_value_vector(context_block, agent=agent_name)
        except Exception as e:
            print(f"[agents] Value vector extraction failed for agent '{agent_name}': {e}")
            value_vec = {}

    # Dynamically inject emotion vector (unless agent provides custom)
    emotion_vec = result.get("emotion_vector")
    if not emotion_vec:
        try:
            emotion_vec = run_llm_emotion_vector(context_block, agent=agent_name)
        except Exception as e:
            print(f"[agents] Emotion vector extraction failed for agent '{agent_name}': {e}")
            emotion_vec = {}

    rationale = result.get("rationale", f"No rationale provided by {agent_name}.")
    score = float(result.get("score", 1.0))
    action_plan = result.get("action_plan", None)
    causal_trace = result.get("causal_trace", [])
    schema_version = get_value_schema_version()
    agent_priority = float(result.get("agent_priority", 0.0))
    user_pinned = bool(result.get("user_pinned", False))

    audit_entry = {
        "rationale": rationale,
        "value_vector": value_vec,
        "emotion_vector": emotion_vec,
        "score": score,
        "schema_version": schema_version,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    audit_log = result.get("audit_log", []) + [audit_entry]

    # Support for arbitrary extra fields in responses
    agent_response = {
        "id": str(uuid.uuid4()),
        "agent_name": agent_name,
        "model_type": agent.get("model_type"),
        "persona": agent.get("persona"),
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
        "audit_log": audit_log,
        # Pass through any agent-level extras, in case your agent returns more fields
        **{k: v for k, v in result.items() if k not in {
            "rationale", "score", "action_plan", "value_vector", "emotion_vector",
            "causal_trace", "agent_priority", "user_pinned", "audit_log"
        }}
    }

    if log:
        print(f"[agents] {agent_name} ({agent['model_type']}) Score {score:.2f} | v{schema_version} | Event {event.get('id')}")

    return agent_response

# --- Agent Definition: Dynamic Example Stub ---

def llm_agent(event, context=None):
    """
    Generic agent stub for live demo/testing.
    Replace this with any persona, reflection, or reasoning logic.
    """
    import random
    rationale = "Stub LLM agent: replace me with a true reflection prompt/LLM call."
    # Return empty vectors for dynamic injection, but allow extra fields if desired
    return {
        "rationale": rationale,
        "score": round(random.uniform(0.2, 0.9), 3),
        "action_plan": None,
    }

# Example dynamic agent registration:
register_agent(
    "LLM-Stub",
    llm_agent,
    description="Stub agent for demo/testing.",
    persona="Objective test agent",
    model_type="Stub"
)

# --- Mesh Execution: Run All Agents ---

def run_all_agents(event, context=None):
    responses = []
    for name in AGENT_REGISTRY:
        try:
            resp = agent_reason(event, name, context)
            responses.append(resp)
        except Exception as e:
            print(f"[agents] Error running agent '{name}': {e}")
    return responses

# --- Agent Metadata Tools ---

def explain_agent(agent_name):
    agent = AGENT_REGISTRY.get(agent_name)
    if not agent:
        return f"Agent '{agent_name}' not found."
    return {
        "name": agent_name,
        "description": agent.get("description"),
        "created_at": agent.get("created_at"),
        "model_type": agent.get("model_type"),
        "persona": agent.get("persona"),
        "func_doc": agent["func"].__doc__
    }

def list_agents():
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

# --- Optional: Dynamic Agent Log File Integration ---

def write_agent_log(agent_name, data):
    agent = AGENT_REGISTRY.get(agent_name)
    if not agent or not agent.get("log_path"):
        return
    try:
        with open(agent["log_path"], "a") as f:
            f.write(json.dumps(data) + "\n")
    except Exception as e:
        print(f"[agents] Failed to write log for {agent_name}: {e}")
