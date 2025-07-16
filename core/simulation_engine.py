# core/simulation_engine.py — Timeline Simulation Engine
from datetime import datetime

from core.graph_io import create_node, create_relationship
from core.logging_engine import log_action
from core.timeline_engine import summarize_sequence
from core.llm_tools import prompt_gpt

# --- Constants ---
SIM_NODE_LABEL = "SimulatedTimeline"
REL_SIMULATES = "SIMULATES"

# --- Core Functions ---
def simulate_timeline_change(event_id: str, mutation: dict) -> dict:
    """Create a projected outcome path if an event’s action or timing is changed."""
    base_context = get_event_summary(event_id)
    mutation_prompt = (
        f"Original context:\n{base_context}\n\n"
        f"Now simulate what might happen if we apply this change:\n{mutation}"
    )

    outcome = prompt_gpt(mutation_prompt)
    timeline_node = {
        "id": f"sim_{event_id[-6:]}_{int(datetime.utcnow().timestamp())}",
        "base_context": [event_id],
        "mutation": str(mutation),
        "projected_outcomes": [{"timestep": 1, "description": outcome}],
        "generated_by": "simulation_engine",
        "timestamp": datetime.utcnow().isoformat()
    }

    create_node(SIM_NODE_LABEL, timeline_node)
    create_relationship(event_id, timeline_node["id"], REL_SIMULATES)
    log_action("simulation_engine", "simulate_change", f"Simulated mutation on {event_id}")
    return timeline_node

def simulate_policy_shift(policy_vector: dict, test_scope: list[str]) -> dict:
    """Model system or community behavior based on a proposed new value configuration."""
    values_summary = "\n".join(f"{k}: {v}" for k, v in policy_vector.items())
    context_blurb = "\n".join(get_event_summary(nid) for nid in test_scope)

    prompt = (
        f"Given the following policy shift:\n{values_summary}\n\n"
        f"And this context:\n{context_blurb}\n\n"
        f"What would likely change in behavior, governance, or relationships?"
    )
    result = prompt_gpt(prompt)

    sim_id = f"policy_sim_{int(datetime.utcnow().timestamp())}"
    node = {
        "id": sim_id,
        "mutation": policy_vector,
        "base_context": test_scope,
        "projected_outcomes": [{"timestep": 1, "description": result}],
        "generated_by": "simulation_engine",
        "timestamp": datetime.utcnow().isoformat()
    }

    create_node(SIM_NODE_LABEL, node)
    for nid in test_scope:
        create_relationship(nid, sim_id, REL_SIMULATES)

    log_action("simulation_engine", "simulate_policy", f"Simulated policy shift over {len(test_scope)} nodes")
    return node

def generate_simulated_node(sequence: list[dict]) -> dict:
    """Compress a projected chain of outcomes into a SimulatedTimeline node."""
    summary = summarize_sequence([s["description"] for s in sequence], title="Simulated Pathway")
    node_id = f"sim_seq_{int(datetime.utcnow().timestamp())}"

    node = {
        "id": node_id,
        "mutation": "synthetic_chain",
        "projected_outcomes": sequence,
        "summary": summary["summary"],
        "generated_by": "simulation_engine",
        "timestamp": datetime.utcnow().isoformat()
    }

    create_node(SIM_NODE_LABEL, node)
    log_action("simulation_engine", "simulate_chain", f"Simulated sequence node {node_id}")
    return node

def log_simulation(sim_data: dict) -> bool:
    """Store the simulated output for admin and user review."""
    if not sim_data.get("projected_outcomes"):
        return False
    create_node(SIM_NODE_LABEL, sim_data)
    log_action("simulation_engine", "log", f"Simulation node {sim_data['id']} saved")
    return True

# --- Helpers ---
def get_event_summary(event_id: str) -> str:
    from core.graph_io import run_read_query
    query = "MATCH (e {id: $id}) RETURN e.summary AS summary, e.raw_text AS raw LIMIT 1"
    result = run_read_query({"id": event_id}, query)
    if result:
        return result[0].get("summary") or result[0].get("raw") or "[No content]"
    return "[No event found]"
