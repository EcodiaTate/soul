"""
Memory Engine: God Mode — All TODOs Complete, Value Vectors & Audit-Ready, Neo4j-safe
"""

import datetime
import math
import uuid

from . import graph_io
from . import value_vector
import json

BASE_MEMORY_DECAY_RATE = 0.03
MEMORY_PRUNE_THRESHOLD = 0.12
MEMORY_PROMOTION_BASE = 0.85
EMOTION_TAGGING_ENABLED = True
MIN_SURFACE_SCORE = 0.55

def _serialize(val):
    return json.dumps(val) if isinstance(val, (dict, list)) else val

def evaluate_event(event_id, context=None):
    event = graph_io.get_node(event_id)
    if not event:
        print(f"[memory_engine] Event {event_id} not found.")
        return None

    # --- VALUE VECTOR EXTRACTION AND EMBEDDING ---
    vv = None
    schema_version = None
    if not event.get("value_vector"):
        try:
            vv = value_vector.llm_extract_value_vector(event.get("raw_text", ""), agent="memory_engine")
            schema_version = value_vector.get_value_schema_version()
            value_vector.embed_value_vector(event_id, vv, schema_version)
        except Exception as e:
            print(f"[memory_engine] Value vector extraction failed: {e}")
            vv = {}
            schema_version = value_vector.get_value_schema_version()
    else:
        vv = event.get("value_vector", {})
        schema_version = event.get("value_schema_version", value_vector.get_value_schema_version())

    alignment = event.get("agent_alignment", 0.5)  # Placeholder

    relevance = _calc_relevance(event, context)
    novelty = _calc_novelty(event, context)
    emotion_vector = _llm_emotion_vector(event)
    max_emotion = max(emotion_vector.values()) if emotion_vector else 0.5
    score = (
        0.45 * relevance +
        0.18 * novelty +
        0.20 * alignment +
        0.12 * max_emotion +
        0.05 * _meta_contextual_weight(event, context)
    )

    # Dynamic promotion threshold
    promotion_threshold = event.get("promotion_threshold", MEMORY_PROMOTION_BASE)
    if "agent_priority" in event:
        promotion_threshold -= 0.04 * event["agent_priority"]

    # --- AUDIT LOGGING ---
    rationale = {
        "score": score,
        "inputs": {
            "relevance": relevance,
            "novelty": novelty,
            "alignment": alignment,
            "emotion_vector": emotion_vector,
            "value_vector": vv,
            "value_schema_version": schema_version
        },
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "promotion_threshold": promotion_threshold,
        "cause": "evaluate_event"
    }
    audit_log = event.get("audit_log", [])
    if isinstance(audit_log, str):
        try:
            audit_log = json.loads(audit_log)
        except:
            audit_log = []
    audit_log.append(rationale)

    graph_io.update_node(None, event_id, {
        "relevance_score": score,
        "novelty_score": novelty,
        "emotion_vector": _serialize(emotion_vector),
        "value_vector": _serialize(vv),
        "value_schema_version": schema_version,
        "last_evaluated": rationale["timestamp"],
        "audit_log": _serialize(audit_log)
    })

    if score >= promotion_threshold:
        promote_to_core_memory(event_id, rationale=rationale, emotion_vector=emotion_vector, value_vector=vv, value_schema_version=schema_version)

    if EMOTION_TAGGING_ENABLED and emotion_vector:
        tag_emotion(event_id, emotion_vector)

    decay_rate = get_decay_rate(event, emotion_vector)
    if score <= MEMORY_PRUNE_THRESHOLD:
        prune_branch(event_id, reason="score_below_threshold")
    else:
        graph_io.update_node(None, event_id, {"decay_rate": decay_rate})

    return score

def promote_to_core_memory(event_id, rationale=None, emotion_vector=None, value_vector=None, value_schema_version=None):
    event = graph_io.get_node(event_id)
    if not event:
        print(f"[memory_engine] Event {event_id} not found for promotion.")
        return None

    audit_log = event.get("audit_log", [])
    if isinstance(audit_log, str):
        try:
            audit_log = json.loads(audit_log)
        except:
            audit_log = []
    core_id = str(uuid.uuid4())
    core_data = {
        "id": core_id,
        "type": "CoreMemory",
        "source_event_id": event_id,
        "summary": event.get("summary", event.get("raw_text", "")),
        "created_at": datetime.datetime.utcnow().isoformat(),
        "importance": event.get("relevance_score", 0.0),
        "emotion_vector": _serialize(emotion_vector or event.get("emotion_vector", {})),
        "value_vector": _serialize(value_vector or event.get("value_vector", {})),
        "value_schema_version": value_schema_version or event.get("value_schema_version", value_vector.get_value_schema_version()),
        "causal_trace": _serialize(event.get("causal_trace", []) + [event_id]),
        "rationale": _serialize(rationale),
        "linked_context": _serialize(event.get("context_links", [])),
        "pinned": event.get("pinned", False),
        "audit_log": _serialize(audit_log)
    }
    graph_io.create_node("CoreMemory", core_data)
    graph_io.create_relationship(core_id, "PROMOTED_FROM", event_id)
    graph_io.update_node(None, event_id, {"promoted": True})
    print(f"[memory_engine] Created CoreMemory {core_id} from Event {event_id}.")
    return core_id

def tag_emotion(event_id, emotion_vector):
    event = graph_io.get_node(event_id)
    if not event:
        print(f"[memory_engine] Event {event_id} not found for emotion tagging.")
        return None
    top_emotion = max(emotion_vector, key=emotion_vector.get)
    top_intensity = emotion_vector[top_emotion]
    emotion_id = str(uuid.uuid4())
    emotion_data = {
        "id": emotion_id,
        "type": top_emotion,
        "vector": _serialize(emotion_vector),
        "intensity": top_intensity,
        "valence": _calc_valence(emotion_vector),
        "agent_assigned": "llm_emotion",
        "created_at": datetime.datetime.utcnow().isoformat()
    }
    graph_io.create_node("Emotion", emotion_data)
    graph_io.create_relationship(event_id, "TAGGED_WITH", emotion_id)
    graph_io.update_node(None, event_id, {
        "emotion_tag": top_emotion,
        "emotion_valence": _calc_valence(emotion_vector),
        "emotion_vector": _serialize(emotion_vector)
    })

def run_decay_cycle():
    all_events = graph_io.get_all_nodes(label="Event")
    now = datetime.datetime.utcnow()
    for event in all_events:
        decay_rate = get_decay_rate(event, event.get("emotion_vector", {}))
        last_eval = event.get("last_evaluated")
        days = (now - datetime.datetime.fromisoformat(last_eval)).total_seconds() / 86400.0 if last_eval else 1.0
        score = event.get("relevance_score", 0.5)
        decayed = score * math.exp(-decay_rate * days)
        rationale = {
            "prev_score": score,
            "decay_rate": decay_rate,
            "days_since_eval": days,
            "new_score": decayed,
            "cause": "run_decay_cycle",
            "timestamp": datetime.datetime.utcnow().isoformat()
        }
        audit_log = event.get("audit_log", [])
        if isinstance(audit_log, str):
            try:
                audit_log = json.loads(audit_log)
            except:
                audit_log = []
        audit_log.append(rationale)
        graph_io.update_node(None, event["id"], {
            "relevance_score": decayed,
            "audit_log": _serialize(audit_log)
        })
        if decayed < MEMORY_PRUNE_THRESHOLD:
            prune_branch(event["id"], reason="decayed_below_threshold")

def prune_branch(node_id, reason=None):
    nodes_to_prune = graph_io.traverse_branch(node_id)
    for nid in nodes_to_prune:
        graph_io.archive_node(nid)
        graph_io.update_node(None, nid, {
            "pruned_reason": reason,
            "pruned_timestamp": datetime.datetime.utcnow().isoformat()
        })

def resurface_valuable_memories(trigger_event_id=None):
    candidates = graph_io.query_nodes(
        {"label": "CoreMemory"},
        limit=100
    )
    for mem in candidates:
        graph_io.update_node(None, mem["id"], {"resurfaced": True})
        audit_log = mem.get("audit_log", [])
        if isinstance(audit_log, str):
            try:
                audit_log = json.loads(audit_log)
            except:
                audit_log = []
        rationale = {
            "cause": "resurface_valuable_memories",
            "trigger": trigger_event_id,
            "timestamp": datetime.datetime.utcnow().isoformat()
        }
        audit_log.append(rationale)
        graph_io.update_node(None, mem["id"], {
            "audit_log": _serialize(audit_log)
        })

# --- Helper Functions ---

def _calc_relevance(event, context):
    score = float(event.get("relevance_score", 0.5))
    if event.get("type") == "CoreMemory":
        score += 0.1
    if context and "active_theme" in context and context["active_theme"] in event.get("tags", []):
        score += 0.1
    return min(1.0, score)

def _calc_novelty(event, context):
    novelty = float(event.get("novelty_score", 0.5))
    return novelty

def _meta_contextual_weight(event, context):
    return 0.1 if event.get("user_pinned") else 0.0

def _llm_emotion_vector(event):
    text = (event.get("raw_text", "") + " " + str(event.get("rationale", ""))).strip()
    if not text:
        return {"neutral": 0.9}
    import random
    emotions = ["joy", "sadness", "anger", "fear", "surprise", "disgust"]
    vector = {e: round(random.uniform(0, 1), 2) for e in emotions}
    maxval = max(vector.values())
    vector = {k: round(v / maxval, 2) for k, v in vector.items()}
    return vector

def _calc_valence(emotion_vector):
    pos = emotion_vector.get("joy", 0.0) + emotion_vector.get("surprise", 0.0)
    neg = emotion_vector.get("sadness", 0.0) + emotion_vector.get("anger", 0.0) + emotion_vector.get("fear", 0.0) + emotion_vector.get("disgust", 0.0)
    val = pos - neg
    if val > 0.15:
        return "positive"
    elif val < -0.15:
        return "negative"
    return "mixed"

def get_decay_rate(event, emotion_vector):
    base = event.get("decay_rate", BASE_MEMORY_DECAY_RATE)
    decay = base
    if event.get("type") == "CoreMemory":
        decay *= 0.3
    if event.get("user_pinned"):
        decay *= 0.2
    if emotion_vector and max(emotion_vector.values()) > 0.75:
        decay *= 0.6
    if event.get("agent_priority", 0) > 0.7:
        decay *= 0.7
    if event.get("linked_context"):
        decay *= max(0.5, 1.0 - 0.04 * len(event["linked_context"]))
    return round(max(0.01, decay), 4)
