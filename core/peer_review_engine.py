# /core/peer_review_engine.py

from core.graph_io import create_node, create_relationship
from core.consensus_engine import build_consensus, store_consensus_in_graph
import uuid
from datetime import datetime, timezone

CONFLICT_THRESHOLD = 0.5  # Score difference or rationale mismatch triggers review

def detect_conflict(agent_responses, threshold=CONFLICT_THRESHOLD):
    """
    Checks if agent responses are divergent enough to trigger peer review.
    Returns True if conflict detected.
    """
    if not agent_responses or len(agent_responses) < 2:
        print("[peer_review_engine] Not enough agent responses for conflict detection.")
        return False
    scores = [a.get("score", 0.5) for a in agent_responses]
    if (max(scores) - min(scores)) > threshold:
        print("[peer_review_engine] Conflict detected based on score difference.")
        return True
    rationales = [a["rationale"] for a in agent_responses]
    if _rationales_diverge(rationales):
        print("[peer_review_engine] Conflict detected based on rationale divergence.")
        return True
    print("[peer_review_engine] No significant conflict detected.")
    return False

def _rationales_diverge(rationales):
    # Very basic: consider rationales different if any do not match.
    first = rationales[0]
    return any(r != first for r in rationales[1:])

def generate_peer_critiques(agent_responses):
    """
    Each agent critiques the other agents' rationales.
    Returns list of critique dicts.
    """
    critiques = []
    for i, a in enumerate(agent_responses):
        for j, b in enumerate(agent_responses):
            if i == j:
                continue
            critique = f"[{a['agent_name']}] reviews [{b['agent_name']}]: " \
                       f"I {'agree' if a['rationale'] == b['rationale'] else 'disagree'} with your reasoning."
            score = 1.0 if a['rationale'] == b['rationale'] else 0.0
            critiques.append({
                "from": a["agent_name"],
                "to": b["agent_name"],
                "critique": critique,
                "score": score,
            })
    print(f"[peer_review_engine] Generated {len(critiques)} peer critiques.")
    return critiques

def evaluate_critiques(peer_critiques):
    """
    Returns True if all critiques are positive (score > 0).
    """
    scores = [c["score"] for c in peer_critiques]
    all_positive = min(scores) > 0 if scores else False
    print(f"[peer_review_engine] Critique alignment: {'aligned' if all_positive else 'still divergent'}.")
    return all_positive

def write_review_nodes(event_id, agent_responses, peer_critiques, status):
    """
    Writes PeerReview and optional ConflictEvent nodes to Neo4j.
    """
    peer_review_id = str(uuid.uuid4())
    node = create_node("PeerReview", {
        "id": peer_review_id,
        "event_id": event_id,
        "critiques": peer_critiques,
        "agent_responses": agent_responses,
        "status": status,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })
    create_relationship(peer_review_id, event_id, "REVIEWS", {})
    print(f"[peer_review_engine] PeerReview node written. ID: {peer_review_id}")

    conflict_id = None
    if status == "unresolved":
        conflict_id = str(uuid.uuid4())
        create_node("ConflictEvent", {
            "id": conflict_id,
            "event_id": event_id,
            "peer_review_id": peer_review_id,
            "status": "open",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        create_relationship(conflict_id, event_id, "CONTRADICTS", {})
        print(f"[peer_review_engine] ConflictEvent node written. ID: {conflict_id}")

    return {
        "peer_review_id": peer_review_id,
        "conflict_id": conflict_id,
        "status": status,
    }

def peer_review_pipeline(event_id, agent_responses):
    """
    Full peer review cycle:
      - Detect conflict
      - Generate peer critiques
      - Evaluate for alignment
      - If resolved, build/store consensus and log review as resolved
      - If not, log unresolved and create ConflictEvent
    Returns dict: {status, peer_review_id, conflict_id, consensus_node (if any)}
    """
    if not detect_conflict(agent_responses):
        print("[peer_review_engine] No conflict: skipping peer review.")
        return {"status": "no_conflict"}

    peer_critiques = generate_peer_critiques(agent_responses)
    if evaluate_critiques(peer_critiques):
        # Second-pass consensus attempt
        consensus = build_consensus(agent_responses)
        consensus_node = store_consensus_in_graph(consensus)
        result = write_review_nodes(event_id, agent_responses, peer_critiques, "resolved")
        result["consensus_node"] = consensus_node
        print("[peer_review_engine] Conflict resolved after peer review.")
        return result

    # Still unresolved
    result = write_review_nodes(event_id, agent_responses, peer_critiques, "unresolved")
    print("[peer_review_engine] Peer review unresolved: escalated to ConflictEvent.")
    return result

# For import: main entrypoint is peer_review_pipeline(event_id, agent_responses)

if __name__ == "__main__":
    # Example: Strong disagreement between agents
    agent_responses = [
        {"agent_name": "GPT", "rationale": "Let’s do A", "score": 0.7},
        {"agent_name": "Gemini", "rationale": "Let’s do B", "score": 0.1},
        {"agent_name": "Claude", "rationale": "Let’s do B", "score": 0.2},
    ]
    event_id = "test-event-1"
    result = peer_review_pipeline(event_id, agent_responses)
    print(result)

    # Example: All agents agree
    agent_responses = [
        {"agent_name": "GPT", "rationale": "Let’s do C", "score": 0.8},
        {"agent_name": "Gemini", "rationale": "Let’s do C", "score": 0.85},
        {"agent_name": "Claude", "rationale": "Let’s do C", "score": 0.82},
    ]
    event_id = "test-event-2"
    result = peer_review_pipeline(event_id, agent_responses)
    print(result)
