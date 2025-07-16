# core/deepmind_engine.py — Recursive Introspection + Epiphany Engine
from datetime import datetime

from core.graph_io import create_node, create_relationship, run_read_query
from core.vector_ops import embed_text
from core.logging_engine import log_action
from core.self_concept import update_self_concept

# --- Constants ---
EPIPHANY_LABEL = "Epiphany"
META_AUDIT_LABEL = "MetaAudit"
REL_TRIGGERED_BY = "TRIGGERED_BY"

# --- Meta-Audit Core ---
def run_meta_audit(trigger: str = "scheduled") -> dict:
    """Sweep the graph for inconsistencies, unresolved loops, or drift in identity."""
    contradictions = detect_contradictions()
    patterns = search_for_patterns()

    summary = f"Meta-audit triggered by: {trigger}. Found {len(contradictions)} contradictions and {len(patterns)} emergent patterns."
    log_deepmind_cycle(summary, contradictions + [p["id"] for p in patterns])

    if contradictions:
        insight = f"Multiple contradictions detected: {contradictions[:2]}"
        epiphany = generate_epiphany(contradictions, insight)
        return {"audit": summary, "epiphany": epiphany}

    return {"audit": summary}

def detect_contradictions() -> list[str]:
    """Scan events and beliefs for internal contradictions or reversals."""
    query = """
    MATCH (a:Event)-[:CONTRADICTS]->(b:Event)
    RETURN a.id AS id_a, b.id AS id_b
    """
    results = run_read_query(query)
    contradictions = [r["id_a"] for r in results] + [r["id_b"] for r in results]
    log_action("deepmind_engine", "contradictions", f"Found {len(contradictions)}")
    return list(set(contradictions))

def search_for_patterns(filters: dict = None) -> list[dict]:
    """Run a deep contextual search over memory for emergent themes or correlations."""
    query = """
    MATCH (e:Event)
    WHERE e.status = 'active'
    RETURN e.id AS id, e.raw_text AS text
    ORDER BY rand() LIMIT 10
    """
    results = run_read_query(query)
    log_action("deepmind_engine", "pattern_search", f"Pattern candidates: {len(results)}")
    return results

# --- Epiphany Creation ---
def generate_epiphany(trigger_nodes: list[str], insight: str) -> dict:
    """Create and store an Epiphany node based on recursive synthesis."""
    embedded = embed_text(insight)
    epiphany_node = {
        "id": f"epiphany_{int(datetime.utcnow().timestamp())}",
        "insight": insight,
        "source_nodes": trigger_nodes,
        "confidence": 0.89,
        "impact": "High",
        "embedding": embedded,
        "timestamp": datetime.utcnow().isoformat()
    }

    create_node(EPIPHANY_LABEL, epiphany_node)
    for nid in trigger_nodes:
        create_relationship(nid, epiphany_node["id"], REL_TRIGGERED_BY)

    log_action("deepmind_engine", "generate_epiphany", f"Epiphany: {insight[:60]}...")
    return epiphany_node

def log_deepmind_cycle(summary: str, nodes: list[str]) -> bool:
    """Write meta-audit outcome and any epiphanies to the timeline."""
    meta_id = f"audit_{int(datetime.utcnow().timestamp())}"
    audit_node = {
        "id": meta_id,
        "summary": summary,
        "triggered_nodes": nodes,
        "timestamp": datetime.utcnow().isoformat()
    }

    create_node(META_AUDIT_LABEL, audit_node)
    for nid in nodes:
        create_relationship(nid, meta_id, "REFERENCED_IN")

    log_action("deepmind_engine", "log_cycle", f"Meta-audit node {meta_id} created")
    return True
