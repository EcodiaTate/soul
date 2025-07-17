# core/agent_manager.py — Agent Orchestration Core
from core.utils import generate_uuid, timestamp_now
from core.logging_engine import log_action
from models.claude import ClaudeWrapper
from models.gpt import GPTWrapper
from models.gemini import GeminiWrapper
from core.graph_io import run_read_query


# --- Global Agent Registry ---
AGENT_REGISTRY = {
  "claude_reflector": {
    "role": "reflector",
    "description": "Identifies contradictions and adds meta-questions",
    "status": "active",
    "model": ClaudeWrapper(),   # <- expects a class
  },
  "gpt_writer": {
    "role": "synthesis",
    "description": "Fuses responses from debates or reflections into narrative",
    "status": "active",
    "model": GPTWrapper(),     # <- expects a class
  },
  "gemini_critic": {
    "role": "critic",
    "description": "Critiques reasoning from a factual basis",
    "status": "active",
    "model": GeminiWrapper(),  # <- expects a class
  }
}
    # Add more agents as needed

# --- Core Functions ---
def register_agent(agent_id: str, agent_type: str, description: str, model_interface: object) -> None:
    """Create and store metadata for a new agent model/tool."""
    AGENT_REGISTRY[agent_id] = {
        "id": agent_id,
        "role": agent_type,
        "description": description,
        "status": "active",
        "model": model_interface
    }
    log_action("agent_manager", "register_agent", f"{agent_id} as {agent_type}")

def assign_task(agent_id: str, task: str, context: dict) -> dict:
    """Send a task to a selected agent and return the response."""
    agent = AGENT_REGISTRY.get(agent_id)
    if not agent or agent["status"] != "active":
        return {"error": f"Agent {agent_id} not available"}
    
    try:
        context_prompt = get_context_for_agent(agent_id, context)
        result = agent["model"].run(task, context_prompt)
        log_action("agent_manager", "assign_task", f"{agent_id} completed task")
        return {"agent": agent_id, "response": result}
    except Exception as e:
        log_action("agent_manager", "task_error", f"{agent_id} failed: {e}")
        return {"agent": agent_id, "error": str(e)}

def run_debate(agent_ids: list, prompt: str, judge_id: str = None) -> dict:
    """Execute a structured debate between agents and optionally get judgment."""
    round_results = []
    for agent_id in agent_ids:
        response = assign_task(agent_id, prompt, {})
        round_results.append(response)
    
    if judge_id:
        compiled = "\n---\n".join(r["response"] for r in round_results if "response" in r)
        judgment = assign_task(judge_id, f"Evaluate responses:\n{compiled}", {})
        log_action("agent_manager", "debate", f"Judge {judge_id} resolved debate")
        return {"rounds": round_results, "judgment": judgment}
    
    return {"rounds": round_results}

def get_agent_roster(role: str = None) -> list:
    """Return current list of agents, optionally filtered by role."""
    return [
        a for a in AGENT_REGISTRY.values()
        if role is None or a["role"] == role
    ]

def evaluate_agents() -> dict:
    """Run performance and coherence metrics on active agents."""
    # Placeholder logic — to be replaced with actual eval engine
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
    """Use prompt/template to spawn agent with role-specific behavior and memory access."""
    new_id = f"{role}_{generate_uuid()}"
    description = f"Dynamic {role} agent"
    model = ClaudeWrapper() if "reflect" in role else GPTWrapper()
    register_agent(new_id, role, description, model)
    return new_id

def get_context_for_agent(agent_id: str, limit: int = 20) -> dict:
    query = """
    MATCH (e:Event)
    WHERE e.agent_origin = $agent_id
    RETURN e
    ORDER BY e.timestamp DESC
    LIMIT $limit
    """
    result = run_read_query(query, {"agent_id": agent_id, "limit": limit})
    context = {"recent_events": [r['e'] for r in result]}
    return context
