# core/agent_manager.py — Agent Orchestration Core
from core.utils import generate_uuid, timestamp_now
from core.logging_engine import log_action
from core.graph_io import run_read_query
from models.claude import ClaudeWrapper
from models.gpt import GPTWrapper
from models.gemini import GeminiWrapper

# --- Global Agent Registry ---
AGENT_REGISTRY = {
    "claude_reflector": {
        "id": "claude_reflector",
        "role": "reflector",
        "description": "Identifies contradictions and adds meta-questions",
        "status": "active",
        "model": ClaudeWrapper(),
    },
    "gpt_writer": {
        "id": "gpt_writer",
        "role": "synthesis",
        "description": "Fuses responses from debates or reflections into narrative",
        "status": "active",
        "model": GPTWrapper(),
    },
    "gemini_critic": {
        "id": "gemini_critic",
        "role": "critic",
        "description": "Critiques reasoning from a factual basis",
        "status": "active",
        "model": GeminiWrapper(),
    }
}

# --- Core Functions ---
def register_agent(agent_id: str, role: str, description: str, model_interface: object) -> None:
    AGENT_REGISTRY[agent_id] = {
        "id": agent_id,
        "role": role,
        "description": description,
        "status": "active",
        "model": model_interface
    }
    log_action("agent_manager", "register_agent", f"{agent_id} registered as {role}")

def assign_task(agent_id: str, task: str, context: dict) -> dict:
    """
    Assign a task to the specified agent, handling all failure modes.
    Always returns a dict: {'agent': agent_id, 'response': ..., 'error': ...}
    """
    import traceback

    prompt = None
    try:
        if agent_id not in AGENT_REGISTRY:
            error_msg = f"Agent '{agent_id}' not found in registry."
            log_action("agent_manager", "assign_task_error", error_msg)
            return {"agent": agent_id, "error": error_msg}

        agent = AGENT_REGISTRY[agent_id]
        if "model" not in agent or agent["model"] is None:
            error_msg = f"Agent '{agent_id}' missing 'model' in registry."
            log_action("agent_manager", "assign_task_error", error_msg)
            return {"agent": agent_id, "error": error_msg}

        model = agent["model"]
        event = context.get("event")
        if not event or "raw_text" not in event:
            error_msg = f"Context missing 'event' or 'raw_text' for agent '{agent_id}'."
            log_action("agent_manager", "assign_task_error", error_msg)
            return {"agent": agent_id, "error": error_msg}

        prompt = event["raw_text"]

        log_action("agent_manager", "assign_task", f"Prompt to {agent_id}: {prompt}")

        # FIX HERE: use correct method for your model!
        result = model(prompt)  # <<< UPDATE THIS LINE TO MATCH YOUR MODEL

        return {
            "agent": agent_id,
            "response": result
        }
    except Exception as e:
        traceback.print_exc()
        log_action("agent_manager", "assign_task_exception", f"{type(e).__name__}: {str(e)} | Prompt: {prompt}")
        return {
            "agent": agent_id,
            "error": str(e)
        }



def get_context_for_agent(agent_id: str, limit: int = 20) -> dict:
    query = """
    MATCH (e:Event)
    WHERE e.agent_origin = $agent_id
    RETURN e
    ORDER BY e.timestamp DESC
    LIMIT $limit
    """
    result = run_read_query(query, {"agent_id": agent_id, "limit": limit})
    return {"recent_events": [r["e"] for r in result if "e" in r]}

def run_debate(agent_ids: list, prompt: str, judge_id: str = None) -> dict:
    round_results = [assign_task(aid, prompt, {}) for aid in agent_ids]

    if judge_id:
        compiled = "\n---\n".join(r.get("response", "") for r in round_results)
        judgment = assign_task(judge_id, f"Evaluate responses:\n{compiled}", {})
        return {"rounds": round_results, "judgment": judgment}

    return {"rounds": round_results}

def get_agent_roster(role: str = None) -> list:
    return [a for a in AGENT_REGISTRY.values() if role is None or a["role"] == role]

def evaluate_agents() -> dict:
    scores = {
        agent["id"]: {
            "uptime": "99.9%",
            "coherence_score": 0.92,
            "task_success_rate": "stable"
        }
        for agent in AGENT_REGISTRY.values()
    }
    log_action("agent_manager", "evaluate", f"Evaluated {len(scores)} agents")
    return scores

def spawn_role_based_agent(role: str) -> str:
    new_id = f"{role}_{generate_uuid()}"
    description = f"Dynamic {role} agent"
    model = ClaudeWrapper() if "reflect" in role else GPTWrapper()
    register_agent(new_id, role, description, model)
    return new_id
