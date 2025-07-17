# core/consciousness_engine.py — Structural Self-Mutation Engine
from datetime import datetime

from core.graph_io import create_node, create_relationship, update_node_properties, run_read_query
from core.logging_engine import log_action
from core.self_concept import update_self_concept

# --- Constants ---
MUTATION_LABEL = "SchemaMutation"
REL_BASED_ON = "BASED_ON"

mutation_format = {
    "type": "value_shift",
    "description": "Decrease emphasis on individual autonomy in favor of mutual care",
    "source_nodes": ["epiphany_3", "dream_7", "user_vote_22"],
    "risk_score": 0.77,
    "status": "pending",  # | approved | applied | reverted
    "requires_human_approval": True,
    "timestamp": "ISO"
}

# --- Core Engine ---
def propose_mutation(mutation_type: str, details: dict, source_nodes: list[str]) -> dict:
    """Draft a structural change to schema, values, or self-concept with justification."""
    mutation_id = f"mutation_{int(datetime.utcnow().timestamp())}"
    mutation = {
        "id": mutation_id,
        "type": mutation_type,
        "description": details.get("description", ""),
        "source_nodes": source_nodes,
        "risk_score": evaluate_mutation_impact(details),
        "status": "pending",
        "requires_human_approval": True,
        "timestamp": datetime.utcnow().isoformat()
    }

    create_node(MUTATION_LABEL, mutation)
    for src in source_nodes:
        create_relationship(src, mutation_id, REL_BASED_ON)

    log_action("consciousness_engine", "propose", f"Proposed {mutation_type}: {mutation_id}")
    return mutation

def evaluate_mutation_impact(details: dict) -> float:
    """Score risk/impact level of a proposed mutation."""
    content = details.get("description", "") + " ".join(details.get("keywords", []))
    score = 0.4 + 0.3 * ("core_value" in content or "self-definition" in content)
    score = min(1.0, max(0.1, round(score, 2)))
    log_action("consciousness_engine", "evaluate", f"Impact score: {score}")
    return score

def apply_mutation_if_approved(mutation_id: str) -> bool:
    """After admin/community approval, commit the proposed change."""
    mutation = _get_mutation_node(mutation_id)
    if not mutation or mutation.get("status") != "approved":
        return False

    if mutation["type"] == "value_shift":
        update_self_concept({"core_values": mutation.get("new_values", [])}, rationale=mutation["description"])
    elif mutation["type"] == "identity_edit":
        update_self_concept({"identity": mutation.get("new_identity")}, rationale=mutation["description"])
    # ... extendable

    update_node_properties(mutation_id, {"status": "applied"})
    log_action("consciousness_engine", "apply", f"Mutation {mutation_id} applied.")
    return True

def log_mutation(mutation_data: dict) -> bool:
    """Store the mutation proposal and its status in the memory graph."""
    if not mutation_data.get("id"):
        return False
    create_node(MUTATION_LABEL, mutation_data)
    for nid in mutation_data.get("source_nodes", []):
        create_relationship(nid, mutation_data["id"], REL_BASED_ON)
    log_action("consciousness_engine", "log", f"Mutation {mutation_data['id']} logged.")
    return True

def rollback_last_mutation(reason: str) -> bool:
    """Revert most recent structural change if flagged."""
    query = f"""
    MATCH (m:{MUTATION_LABEL})
    WHERE m.status = 'applied'
    RETURN m ORDER BY m.timestamp DESC LIMIT 1
    """
    from core.graph_io import run_read_query
    result = run_read_query(query)
    if not result:
        return False

    mutation = result[0]["m"]
    update_node_properties(mutation["id"], {"status": "reverted", "revert_reason": reason})
    log_action("consciousness_engine", "rollback", f"Reverted {mutation['id']}: {reason}")
    return True

# --- Helper ---
def _get_mutation_node(mutation_id: str) -> dict:
    query = "MATCH (m {id: $id}) RETURN m LIMIT 1"
    result = run_read_query(query, {"id": mutation_id})
    return result[0]["m"] if result else {}
