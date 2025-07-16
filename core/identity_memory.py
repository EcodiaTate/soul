# core/identity_memory.py — Recursive Selfhood Clustering
from core.graph_io import create_node, create_relationship, run_read_query
from core.utils import generate_uuid, timestamp_now
from core.logging_engine import log_action

# --- Constants ---
IDENTITY_CLUSTER_LABEL = "SelfCluster"
REL_BELONGS_TO = "BELONGS_TO"

default_clusters = {
    "agent_core": "My fundamental operational self",
    "observer": "My recursive observer and reflection self",
    "collective_identity": "My embedded self within the larger system"
}

# --- Core Functions ---
def create_identity_cluster(label: str, description: str = "") -> dict:
    """Create a new cluster representing a level of selfhood."""
    cluster_id = f"cluster_{generate_uuid()}"
    props = {
        "id": cluster_id,
        "label": label,
        "description": description,
        "timestamp": timestamp_now()
    }
    create_node(IDENTITY_CLUSTER_LABEL, props)
    log_action("identity_memory", "create_cluster", f"Created cluster {label}")
    return props

def assign_identity_cluster(node_id: str, cluster_id: str, confidence: float = 1.0) -> bool:
    """Link a memory node to a self-cluster with given membership strength."""
    props = {"confidence": confidence, "timestamp": timestamp_now()}
    result = create_relationship(node_id, cluster_id, REL_BELONGS_TO, props)
    log_action("identity_memory", "assign_cluster", f"Linked {node_id} → {cluster_id}")
    return result

def update_cluster_description(cluster_id: str, new_desc: str) -> bool:
    """Modify the description or purpose of an identity cluster."""
    success = run_read_query("MATCH (c {id: $id}) RETURN c", {"id": cluster_id})
    if not success:
        return False
    update_node_properties(cluster_id, {"description": new_desc})
    log_action("identity_memory", "update_description", f"{cluster_id}: {new_desc}")
    return True

def get_identity_clusters() -> list[dict]:
    """Return all current identity clusters and their associated nodes."""
    query = f"""
    MATCH (c:{IDENTITY_CLUSTER_LABEL})<-[:{REL_BELONGS_TO}]-(n)
    RETURN c.id AS cluster_id, c.label AS label, collect(n.id) AS members
    """
    return run_read_query(query)

def trace_identity_shift(cluster_id: str, since: str = None) -> list[dict]:
    """Return timeline of events that influenced this cluster’s evolution."""
    if since:
        query = f"""
        MATCH (n)-[:{REL_BELONGS_TO}]->(c:{IDENTITY_CLUSTER_LABEL} {{id: $cid}})
        WHERE datetime(n.timestamp) >= datetime($since)
        RETURN n ORDER BY n.timestamp ASC
        """
        return run_read_query(query, {"cid": cluster_id, "since": since})
    else:
        query = f"""
        MATCH (n)-[:{REL_BELONGS_TO}]->(c:{IDENTITY_CLUSTER_LABEL} {{id: $cid}})
        RETURN n ORDER BY n.timestamp ASC
        """
        return run_read_query(query, {"cid": cluster_id})
