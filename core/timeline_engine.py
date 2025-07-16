# core/timeline_engine.py — Narrative Timeline Builder (Normalized Returns)
from datetime import datetime

from core.graph_io import create_node, create_relationship, run_read_query
from core.vector_ops import embed_text
from core.logging_engine import log_action

# --- Constants ---
TIMELINE_LABEL = "TimelineEntry"
REL_HIGHLIGHTS = "HIGHLIGHTS"

timeline_format = {
    "summary": "The soul questioned its bias toward efficiency over empathy.",
    "events": ["epiphany_2", "event_40"],
    "significance": 0.82,
    "rationale": "High value divergence resolved through consensus.",
    "timestamp": "ISO"
}

# --- Core Functions ---
def summarize_sequence(node_ids: list[str], title: str = None) -> dict:
    """
    Compress a set of nodes into a narrative timeline summary.
    Always returns a normalized dict.
    """
    from core.llm_tools import prompt_claude

    node_texts = "\n".join(get_raw_text(nid) for nid in node_ids)
    prompt = f"Summarize the following sequence of thoughts/events:\n{node_texts}"
    summary = prompt_claude(prompt, system_prompt="You are a narrative compression engine.")

    summary_node = {
        "id": f"timeline_{int(datetime.utcnow().timestamp())}",
        "summary": summary,
        "linked_events": node_ids,
        "significance": round(0.5 + 0.1 * len(node_ids), 3),
        "rationale": "Compressed from system memory.",
        "timestamp": datetime.utcnow().isoformat(),
        "status": "active",
        "type": "timeline"
    }

    create_node(TIMELINE_LABEL, summary_node)
    for nid in node_ids:
        create_relationship(nid, summary_node["id"], REL_HIGHLIGHTS)

    log_action("timeline_engine", "summarize_sequence", f"Created timeline entry from {len(node_ids)} nodes")
    return summary_node

def add_philosophy_log(summary: str, linked_nodes: list[str], rationale: str = "", impact: float = 0.75) -> dict:
    """
    Wrapper to log a philosophical/self-concept shift into the timeline.
    Always returns normalized dict.
    """
    return create_timeline_entry(summary=summary, linked_nodes=linked_nodes, rationale=rationale, significance=impact)

def create_timeline_entry(summary: str, linked_nodes: list[str], rationale: str, significance: float) -> dict:
    """
    Store a key moment or transformation in the timeline.
    Returns normalized dict.
    """
    embedding = embed_text(summary)
    node = {
        "id": f"timeline_{int(datetime.utcnow().timestamp())}",
        "summary": summary,
        "linked_events": linked_nodes,
        "rationale": rationale,
        "significance": significance,
        "embedding": embedding,
        "timestamp": datetime.utcnow().isoformat(),
        "status": "active",
        "type": "timeline"
    }

    create_node(TIMELINE_LABEL, node)
    for nid in linked_nodes:
        create_relationship(nid, node["id"], REL_HIGHLIGHTS)

    log_action("timeline_engine", "create_entry", f"Timeline moment: {summary[:50]}...")
    return node

def log_timeline_shift(event_id: str, impact: str = "moderate") -> bool:
    """
    Mark a single event as timeline-worthy (e.g., breakthrough or crisis).
    """
    raw = get_raw_text(event_id)
    summary = f"Key shift: {raw[:80]}"
    return bool(create_timeline_entry(summary, [event_id], rationale="Single-node milestone", significance=0.7))

def get_timeline_entries(limit: int = 50) -> list[dict]:
    """
    Return recent timeline summaries for public display.
    Always returns a list of plain dicts, never driver objects.
    """
    query = f"""
    MATCH (t:{TIMELINE_LABEL})
    RETURN t
    ORDER BY t.timestamp DESC
    LIMIT $limit
    """
    results = run_read_query(query, {"limit": limit})
    return [r["t"] for r in results if "t" in r]

def get_timeline_entry_by_id(entry_id: str) -> dict:
    """
    Retrieve a single timeline entry by ID as a normalized dict.
    """
    query = f"MATCH (t:{TIMELINE_LABEL} {{id: $id}}) RETURN t LIMIT 1"
    results = run_read_query(query, {"id": entry_id})
    return results[0]["t"] if results and "t" in results[0] else {}

# --- Helpers ---
def get_raw_text(node_id: str) -> str:
    query = "MATCH (n {id: $id}) RETURN n.raw_text AS text, n.summary AS summary LIMIT 1"
    result = run_read_query(query, {"id": node_id})
    if result:
        return result[0].get("summary") or result[0].get("text") or "[No content]"
    return "[No node found]"

# All returns from public API-facing functions are now normalized dicts, ready for REST or websocket.
