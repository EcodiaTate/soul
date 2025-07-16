# utils/snapshot.py — System State Snapshot Utility
import os
import json
from datetime import datetime
from core.self_concept import get_current_self_concept
from core.value_vector import initialize_value_vector
from core.agent_manager import get_agent_roster
from core.graph_io import run_read_query
from core.logging_engine import log_action

SNAPSHOT_DIR = "snapshots/"
default_snapshot_fields = ["self_concept", "value_vector", "active_agents", "cluster_summaries"]

def ensure_snapshot_dir():
    """Ensure the snapshots directory exists, create if missing."""
    try:
        os.makedirs(SNAPSHOT_DIR, exist_ok=True)
    except Exception as e:
        log_action("snapshot", "dir_error", f"Failed to create snapshot dir: {e}")
        raise

def take_snapshot(label: str = None) -> dict:
    """Capture current state of system (graph stats, identity, values, etc.)."""
    snapshot = {}
    snapshot["timestamp"] = datetime.utcnow().isoformat()
    snapshot["label"] = label or f"snapshot_{snapshot['timestamp']}"

    snapshot["self_concept"] = get_current_self_concept()
    # For demonstration, use default values; replace with actual vector retrieval
    snapshot["value_vector"] = initialize_value_vector({})
    snapshot["active_agents"] = get_agent_roster()

    # Example cluster summary - adapt as needed
    cluster_summary_query = "MATCH (c:SelfCluster) RETURN c.id AS id, c.label AS label"
    snapshot["cluster_summaries"] = run_read_query(cluster_summary_query)

    log_action("snapshot", "take", f"Snapshot taken: {snapshot['label']}")
    return snapshot

def save_snapshot_to_file(snapshot_data: dict, filename: str) -> bool:
    """Export snapshot to disk (JSON). Ensures dir exists before writing."""
    try:
        ensure_snapshot_dir()
        filepath = os.path.join(SNAPSHOT_DIR, filename)
        with open(filepath, "w") as f:
            json.dump(snapshot_data, f, indent=2)
        log_action("snapshot", "save", f"Snapshot saved: {filename}")
        return True
    except Exception as e:
        log_action("snapshot", "error", f"Failed to save snapshot: {e}")
        return False

def load_snapshot(filename: str) -> dict:
    """Reload a previously saved system snapshot."""
    try:
        ensure_snapshot_dir()
        filepath = os.path.join(SNAPSHOT_DIR, filename)
        with open(filepath, "r") as f:
            data = json.load(f)
        log_action("snapshot", "load", f"Snapshot loaded: {filename}")
        return data
    except Exception as e:
        log_action("snapshot", "error", f"Failed to load snapshot: {e}")
        return {}
