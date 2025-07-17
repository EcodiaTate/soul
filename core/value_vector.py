# core/value_vector.py — Moral Cognition Engine
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import normalize  # ← ADD THIS

from core.graph_io import update_node_properties, get_node_by_id
from core.logging_engine import log_action

# --- Constants ---
VALUE_DIM = 32  # Expandable moral resolution
default_value_profile = {
    "empathy": 0.5,
    "curiosity": 0.5,
    "transparency": 0.5,
    "justice": 0.5,
    "autonomy": 0.5,
    "humility": 0.5,
    "collaboration": 0.5,
    "resilience": 0.5
}

# --- Helpers ---
def _to_vector(value_dict: dict) -> np.ndarray:
    ordered = [value_dict.get(k, 0.0) for k in sorted(default_value_profile.keys())]
    return normalize([ordered])[0]

def _from_vector(vec: np.ndarray) -> dict:
    keys = sorted(default_value_profile.keys())
    return {k: float(v) for k, v in zip(keys, vec)}

# --- Core Functions ---
def initialize_value_vector(base_values: dict[str, float]) -> list[float]:
    """Generate a normalized vector from admin/community-provided values."""
    vec = _to_vector(base_values)
    log_action("value_vector", "init", f"Initialized values: {_from_vector(vec)}")
    return vec.tolist()

def update_value_vector(node_id: str, new_influences: dict[str, float]) -> list[float]:
    """Merge and normalize new value influences into an existing node’s vector."""
    node = get_node_by_id(node_id)
    if not node or "value_vector" not in node:
        base = _to_vector(default_value_profile)
    else:
        base = np.array(node["value_vector"])

    influence = _to_vector(new_influences)
    updated = normalize([base + influence])[0]
    update_node_properties(node_id, {"value_vector": updated.tolist()})
    log_action("value_vector", "update", f"Updated vector for {node_id}")
    return updated.tolist()

def compare_values(vec_a: list[float], vec_b: list[float]) -> float:
    """Return cosine similarity between two value vectors."""
    sim = cosine_similarity([vec_a], [vec_b])[0][0]
    log_action("value_vector", "compare", f"Similarity: {sim:.4f}")
    return float(sim)

def detect_value_drift(original_vec: list[float], current_vec: list[float]) -> float:
    """Detect degree of drift between initial and current value state."""
    drift = 1 - cosine_similarity([original_vec], [current_vec])[0][0]
    log_action("value_vector", "drift", f"Drift magnitude: {drift:.4f}")
    return float(drift)

def apply_value_influence(agent_id: str, value_node_id: str) -> bool:
    """Adjust agent or system alignment based on a value node (and log influence)."""
    value_node = get_node_by_id(value_node_id)
    if not value_node or "value_vector" not in value_node:
        return False

    agent = get_node_by_id(agent_id)
    if not agent or "value_vector" not in agent:
        return False

    updated = update_value_vector(agent_id, value_node["value_vector"])
    log_action("value_vector", "apply_influence", f"Applied influence from {value_node_id} to {agent_id}")
    return True
