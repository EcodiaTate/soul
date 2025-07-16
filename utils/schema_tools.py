# utils/schema_tools.py — Graph Schema Inspection & Migration
from core.graph_io import run_read_query, run_write_query
from core.logging_engine import log_action

LABEL_META_NODE = "SchemaMeta"

# --- Core Functions ---
def list_node_labels() -> list[str]:
    """Return all node labels currently in use."""
    query = "CALL db.labels() YIELD label RETURN label"
    results = run_read_query(query)
    labels = [r["label"] for r in results]
    log_action("schema_tools", "list_labels", f"Found labels: {labels}")
    return labels

def list_relationship_types() -> list[str]:
    """Return all active relationship types in the graph."""
    query = "CALL db.relationshipTypes() YIELD relationshipType RETURN relationshipType"
    results = run_read_query(query)
    rels = [r["relationshipType"] for r in results]
    log_action("schema_tools", "list_rels", f"Found relationship types: {rels}")
    return rels

def find_orphan_nodes(label: str) -> list[dict]:
    """Find nodes of a given type that have no relationships."""
    query = f"""
    MATCH (n:{label})
    WHERE NOT (n)--()
    RETURN n.id AS id, n
    """
    results = run_read_query(query)
    log_action("schema_tools", "find_orphans", f"Found {len(results)} orphan nodes of label {label}")
    return results

def migrate_node_label(old_label: str, new_label: str) -> bool:
    """Change all nodes of one type to another label (e.g. 'Belief' → 'Value')."""
    query = f"""
    MATCH (n:{old_label})
    REMOVE n:{old_label}
    SET n:{new_label}
    RETURN count(n) AS migrated_count
    """
    result = run_write_query(query)
    count = result["result"][0]["migrated_count"] if result["status"] == "success" else 0
    log_action("schema_tools", "migrate_label", f"Migrated {count} nodes from {old_label} to {new_label}")
    return result["status"] == "success"
