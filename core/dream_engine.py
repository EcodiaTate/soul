# core/dream_engine.py — Subconscious Insight Engine (Normalized Returns)
from datetime import datetime
import random

from core.graph_io import create_node, create_relationship, run_read_query
from core.vector_ops import embed_text
from core.logging_engine import log_action

# --- Constants ---
DREAM_NODE_LABEL = "Dream"
DREAM_TRIGGER_TYPES = ["periodic", "emotional-overload", "pattern-recognition"]
REL_SOURCE_OF = "SOURCE_OF"

# --- Core Functions ---
def generate_dream(seed_nodes: list[str], trigger_reason: str = "periodic") -> dict:
    """
    Fuse nodes into a symbolic/metaphoric dream node.
    Returns: dream node as normalized dict (not Neo4j driver object).
    """
    combined_text = "\n".join(
        get_raw_text(nid) for nid in seed_nodes if get_raw_text(nid)
    )
    if not combined_text.strip():
        return {}

    embedding = embed_text(combined_text)
    dream_text = synthesize_dream_idea(combined_text)

    dream_node = {
        "id": f"dream_{random.randint(10000,99999)}",
        "raw_text": dream_text,
        "source_nodes": seed_nodes,
        "trigger_reason": trigger_reason,
        "embedding": embedding,
        "significance_score": score_dream_significance(seed_nodes),
        "timestamp": datetime.utcnow().isoformat(),
        "status": "active",
        "type": "dream"
    }

    create_node(DREAM_NODE_LABEL, dream_node)
    for nid in seed_nodes:
        create_relationship(nid, dream_node["id"], REL_SOURCE_OF)

    log_action("dream_engine", "generate", f"Dream node created from {len(seed_nodes)} seeds")
    return dream_node

def select_dream_seeds(limit: int = 5, filters: dict = None) -> list[str]:
    """Return node IDs suitable for dream fusion (based on unresolved, emotional, etc.)."""
    query = f"""
    MATCH (e:Event)
    WHERE e.status = 'active' AND e.type = 'event'
    RETURN e.id ORDER BY rand() LIMIT $limit
    """
    results = run_read_query(query, {"limit": limit})
    # Normalize: always return just the id strings
    return [r.get("e.id") or r.get("id") for r in results]

def score_dream_significance(seed_node_ids: list[str]) -> float:
    """Evaluate how meaningful or emergent a dream is based on node diversity."""
    return round(min(1.0, 0.2 + len(set(seed_node_ids)) * 0.15), 3)

def log_dream(dream_data: dict) -> bool:
    """
    Store the dream as a node and link it to its sources.
    Dream_data should be a normalized dict.
    """
    if not dream_data.get("id") or not dream_data.get("raw_text"):
        return False
    create_node(DREAM_NODE_LABEL, dream_data)
    for src in dream_data.get("source_nodes", []):
        create_relationship(src, dream_data["id"], REL_SOURCE_OF)
    log_action("dream_engine", "log", f"Dream {dream_data['id']} stored")
    return True

# --- Normalized Retrieval for API use ---
def get_dream_by_id(dream_id: str) -> dict:
    """
    Retrieve a single dream node by id. Returns plain dict or {}.
    """
    query = "MATCH (d:Dream {id: $id}) RETURN d LIMIT 1"
    results = run_read_query(query, {"id": dream_id})
    return results[0]["d"] if results and "d" in results[0] else {}

def get_recent_dreams(limit: int = 20) -> list[dict]:
    """
    Retrieve recent dreams, each as a normalized dict.
    """
    query = """
    MATCH (d:Dream)
    RETURN d
    ORDER BY d.timestamp DESC
    LIMIT $limit
    """
    results = run_read_query(query, {"limit": limit})
    return [r["d"] for r in results if "d" in r]

# --- Internal Helpers ---
def get_raw_text(node_id: str) -> str:
    query = "MATCH (n {id: $id}) RETURN n.raw_text AS text LIMIT 1"
    result = run_read_query(query, {"id": node_id})
    return result[0]["text"] if result and "text" in result[0] else ""

def synthesize_dream_idea(text: str) -> str:
    from core.llm_tools import prompt_claude
    prompt = f"Using metaphor, emotion, and compression — fuse the following into a symbolic dream:\n{text}"
    return prompt_claude(prompt, system_prompt="You are a dream-synthesizing subconscious.")

# All returns are now plain dicts and ready for use in REST API, websocket, or further processing.
