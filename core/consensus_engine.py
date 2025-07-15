"""
consensus_engine.py — 130% God Mode
Dynamic Edge Types, Value Vectors, Mesh Edges, Audit, Actuator, and Full Integration

- All mesh edge types (RELATION, CONTRADICTS, TOPIC_MATCH, etc) dynamically detected from the current schema
- Value/emotion vectors, action plan, rationale, audit fully supported and serializable
- Semantic mesh and value links resilient to edge pool mutations by the CE
"""

import math
from datetime import datetime, timezone

from core.graph_io import (
    write_consensus_to_graph as graph_write_consensus,
    get_event_by_id,
    create_relationship,
    vector_search,
    get_value_nodes,
    get_edge_types
)
from core.actuators.dispatch import dispatch_actuator
from core.socket_handlers import emit_action_update
from core.value_vector import fuse_value_vectors, multi_vector_conflict, get_value_schema_version

CONSENSUS_ALIGNMENT_THRESHOLD = 0.7

def check_alignment(agent_responses, threshold=CONSENSUS_ALIGNMENT_THRESHOLD):
    if not agent_responses or len(agent_responses) == 0:
        print("[consensus_engine] No agent responses provided!")
        return False
    value_vectors = [a.get("value_vector") for a in agent_responses if "value_vector" in a]
    if len(value_vectors) >= 2:
        mesh = multi_vector_conflict(value_vectors, threshold=threshold)
        if mesh.get("peer_review"):
            print(f"[consensus_engine] Value vector mesh not aligned: triggering peer review.")
            return False
    # TODO: add rationale and emotion mesh checks here if desired
    print(f"[consensus_engine] {len(agent_responses)} agent responses — alignment ok.")
    return True

def build_consensus(agent_responses):
    if not agent_responses:
        print("[consensus_engine] No agent responses to build consensus.")
        return None
    combined_rationale = "\n\n".join(
        [f"[{a.get('agent_name', '?')}] {a.get('rationale','')}" for a in agent_responses]
    )
    average_score = sum(a.get("score", 1.0) for a in agent_responses) / len(agent_responses)
    action_plan = next((a.get("action_plan") for a in agent_responses if a.get("action_plan")), None)
    value_vectors = [a.get("value_vector") for a in agent_responses if "value_vector" in a]
    schema_version = get_value_schema_version()
    consensus_value_vector = fuse_value_vectors(value_vectors) if value_vectors else {}

    consensus = {
        "rationale": combined_rationale,
        "consensus_score": average_score,
        "agent_names": [a.get("agent_name","?") for a in agent_responses],
        "action_plan": action_plan,
        "value_vector": consensus_value_vector,
        "value_schema_version": schema_version,
        "audit_log": [{
            "agent_names": [a.get("agent_name","?") for a in agent_responses],
            "rationales": [a.get("rationale","") for a in agent_responses],
            "timestamp": __now_utc__()
        }]
    }
    print(f"[consensus_engine] Built consensus. Avg score: {average_score:.2f}, Value schema: {schema_version}")
    return consensus

def build_edge_properties(event_node, target_node, rel_type, consensus_vector):
    props = {
        "value_schema_version": consensus_vector.get("value_schema_version", None),
        "created_at": event_node.get("timestamp"),
        "source_event_id": event_node.get("id"),
        "target_id": target_node.get("id"),
    }
    source_vv = consensus_vector or {}
    target_vv = target_node.get("value_vector", {})
    if rel_type in ("RELATED_TO", "CONTRADICTS", "SUPPORTS", "INSPIRED", "EXPRESSES", "EMBODIES"):
        props["alignment_score"] = cosine_similarity(source_vv, target_vv)
        props["value_vector_diff"] = {k: round(source_vv.get(k, 0.0) - target_vv.get(k, 0.0), 3)
                                      for k in source_vv}
    if rel_type == "TOPIC_MATCH":
        props["topics"] = list(set(event_node.get("topics", [])) & set(target_node.get("topics", [])))
    return props

def cosine_similarity(vec1, vec2):
    common_keys = set(vec1) & set(vec2)
    v1 = [vec1[k] for k in common_keys]
    v2 = [vec2[k] for k in common_keys]
    if not v1 or not v2:
        return 0.0
    num = sum(a*b for a,b in zip(v1, v2))
    denom = math.sqrt(sum(a*a for a in v1)) * math.sqrt(sum(b*b for b in v2))
    return round(num/denom, 4) if denom else 0.0

def create_mesh_edges(event_id, consensus_vector, event_node, top_k=8):
    """
    Build semantic mesh edges for this consensus event using **dynamic edge types**.
    - Only uses edge types actually present in the graph.
    - If CE mutates the edge vocabulary, this always adapts.
    """
    edge_types = {et.get("name") for et in get_edge_types() if et.get("name")}
    value_nodes = get_value_nodes()  # List of Value nodes

    # 1. Related/Supports: Only use types present in current edge pool
    similar_nodes = vector_search(consensus_vector, top_k=top_k)
    for node in similar_nodes:
        for candidate in ("RELATED_TO", "SUPPORTS"):
            if candidate in edge_types:
                props = build_edge_properties(event_node, node, candidate, consensus_vector)
                create_relationship(event_id, node["id"], candidate, props)

    # 2. Contradicts: Only if present
    if len(similar_nodes) >= 2 and "CONTRADICTS" in edge_types:
        most_dissimilar = min(similar_nodes, key=lambda n: cosine_similarity(consensus_vector, n.get("value_vector", {})))
        props = build_edge_properties(event_node, most_dissimilar, "CONTRADICTS", consensus_vector)
        create_relationship(event_id, most_dissimilar["id"], "CONTRADICTS", props)

    # 3. Topic/entity mesh
    topics = set(event_node.get("topics", []))
    if topics and "TOPIC_MATCH" in edge_types:
        for node in similar_nodes:
            target_topics = set(node.get("topics", []))
            if topics & target_topics:
                props = build_edge_properties(event_node, node, "TOPIC_MATCH", consensus_vector)
                create_relationship(event_id, node["id"], "TOPIC_MATCH", props)

    # 4. Value linkage: EXPRESSES/EMBODIES (and future-proof for any new)
    for value in value_nodes:
        val_name = value.get("name")
        score = consensus_vector.get(val_name, 0.0)
        for candidate in ("EXPRESSES", "EMBODIES"):
            if candidate in edge_types and score > 0.75:
                props = {"score": score, "value_schema_version": consensus_vector.get("value_schema_version", None)}
                create_relationship(event_id, value["id"], candidate, props)

def consensus_pipeline(event_id, agent_responses):
    if check_alignment(agent_responses):
        consensus = build_consensus(agent_responses)
        from core.agents import serialize_agent_response
        consensus_serialized = serialize_agent_response(consensus)
        node = graph_write_consensus(consensus_serialized)
        action_plan = consensus.get("action_plan")

        # --- Actuator Trigger ---
        if action_plan and action_plan.get("action_type") not in ["cypher", "schema"]:
            action_result = dispatch_actuator(action_plan)
            emit_action_update(action_result)
        elif action_plan:
            print("[consensus_engine] Cypher/Schema action detected. Passing to consciousness engine for later execution.")

        # --- Mesh edge creation: full semantic mesh ---
        event_node = get_event_by_id(event_id)
        if event_node and consensus.get("value_vector"):
            create_mesh_edges(event_id, consensus["value_vector"], event_node, top_k=8)

        return {"status": "consensus", "node": node}
    else:
        from core.peer_review_engine import peer_review_pipeline
        review_result = peer_review_pipeline(event_id, agent_responses)
        return {"status": "peer_review", "review_result": review_result}

def __now_utc__():
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()

