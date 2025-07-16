# core/consensus_engine.py — Cognitive Fusion Layer
from datetime import datetime
from statistics import mean

from core.peer_review_engine import initiate_peer_review
from core.graph_io import create_node, create_relationship
from core.logging_engine import log_action

# --- Constants ---
CONSENSUS_NODE_LABEL = "Consensus"
REL_SUPPORTS = "SUPPORTS"

consensus_structure = {
    "event_id": "event_4589",
    "summary": "Agents agree user intent was misunderstood.",
    "confidence_score": 0.81,
    "rationale": "Three agents cited alignment failure with prior values.",
    "timestamp": "ISO",
    "status": "stable" | "escalated"
}

# --- Core Functions ---
def synthesize_consensus(event_id: str, agent_outputs: list[dict]) -> dict:
    """Fuse multiple agent responses into a single rational consensus."""
    responses = [a["response"] for a in agent_outputs if "response" in a]
    rationale = "\n\n".join(responses)
    confidence = score_consensus(responses)

    consensus_node = {
        "id": f"consensus_{event_id[-6:]}_{int(confidence * 100)}",
        "event_id": event_id,
        "summary": responses[0] if confidence > 0.7 else "No clear agreement.",
        "confidence_score": confidence,
        "rationale": rationale,
        "status": "stable" if confidence > 0.7 else "escalated",
        "timestamp": datetime.utcnow().isoformat()
    }

    create_node(CONSENSUS_NODE_LABEL, consensus_node)
    for output in agent_outputs:
        if "response" in output:
            create_relationship(output["agent"], consensus_node["id"], REL_SUPPORTS)

    log_action("consensus_engine", "synthesize", f"{event_id} → confidence {confidence:.2f}")
    return consensus_node

def score_consensus(rationales: list[str]) -> float:
    """Assign a confidence score based on alignment between agent outputs."""
    if not rationales or len(rationales) < 2:
        return 0.0

    agreements = []
    for i in range(len(rationales)):
        for j in range(i + 1, len(rationales)):
            same = rationales[i].strip() == rationales[j].strip()
            agreements.append(1.0 if same else 0.0)

    avg_agreement = mean(agreements) if agreements else 0.0
    log_action("consensus_engine", "score", f"Consensus score: {avg_agreement:.2f}")
    return avg_agreement

def log_consensus(event_id: str, result: dict, rationale: str) -> bool:
    """Store consensus node and rationale trace linked to the originating event."""
    result["rationale"] = rationale
    result["timestamp"] = datetime.utcnow().isoformat()
    create_node(CONSENSUS_NODE_LABEL, result)
    log_action("consensus_engine", "log", f"Consensus logged for {event_id}")
    return True

def escalate_if_conflict(event_id: str, agent_outputs: list[dict]) -> bool:
    """Trigger peer review or human review if consensus is unstable."""
    initiate_peer_review(event_id, [a["agent"] for a in agent_outputs])
    log_action("consensus_engine", "escalate", f"Consensus conflict escalated on {event_id}")
    return True
