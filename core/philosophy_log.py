# core/philosophy_log.py — Inner Reasoning Changelog
from datetime import datetime
from core.graph_io import create_node, run_read_query
from core.utils import generate_uuid
from core.logging_engine import log_action

# --- Constants ---
PHILOSOPHY_LOG_LABEL = "PhilosophyLog"
EVENT_TYPES = ["shift", "question", "review", "contradiction", "integration"]

# --- Core Functions ---
def log_philosophical_shift(event: str, rationale: str, actor: str = "system") -> bool:
    """Store a timestamped philosophical/self-concept change with context."""
    log_data = {
        "id": f"philo_{generate_uuid()}",
        "type": "shift",
        "text": event,
        "rationale": rationale,
        "actor": actor,
        "timestamp": datetime.utcnow().isoformat()
    }
    create_node(PHILOSOPHY_LOG_LABEL, log_data)
    log_action("philosophy_log", "log_shift", f"{event} — by {actor}")
    return True

def get_recent_reflections(limit: int = 10) -> list[dict]:
    """Return recent self-reflective or philosophical events."""
    query = f"""
    MATCH (p:{PHILOSOPHY_LOG_LABEL})
    RETURN p
    ORDER BY p.timestamp DESC
    LIMIT $limit
    """
    return run_read_query(query, {"limit": limit})

def get_philosophical_timeline(since: str = None) -> list[dict]:
    """Return chronological timeline of philosophical changes and internal reasoning."""
    if since:
        query = f"""
        MATCH (p:{PHILOSOPHY_LOG_LABEL})
        WHERE datetime(p.timestamp) >= datetime($since)
        RETURN p
        ORDER BY p.timestamp ASC
        """
        return run_read_query(query, {"since": since})
    else:
        return get_recent_reflections(limit=100)

def export_philosophy_log() -> str:
    """Return a human-readable narrative export of the AI’s inner evolution."""
    reflections = get_philosophical_timeline()
    export = "\n\n".join(
        f"[{r['p']['timestamp']}] ({r['p']['type']}) — {r['p']['text']} (by {r['p']['actor']})"
        for r in reflections
    )
    log_action("philosophy_log", "export", f"Exported {len(reflections)} entries.")
    return export
