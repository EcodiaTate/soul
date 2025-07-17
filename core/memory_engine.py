# core/memory_engine.py — Event Memory Core (Event Return Normalization)

from datetime import datetime
from uuid import uuid4

from core.vector_ops import embed_text
from core.graph_io import run_write_query, run_read_query
from core.logging_engine import log_action

# --- Constants ---
EVENT_LABELS = ["Event", "Dream", "TimelineEntry"]
EMBEDDING_DIM = 1536

def _generate_event_id(prefix: str = "event") -> str:
    return f"{prefix}_{uuid4().hex[:8]}"

def _now() -> str:
    return datetime.utcnow().isoformat()

# --- Event Creation ---
def store_event(raw_text: str, agent_origin: str = None, metadata: dict = None) -> dict:
    """
    Embed, package, and store a new event node in Neo4j.
    RETURNS: event dict (not Neo4j object), always with at least raw_text and id.
    """
    try:
        embedding = embed_text(raw_text)
        node_data = {
            "id": _generate_event_id("event"),
            "timestamp": _now(),
            "embedding": embedding,
            "raw_text": raw_text,
            "agent_origin": agent_origin or "system",
            "status": "active",
            "type": "event",
            "metadata": metadata or {}
        }

        result = run_write_query("CREATE (e:Event $props) RETURN e", {"props": node_data})
        # Try to get dict from Neo4j response
        if result and result.get("status") == "success":
            records = result.get("result", [])
            if records and isinstance(records[0], dict) and "e" in records[0]:
                event_dict = dict(records[0]["e"])
                # Ensure critical fields present
                event_dict.setdefault("id", node_data["id"])
                event_dict.setdefault("raw_text", node_data["raw_text"])
                event_dict.setdefault("agent_origin", node_data["agent_origin"])
                return event_dict

        # On failure, always return fallback event dict for downstream safety
        log_action("memory_engine", "store_event_error", f"Write failed or empty result: {result}")
        # Fallback: always provide enough for agent context
        return {
            "id": node_data["id"],
            "raw_text": node_data["raw_text"],
            "agent_origin": node_data["agent_origin"],
            "status": "failed",
            "type": "event"
        }

    except Exception as e:
        log_action("memory_engine", "store_event_exception", str(e))
        # Also return minimal fallback event dict
        return {
            "id": "event_error",
            "raw_text": raw_text,
            "agent_origin": agent_origin or "system",
            "status": "error",
            "type": "event"
        }

# --- Dream Creation ---
def store_dream_node(source_nodes: list, notes: str = "") -> dict:
    dream_id = _generate_event_id("dream")
    raw_text = f"Dream fusion of nodes: {source_nodes}"
    embedding = embed_text(raw_text)
    node_data = {
        "id": dream_id,
        "timestamp": _now(),
        "embedding": embedding,
        "raw_text": raw_text,
        "notes": notes,
        "status": "active",
        "type": "dream"
    }

    result = run_write_query("CREATE (d:Dream $props) RETURN d", {"props": node_data})
    for source_id in source_nodes:
        run_write_query("""
            MATCH (d:Dream {id: $dream_id}), (s {id: $source_id})
            CREATE (s)-[:FUSED_INTO]->(d)
        """, {"dream_id": dream_id, "source_id": source_id})

    log_action("memory_engine", "store_dream", f"Created dream node: {dream_id}")

    if result and result.get("status") == "success":
        records = result.get("result", [])
        if records and isinstance(records[0], dict):
            return dict(records[0].get("d", {}))

    return dict(node_data)

# --- Timeline Entry ---
def store_timeline_entry(summary: str, event_ids: list, significance: float, rationale: str) -> dict:
    entry_id = _generate_event_id("timeline")
    embedding = embed_text(summary)
    node_data = {
        "id": entry_id,
        "timestamp": _now(),
        "embedding": embedding,
        "summary": summary,
        "linked_events": event_ids,
        "significance": significance,
        "rationale": rationale,
        "type": "timeline",
        "status": "active"
    }

    result = run_write_query("CREATE (t:TimelineEntry $props) RETURN t", {"props": node_data})
    for eid in event_ids:
        run_write_query("""
            MATCH (t:TimelineEntry {id: $entry_id}), (e {id: $event_id})
            CREATE (e)-[:HIGHLIGHTED_IN]->(t)
        """, {"entry_id": entry_id, "event_id": eid})

    log_action("memory_engine", "store_timeline", f"Created timeline entry: {entry_id}")

    if result and result.get("status") == "success":
        records = result.get("result", [])
        if records and isinstance(records[0], dict):
            return dict(records[0].get("t", {}))

    return dict(node_data)

# --- Memory Lifecycle ---
def decay_memory(node_id: str) -> bool:
    result = run_write_query("""
        MATCH (n {id: $node_id})
        SET n.status = 'deprioritized',
            n.attention = coalesce(n.attention, 1.0) * 0.2
        RETURN n
    """, {"node_id": node_id})
    log_action("memory_engine", "decay_node", f"Decayed node {node_id}")
    return result.get("status") == "success"

def summarize_node(node_id: str) -> str:
    node = run_read_query("MATCH (n {id: $node_id}) RETURN n", {"node_id": node_id})
    if not node:
        return ""
    raw = node[0]["n"].get("raw_text", "")
    summary = embed_text(f"Summarize: {raw}")  # Placeholder for actual summarization
    run_write_query("MATCH (n {id: $node_id}) SET n.summary = $summary", {
        "node_id": node_id,
        "summary": summary
    })
    log_action("memory_engine", "summarize_node", f"Summarized node {node_id}")
    return summary

def archive_node(node_id: str) -> bool:
    result = run_write_query("""
        MATCH (n {id: $node_id})
        SET n.status = 'archived'
        RETURN n
    """, {"node_id": node_id})
    log_action("memory_engine", "archive_node", f"Archived node {node_id}")
    return result.get("status") == "success"
