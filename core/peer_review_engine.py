"""
peer_review_engine.py — 130% God Mode
Value/Emotion Vector Mesh, Dynamic Edge Types, Memory Audit, Neo4j-Ready

- Detects and resolves agent mesh conflict (score, value, rationale, emotion)
- Generates peer critiques (vector, emotion, rationale mesh) using LLM-based peer_review_prompt
- Writes PeerReview, ConflictEvent, and all mesh/contradiction edges (edge types pulled from graph dynamically)
- All dict/list fields safely JSON-serialized for Neo4j
- Compatible with CE-driven edge pool and schema evolution
- Full meta-audit and causal trace support
"""

import uuid
import json
import math
from datetime import datetime, timezone

from core.graph_io import (
    create_node,
    create_relationship,
    get_event_by_id,
    get_edge_types
)
from core.consensus_engine import build_consensus, write_consensus_to_graph
from core.value_vector import (
    value_vector_conflict,
    multi_vector_conflict,
    get_value_schema_version,
    get_value_names,
    FIXED_EMOTION_AXES  # Make sure this is exposed as the fixed list in your value_vector.py
)
from core.prompts import peer_review_prompt, get_ecodia_identity
from core.llm_tools import run_llm
from core.agents import serialize_agent_response, deserialize_agent_response
from core.context_engine import format_context_blocks

CONFLICT_THRESHOLD = 0.5  # Adjust as needed for score/semantic divergence

# --- Conflict/Alignment Check ---

def detect_conflict(agent_responses, threshold=CONFLICT_THRESHOLD):
    if not agent_responses or len(agent_responses) < 2:
        print("[peer_review_engine] Not enough agent responses for conflict detection.")
        return False

    # Score divergence
    scores = [a.get("score", 0.5) for a in agent_responses]
    if (max(scores) - min(scores)) > threshold:
        print("[peer_review_engine] Conflict detected: score difference.")
        return True

    # Rationale divergence
    rationales = [a.get("rationale", "") for a in agent_responses]
    if _rationales_diverge(rationales):
        print("[peer_review_engine] Conflict detected: rationale divergence.")
        return True

    # Value vector mesh
    value_vectors = [a.get("value_vector") for a in agent_responses if "value_vector" in a]
    if len(value_vectors) >= 2:
        vv_mesh = multi_vector_conflict(value_vectors, threshold=threshold)
        if vv_mesh.get("peer_review"):
            print("[peer_review_engine] Conflict detected: value vector mesh.")
            return True

    # Emotion vector mesh
    emotion_vectors = [a.get("emotion_vector") for a in agent_responses if "emotion_vector" in a]
    if len(emotion_vectors) >= 2 and _emotion_vector_conflict(emotion_vectors, threshold=threshold):
        print("[peer_review_engine] Conflict detected: emotion vector mesh.")
        return True

    print("[peer_review_engine] No significant conflict detected.")
    return False

def _rationales_diverge(rationales):
    first = rationales[0]
    return any(r != first for r in rationales[1:])

def _emotion_vector_conflict(vectors, threshold=0.5):
    keys = set().union(*vectors)
    def as_vec(d): return [d.get(k, 0.0) for k in keys]
    def cos_sim(v1, v2):
        num = sum(a*b for a, b in zip(v1, v2))
        denom = math.sqrt(sum(a*a for a in v1)) * math.sqrt(sum(b*b for b in v2))
        return num / denom if denom else 0.0
    vlist = [as_vec(v) for v in vectors]
    sims = [1 - cos_sim(vlist[i], vlist[j])
            for i in range(len(vlist)) for j in range(i+1, len(vlist))]
    avg_dist = sum(sims) / len(sims) if sims else 0.0
    return avg_dist > threshold

# --- LLM Peer Critique Generation ---

def generate_peer_critiques(agent_responses):
    """
    Each agent receives all others' outputs as input to an LLM peer review prompt.
    Returns a list of critique dicts (Neo4j-serializable).
    """
    critiques = []
    value_axes = get_value_names()
    # For full emotion axis list, make sure you expose this in value_vector.py (e.g. as FIXED_EMOTION_AXES)
    emotion_axes = FIXED_EMOTION_AXES

    for i, a in enumerate(agent_responses):
        your_prior_output = json.dumps(a, ensure_ascii=False)
        peer_outputs = [
            json.dumps(b, ensure_ascii=False)
            for j, b in enumerate(agent_responses) if i != j
        ]
        prompt = peer_review_prompt(
            get_ecodia_identity(),
            your_prior_output,
            peer_outputs,
            value_axes,
            emotion_axes
        )
        llm_result = run_llm(prompt, agent=a.get("agent_name", "unknown"))
        try:
            review = json.loads(llm_result)
        except Exception as e:
            print(f"[peer_review_engine] LLM critique parse failed: {e}\nRaw: {llm_result}")
            review = {
                "revised_rationale": "LLM parse error",
                "value_vector_diff": {},
                "emotion_vector_diff": {},
                "shifted": False
            }
        critiques.append({
            "from": a.get("agent_name", "?"),
            "review": review
        })
    print(f"[peer_review_engine] Generated {len(critiques)} peer critiques (LLM-based).")
    return critiques

def evaluate_critiques(peer_critiques):
    # Use 'shifted' flag from LLM output, or fall back to score logic
    if not peer_critiques:
        return False
    aligned = all(c.get("review", {}).get("shifted") is False for c in peer_critiques)
    print(f"[peer_review_engine] Critique alignment: {'aligned' if aligned else 'still divergent'}.")
    return aligned

# --- Review Node and Dynamic Edge Writing ---

def write_review_nodes(event_id, agent_responses, peer_critiques, status):
    peer_review_id = str(uuid.uuid4())
    causal_trace = []
    agent_priority = max(a.get("agent_priority", 0) for a in agent_responses) if agent_responses else 0
    user_pinned = any(a.get("user_pinned") for a in agent_responses)
    audit_log_entry = {
        "agent_names": [a.get("agent_name", "?") for a in agent_responses],
        "peer_critiques": peer_critiques,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": status
    }
    for a in agent_responses:
        if a.get("causal_trace"):
            causal_trace.extend(a["causal_trace"])
    causal_trace = list(dict.fromkeys(causal_trace))

    # --- Neo4j: All complex fields must be JSON strings ---
    node = create_node("PeerReview", {
        "id": peer_review_id,
        "event_id": event_id,
        "critiques": json.dumps(peer_critiques),
        "agent_responses": json.dumps(agent_responses),
        "status": status,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "value_schema_version": get_value_schema_version(),
        "causal_trace": json.dumps(causal_trace),
        "agent_priority": agent_priority,
        "user_pinned": user_pinned,
        "audit_log": json.dumps([audit_log_entry]),
    })
    create_relationship(peer_review_id, event_id, "REVIEWS", {})

    # --- Dynamic Contradiction/Mesh Edges for Open Conflicts ---
    conflict_id = None
    if status == "unresolved":
        conflict_id = str(uuid.uuid4())
        create_node("ConflictEvent", {
            "id": conflict_id,
            "event_id": event_id,
            "peer_review_id": peer_review_id,
            "status": "open",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "value_schema_version": get_value_schema_version()
        })
        # Dynamic edge type integration:
        edge_types = [e.get("name") for e in get_edge_types()]
        contradiction_type = "CONTRADICTS" if "CONTRADICTS" in edge_types else (edge_types[0] if edge_types else "CONTRADICTS")
        create_relationship(conflict_id, event_id, contradiction_type, {})
        for a in agent_responses:
            agent_node_id = a.get("agent_name", "Unknown")
            agent_edge_type = "CONTRADICTS_AGENT" if "CONTRADICTS_AGENT" in edge_types else (edge_types[0] if edge_types else "CONTRADICTS_AGENT")
            create_relationship(conflict_id, agent_node_id, agent_edge_type, {})
        print(f"[peer_review_engine] ConflictEvent node written. ID: {conflict_id}")

    return {
        "peer_review_id": peer_review_id,
        "conflict_id": conflict_id,
        "status": status,
    }

# --- Peer Review Pipeline (Main Entrypoint) ---

def peer_review_pipeline(event_id, agent_responses):
    """
    Orchestrates full peer review:
    - Detects mesh conflict
    - Generates & stores LLM-based critiques
    - On alignment: writes consensus node
    - On unresolved: writes ConflictEvent + mesh/contradiction edges
    """
    if not detect_conflict(agent_responses):
        print("[peer_review_engine] No conflict: skipping peer review.")
        return {"status": "no_conflict"}

    peer_critiques = generate_peer_critiques(agent_responses)
    if evaluate_critiques(peer_critiques):
        consensus = build_consensus(agent_responses)
        consensus_serialized = serialize_agent_response(consensus)
        consensus_node = write_consensus_to_graph(consensus_serialized)
        result = write_review_nodes(event_id, agent_responses, peer_critiques, "resolved")
        result["consensus_node"] = consensus_node
        print("[peer_review_engine] Conflict resolved after peer review.")
        return result

    result = write_review_nodes(event_id, agent_responses, peer_critiques, "unresolved")
    print("[peer_review_engine] Peer review unresolved: escalated to ConflictEvent.")
    return result

# --- END GOD MODE PEER_REVIEW_ENGINE.PY ---
