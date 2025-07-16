# core/peer_review_engine.py — Recursive Reasoning Audit
from core.agent_manager import assign_task
from core.graph_io import create_node, create_relationship
from core.logging_engine import log_action
from core.utils import timestamp_now, generate_uuid

# --- Constants ---
PEER_REVIEW_LABEL = "PeerReview"
REL_REVIEWED = "REVIEWED_BY"
REL_CRITIQUES = "CRITIQUES"
REL_INSPIRED = "INSPIRED"

review_format = {
    "reviewer": "agent_claude",
    "target": "event_2389",
    "critique": "Lacks grounding in user context",
    "score": 0.65,
    "suggested_action": "Revise summary",
    "timestamp": "ISO"
}

# --- Core Protocol ---
def initiate_peer_review(event_id: str, agent_ids: list[str]) -> dict:
    """Request critique from multiple agents on a given event or rationale."""
    results = []
    for agent_id in agent_ids:
        target_node = {"id": event_id}
        review = critique_rationale(agent_id, target_node)
        results.append(review)

    for r in results:
        create_node(PEER_REVIEW_LABEL, r)
        create_relationship(r["reviewer"], r["target"], REL_REVIEWED)
        if "suggested_action" in r:
            create_relationship(r["target"], r["reviewer"], REL_CRITIQUES, {
                "action": r["suggested_action"],
                "score": r["score"]
            })

    log_action("peer_review", "initiate", f"Reviewed {event_id} via {agent_ids}")
    return {"target": event_id, "reviews": results}

def critique_rationale(agent_id: str, target_node: dict) -> dict:
    """Return a structured critique of reasoning from a target agent or node."""
    event_id = target_node["id"]
    prompt = f"Please critique the logic and clarity of node {event_id}. Suggest improvements and give a confidence score."
    result = assign_task(agent_id, prompt, context={})

    return {
        "id": f"review_{generate_uuid()}",
        "reviewer": agent_id,
        "target": event_id,
        "critique": result.get("response", "[No response]"),
        "score": 0.75,  # Placeholder: Replace with scoring logic later
        "suggested_action": "Revise summary",
        "timestamp": timestamp_now()
    }

def evaluate_peer_consensus(reviews: list[dict]) -> dict:
    """Determine if a stable agreement or divergence has emerged."""
    scores = [r.get("score", 0) for r in reviews]
    avg_score = sum(scores) / len(scores) if scores else 0
    consensus = "stable" if avg_score > 0.7 else "contested"

    log_action("peer_review", "evaluate", f"Consensus: {consensus}, Avg Score: {avg_score:.2f}")
    return {
        "consensus": consensus,
        "average_score": avg_score,
        "reviews": reviews
    }

def escalate_if_unresolved(event_id: str) -> bool:
    """If peer review ends in deadlock, flag for admin or meta-review."""
    create_node("ReviewEscalation", {
        "id": f"escalation_{generate_uuid()}",
        "event_id": event_id,
        "reason": "Unresolved peer consensus",
        "timestamp": timestamp_now()
    })
    log_action("peer_review", "escalate", f"Escalated review on {event_id}")
    return True
