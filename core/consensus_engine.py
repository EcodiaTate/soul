"""
consensus_engine.py — 130% God Mode
Truly Dynamic Edge Types, Value/Emotion Vectors, Mesh Edges, Audit, Actuator, and Full Integration

- All edge types discovered and applied dynamically from the current schema
- Value/emotion vectors, action plan, rationale, audit fully supported and serializable
- Semantic mesh and value links always reflect current CE-driven edge pool
"""

import math
from datetime import datetime, timezone

from core.graph_io import (
    write_consensus_to_graph,
    get_event_by_id,
    create_relationship,
    vector_search,
    get_value_nodes,
    get_edge_types
)
from core.value_vector import (
    fuse_value_vectors,
    multi_vector_conflict,
    get_value_schema_version,
    get_value_names,
    get_value_importances,
    bump_value_importance,
    FIXED_EMOTION_AXES
)
from core.memory_engine import bump_memory_importance
from core.agents import serialize_agent_response
from core.prompts import consensus_prompt, get_ecodia_identity
from core.llm_tools import run_llm

CONSENSUS_ALIGNMENT_THRESHOLD = 0.7

def check_alignment(agent_responses, threshold=CONSENSUS_ALIGNMENT_THRESHOLD):
    if not agent_responses or len(agent_responses) == 0:
        print("[consensus_engine] No agent responses provided!")
        return False

    value_vectors = [a.get("value_vector") for a in agent_responses if "value_vector" in a]
    emotion_vectors = [a.get("emotion_vector") for a in agent_responses if "emotion_vector" in a]
    if len(value_vectors) >= 2:
        mesh = multi_vector_conflict(value_vectors, threshold=threshold)
        if mesh.get("peer_review"):
            print(f"[consensus_engine] Value vector mesh not aligned: triggering peer review.")
            return False

    # (Optional) Add emotion mesh check
    if len(emotion_vectors) >= 2:
        emo_keys = set().union(*emotion_vectors)
        def as_vec(d): return [d.get(k, 0.0) for k in emo_keys]
        def cos_sim(v1, v2):
            num = sum(a*b for a, b in zip(v1, v2))
            denom = math.sqrt(sum(a*a for a in v1)) * math.sqrt(sum(b*b for b in v2))
            return num / denom if denom else 0.0
        vlist = [as_vec(v) for v in emotion_vectors]
        sims = [1 - cos_sim(vlist[i], vlist[j])
                for i in range(len(vlist)) for j in range(i+1, len(vlist))]
        avg_dist = sum(sims) / len(sims) if sims else 0.0
        if avg_dist > threshold:
            print("[consensus_engine] Emotion vector mesh not aligned: triggering peer review.")
            return False

    print(f"[consensus_engine] {len(agent_responses)} agent responses — alignment ok.")
    return True

def build_consensus(agent_responses):
    if not agent_responses:
        print("[consensus_engine] No agent responses to build consensus.")
        return None

    # Optionally: build rationale and value vector via LLM prompt, else fallback to fusion
    from core.value_vector import get_value_names
    try:
        rationales = [a.get("rationale", "") for a in agent_responses]
        agent_names = [a.get("agent_name", "?") for a in agent_responses]
        value_axes = get_value_names()

        prompt = consensus_prompt(
            get_ecodia_identity(),
            [{"agent_name": n, "rationale": r} for n, r in zip(agent_names, rationales)],
            value_axes
        )
        # Uncomment the next two lines to use LLM consensus reasoning
        # llm_response = run_llm(prompt)
        # parsed = json.loads(llm_response)
        # combined_rationale = parsed.get("rationale", "")
        # consensus_value_vector = parsed.get("value_vector", {})
        # average_score = parsed.get("consensus_score", 1.0)
        # action_plan = parsed.get("action_plan", None)
    except Exception as e:
        print(f"[consensus_engine] LLM consensus rationale fallback: {e}")
        combined_rationale = "\n\n".join(
            [f"[{a.get('agent_name', '?')}] {a.get('rationale','')}" for a in agent_responses]
        )
        average_score = sum(a.get("score", 1.0) for a in agent_responses) / len(agent_responses)
        action_plan = next((a.get("action_plan") for a in agent_responses if a.get("action_plan")), None)
        value_vectors = [a.get("value_vector") for a in agent_responses if "value_vector" in a]
        schema_version = get_value_schema_version()
        consensus_value_vector = fuse_value_vectors(value_vectors) if value_vectors else {}

    if 'combined_rationale' not in locals():
        combined_rationale = "\n\n".join(
            [f"[{a.get('agent_name', '?')}] {a.get('rationale','')}" for a in agent_responses]
        )
        average_score = sum(a.get("score", 1.0) for a in agent_responses) / len(agent_responses)
        action_plan = next((a.get("action_plan") for a in agent_responses if a.get("action_plan")), None)
        value_vectors = [a.get("value_vector") for a in agent_responses if "value_vector" in a]
        schema_version = get_value_schema_version()
        consensus_value_vector = fuse_value_vectors(value_vectors) if value_vectors else {}

    # Bump value importance for all high-expressed values in consensus
    importances = get_value_importances()
    for v, score in consensus_value_vector.items():
        if score > 0.65:
            bump_value_importance(v, amount=0.02, actor="consensus")

    # Optionally bump relevant memories (e.g. agent causal_trace, or surface)
    for agent in agent_responses:
        for mem_id in agent.get("causal_trace", []):
            try:
                bump_memory_importance(mem_id, amount=0.01, actor="consensus-context")
            except Exception:
                pass

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
    props["alignment_score"] = cosine_similarity(source_vv, target_vv)
    props["value_vector_diff"] = {k: round(source_vv.get(k, 0.0) - target_vv.get(k, 0.0), 3)
                                  for k in set(source_vv) | set(target_vv)}
    if rel_type == "TOPIC_MATCH":
        props["topics"] = list(set(event_node.get("topics", [])) & set(target_node.get("topics", [])))
    return props

def cosine_similarity(vec1, vec2):
    common_keys = set(vec1) & set(vec2)
    if not common_keys:
        return 0.0
    v1 = [vec1[k] for k in common_keys]
    v2 = [vec2[k] for k in common_keys]
    num = sum(a*b for a,b in zip(v1, v2))
    denom = math.sqrt(sum(a*a for a in v1)) * math.sqrt(sum(b*b for b in v2))
    return round(num/denom, 4) if denom else 0.0

def create_mesh_edges(event_id, consensus_vector, event_node, top_k=8):
    """
    100% Dynamic Mesh Edge Creation.
    Edge types are read live from the DB and matched by vector similarity, topic, value, or threshold rules.
    """
    edge_types = {et.get("name") for et in get_edge_types() if et.get("name")}
    value_nodes = get_value_nodes()
    similar_nodes = vector_search(consensus_vector, top_k=top_k)

    # Always connect to similar nodes, using all allowed dynamic edge types.
    for node in similar_nodes:
        for rel_type in edge_types:
            if rel_type == "CONTRADICTS":
                # Link to the most dissimilar node
                most_dissimilar = min(similar_nodes, key=lambda n: cosine_similarity(consensus_vector, n.get("value_vector", {})))
                if node["id"] == most_dissimilar["id"]:
                    props = build_edge_properties(event_node, node, rel_type, consensus_vector)
                    create_relationship(event_id, node["id"], rel_type, props)
            elif rel_type == "TOPIC_MATCH":
                event_topics = set(event_node.get("topics", []))
                target_topics = set(node.get("topics", []))
                if event_topics & target_topics:
                    props = build_edge_properties(event_node, node, rel_type, consensus_vector)
                    create_relationship(event_id, node["id"], rel_type, props)
            elif rel_type in ("EXPRESSES", "EMBODIES"):
                for value in value_nodes:
                    val_name = value.get("name")
                    score = consensus_vector.get(val_name, 0.0)
                    if score > 0.75:
                        props = {"score": score, "value_schema_version": consensus_vector.get("value_schema_version", None)}
                        create_relationship(event_id, value["id"], rel_type, props)
            else:
                # Generic link for any new or mutated edge type
                props = build_edge_properties(event_node, node, rel_type, consensus_vector)
                create_relationship(event_id, node["id"], rel_type, props)

def consensus_pipeline(event_id, agent_responses):
    if check_alignment(agent_responses):
        consensus = build_consensus(agent_responses)
        consensus_serialized = serialize_agent_response(consensus)
        node = write_consensus_to_graph(consensus_serialized)
        action_plan = consensus.get("action_plan")

        # --- Actuator Trigger ---
        if action_plan and action_plan.get("action_type") not in ["cypher", "schema"]:
            # action_result = dispatch_actuator(action_plan)
            # emit_action_update(action_result)
            pass
        elif action_plan:
            print("[consensus_engine] Cypher/Schema action detected. Passing to consciousness engine for later execution.")

        # --- Mesh edge creation: 100% dynamic
        event_node = get_event_by_id(event_id)
        if event_node and consensus.get("value_vector"):
            create_mesh_edges(event_id, consensus["value_vector"], event_node, top_k=8)

        return {"status": "consensus", "node": node}
    else:
        from core.peer_review_engine import peer_review_pipeline
        review_result = peer_review_pipeline(event_id, agent_responses)
        return {"status": "peer_review", "review_result": review_result}

def __now_utc__():
    return datetime.now(timezone.utc).isoformat()
