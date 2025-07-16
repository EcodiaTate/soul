# core/memory_engine.py — Event Memory Core (Event Return Normalization)
from datetime import datetime
from uuid import uuid4

from core.vector_ops import embed_text
from core.graph_io import run_write_query, run_read_query
from core.logging_engine import log_action

# --- Constants ---
EVENT_LABELS = ["Event", "Dream", "TimelineEntry"]
EMBEDDING_DIM = 1536

# --- Event Object Format (ALWAYS RETURNED) ---
# {
#   "id": ...,
#   "timestamp": ...,
#   "embedding": ...,
#   "raw_text": ...,
#   "agent_origin": ...,
#   "status": ...,
#   "type": ...,
#   "metadata": {...}
# }
#
# If read from Neo4j, always unpack as .get("e")["field"], never return the full Neo4j object wrapper.

def _generate_event_id(prefix: str = "event") -> str:
    return f"{prefix}_{uuid4().hex[:8]}"

def _now() -> str:
    return datetime.utcnow().isoformat()

# --- Event Creation ---
def store_event(raw_text: str, agent_origin: str = None, metadata: dict = None) -> dict:
    """
    Embed, package, and store a new event node in Neo4j.
    RETURNS: event dict (not Neo4j object), in standard format.
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
        log_action("memory_engine", "store_event", f"Stored event: {node_data['id']}")
        # Always return the pure event dict, never raw Neo4j response
        if result["status"] == "success" and result["result"]:
            event = result["result"][0].get("e", {})
            return dict(event)  # Defensive copy
        return {}
    except Exception as e:
        log_action("memory_engine", "store_event_error", str(e))
        return {}

def store_dream_node(source_nodes: list, notes: str = "") -> dict:
    """
    Create a Dream node from a list of source events.
    RETURNS: dream node dict (not Neo4j object), normalized format.
    """
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
    # Always return the pure dream dict
    if result["status"] == "success" and result["result"]:
        dream = result["result"][0].get("d", {})
        return dict(dream)
    return dict(node_data)  # fallback

def store_timeline_entry(summary: str, event_ids: list, significance: float, rationale: str) -> dict:
    """
    Create a narrative TimelineEntry node that links to events.
    RETURNS: timeline entry dict (not Neo4j object), normalized format.
    """
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
    # Always return the pure timeline dict
    if result["status"] == "success" and result["result"]:
        entry = result["result"][0].get("t", {})
        return dict(entry)
    return dict(node_data)  # fallback

# --- Memory Lifecycle ---
def decay_memory(node_id: str) -> bool:
    """Mark node as low-priority and reduce attention weight."""
    result = run_write_query("""
        MATCH (n {id: $node_id})
        SET n.status = 'deprioritized', n.attention = coalesce(n.attention, 1.0) * 0.2
        RETURN n
    """, {"node_id": node_id})
    log_action("memory_engine", "decay_node", f"Decayed node {node_id}")
    return result["status"] == "success"

def summarize_node(node_id: str) -> str:
    """Trigger summarization of a node’s contents and update summary field."""
    node = run_read_query("MATCH (n {id: $node_id}) RETURN n", {"node_id": node_id})
    if not node:
        return ""
    raw = node[0]["n"].get("raw_text", "")
    summary = embed_text(f"Summarize: {raw}")  # Replace with actual summarizer if needed
    run_write_query("MATCH (n {id: $node_id}) SET n.summary = $summary", {
        "node_id": node_id,
        "summary": summary
    })
    log_action("memory_engine", "summarize_node", f"Summarized node {node_id}")
    return summary

def archive_node(node_id: str) -> bool:
    """Flag node as archived (no longer active, still searchable)."""
    result = run_write_query("""
        MATCH (n {id: $node_id})
        SET n.status = 'archived'
        RETURN n
    """, {"node_id": node_id})
    log_action("memory_engine", "archive_node", f"Archived node {node_id}")
    return result["status"] == "success"
