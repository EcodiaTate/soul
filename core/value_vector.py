"""
value_vector.py — Unified Value/Importance Schema, Scoring, Dynamic Decay, and Audit Engine
Author: Ecodia Dev
Last updated: 2025-07-16
"""

import uuid
import datetime
import json
import logging
from typing import List, Dict, Any, Tuple, Optional

import numpy as np

from core import graph_io

VALUE_VECTOR_PROMPT_VERSION = 2
AUDIT_LOG_NODE_LABEL = "ValueSchemaAudit"
VALUE_NODE_LABEL = "Value"
VECTOR_FIELD = "value_vector"
IMPORTANCE_FIELD = "importance"
SCHEMA_VERSION_FIELD = "value_schema_version"

logger = logging.getLogger("value_vector")
logger.setLevel(logging.INFO)

_value_pool_cache = None
_schema_version_cache = None

# core/value_vector.py

FIXED_EMOTION_AXES = [
    "joy",
    "sadness",
    "anger",
    "fear",
    "disgust",
    "surprise",
    "curiosity",
    "trust",
    "shame",
    "love"
]

def _now():
    return datetime.datetime.utcnow().isoformat()

def _serialize(val):
    return json.dumps(val) if isinstance(val, (dict, list)) else val

def _parse(val):
    if isinstance(val, str):
        try:
            return json.loads(val)
        except Exception:
            return val
    return val

def _new_value_node(name: str, label: str, description: str, actor: str, importance: float = 0.5) -> Dict[str, Any]:
    return {
        "uuid": str(uuid.uuid4()),
        "name": name,
        "label": label,
        "description": description,
        "created_at": _now(),
        "created_by": actor,
        "active": True,
        "importance": float(importance)
    }

def _log_schema_change(old_pool, new_pool, actor, action, note=""):
    payload = {
        "timestamp": _now(),
        "actor": actor,
        "action": action,
        "note": note,
        "old_pool": old_pool,
        "new_pool": new_pool
    }
    logger.info(f"SCHEMA_CHANGE: {json.dumps(payload)}")
    graph_io.create_node(AUDIT_LOG_NODE_LABEL, {k: _serialize(v) for k, v in payload.items()})

# === VALUE POOL & SCHEMA MANAGEMENT ===

def get_current_value_pool() -> Tuple[List[Dict[str, Any]], int]:
    global _value_pool_cache, _schema_version_cache
    if _value_pool_cache is None or _schema_version_cache is None:
        _value_pool_cache, _schema_version_cache = load_pool_from_db()
    return _value_pool_cache, _schema_version_cache

def get_value_schema_version() -> int:
    _, schema_version = get_current_value_pool()
    return schema_version

def update_value_pool(new_pool: List[Dict[str, Any]], actor: str, note: str = ""):
    old_pool, old_version = get_current_value_pool()
    new_version = old_version + 1
    graph_io.update_node_schema(VALUE_NODE_LABEL, new_pool, new_version)
    _log_schema_change(old_pool, new_pool, actor, "update_value_pool", note)
    global _value_pool_cache, _schema_version_cache
    _value_pool_cache = new_pool
    _schema_version_cache = new_version

def add_value_node(name: str, label: str, desc: str, actor: str, importance: float = 0.5) -> Dict[str, Any]:
    pool, _ = get_current_value_pool()
    new_node = _new_value_node(name, label, desc, actor, importance)
    pool.append(new_node)
    update_value_pool(pool, actor, note=f"Added value {name}")
    graph_io.create_node(VALUE_NODE_LABEL, new_node)
    return new_node

def remove_value_node(node_uuid: str, actor: str) -> bool:
    pool, _ = get_current_value_pool()
    found = False
    for v in pool:
        if v["uuid"] == node_uuid:
            v["active"] = False
            found = True
            break
    if not found:
        return False
    update_value_pool(pool, actor, note=f"Removed value {node_uuid}")
    graph_io.update_node(VALUE_NODE_LABEL, node_uuid, {"active": False})
    return True

def edit_value_node(node_uuid: str, actor: str, **fields) -> Optional[Dict[str, Any]]:
    pool, _ = get_current_value_pool()
    for v in pool:
        if v["uuid"] == node_uuid:
            v.update(fields)
            update_value_pool(pool, actor, note=f"Edited value {node_uuid}")
            graph_io.update_node(VALUE_NODE_LABEL, node_uuid, fields)
            return v
    return None

def set_value_importance(node_uuid: str, importance: float, actor: str) -> Optional[Dict[str, Any]]:
    pool, _ = get_current_value_pool()
    for v in pool:
        if v["uuid"] == node_uuid:
            v["importance"] = float(np.clip(importance, 0.0, 1.0))
            update_value_pool(pool, actor, note=f"Changed importance for {node_uuid}")
            graph_io.update_node(VALUE_NODE_LABEL, node_uuid, {"importance": v["importance"]})
            return v
    return None

def decay_all_value_importance(rate: float = 0.01, min_importance: float = 0.01, actor: str = "system"):
    pool, _ = get_current_value_pool()
    changed = False
    for v in pool:
        old = v.get("importance", 0.5)
        new_imp = max(min_importance, old * (1.0 - rate))
        if abs(new_imp - old) > 1e-6:
            v["importance"] = new_imp
            graph_io.update_node(VALUE_NODE_LABEL, v["uuid"], {"importance": new_imp})
            changed = True
            # --- Audit each decay
            rationale = {
                "cause": "decay_value_importance",
                "prev_importance": old,
                "rate": rate,
                "new_importance": new_imp,
                "actor": actor,
                "timestamp": _now()
            }
            audit_log = v.get("audit_log", [])
            if isinstance(audit_log, str):
                try:
                    audit_log = json.loads(audit_log)
                except:
                    audit_log = []
            audit_log.append(rationale)
            graph_io.update_node(VALUE_NODE_LABEL, v["uuid"], {"audit_log": _serialize(audit_log)})
    if changed:
        update_value_pool(pool, actor, note="Decay run on all value importance")

def run_value_decay_cycle(rate: float = 0.01, min_importance: float = 0.01, actor: str = "system"):
    """Shortcut for regular decay (call after each CE or on schedule)."""
    decay_all_value_importance(rate, min_importance, actor)

def load_pool_from_db() -> Tuple[List[Dict[str, Any]], int]:
    pool = graph_io.query_nodes({"label": VALUE_NODE_LABEL, "active": True})
    pool = sorted(pool, key=lambda v: v.get("created_at", ""))
    version = graph_io.get_schema_version(VALUE_NODE_LABEL)
    if version is None:
        version = 1
        graph_io.set_schema_version(VALUE_NODE_LABEL, version)
    return pool, version

def save_pool_to_db():
    pool, version = get_current_value_pool()
    graph_io.update_node_schema(VALUE_NODE_LABEL, pool, version)

def get_audit_log(limit=100) -> List[Dict[str, Any]]:
    logs = graph_io.query_nodes({"label": AUDIT_LOG_NODE_LABEL}, limit=limit)
    for log in logs:
        for k in list(log.keys()):
            log[k] = _parse(log[k])
    return logs

# === VALUE VECTOR EXTRACTION & SCORING ===

def get_value_names() -> List[str]:
    pool, _ = get_current_value_pool()
    return [v["name"] for v in pool if v["active"]]

def get_value_importances() -> Dict[str, float]:
    pool, _ = get_current_value_pool()
    return {v["name"]: v.get("importance", 0.5) for v in pool if v["active"]}

def extract_and_score_value_vector(raw_text: str, context: dict = {}, agent: str = "") -> Dict[str, float]:
    frompool, version = get_current_value_pool()
    axes = [{"name": v["name"], "desc": v["description"]} for v in frompool if v["active"]]
    prompt = build_llm_value_vector_prompt(raw_text, axes, version)
    from .llm_tools import run_llm
    response = run_llm(prompt, agent=agent)
    try:
        scores = json.loads(response)
    except Exception:
        logger.warning(f"LLM extraction failed, raw: {response}")
        raise
    return score_value_vector(scores, agent="llm")

def build_llm_value_vector_prompt(raw_text: str, axes: List[Dict[str, str]], version: int) -> str:
    value_desc = "\n".join([f"- {ax['name']}: {ax['desc']}" for ax in axes])
    prompt = f"""
[Value Vector Extraction v{VALUE_VECTOR_PROMPT_VERSION}.{version}]
System values:
{value_desc}

Task:
Score the following input from 0 to 1 for each value. 0 = not expressed, 1 = strongly expressed. Output valid JSON.

Input: "{raw_text}"
Output JSON: {{"{axes[0]['name'] if axes else 'Compassion'}": 0.5, ...}}
"""
    return prompt

def score_value_vector(input_value, agent: str) -> Dict[str, float]:
    if isinstance(input_value, str):
        try:
            vec = json.loads(input_value)
        except Exception:
            logger.error(f"Could not parse value vector string: {input_value}")
            raise
    else:
        vec = dict(input_value)
    names = get_value_names()
    result = {}
    for name in names:
        val = float(vec.get(name, 0.0))
        result[name] = max(0.0, min(1.0, val))
    return result

def embed_value_vector(node_id: str, vector: Dict[str, float], schema_version: int = None):
    if schema_version is None:
        schema_version = get_value_schema_version()
    updates = {
        VECTOR_FIELD: _serialize(vector),
        SCHEMA_VERSION_FIELD: schema_version
    }
    graph_io.update_node(None, node_id, updates)

def get_node_value_vector(node_id: str) -> Optional[Dict[str, float]]:
    node = graph_io.query_nodes({"id": node_id}, limit=1)
    if not node:
        return None
    vec_str = node[0].get(VECTOR_FIELD)
    if not vec_str:
        return None
    return _parse(vec_str)

# === VALUE IMPORTANCE UPDATE UTILITIES ===

def bump_value_importance(name: str, amount: float = 0.05, max_importance: float = 1.0, actor: str = "system"):
    """
    Increases importance for value 'name'. Robust to missing names; adds audit log.
    """
    pool, _ = get_current_value_pool()
    found = False
    for v in pool:
        if v["name"] == name and v["active"]:
            old = v.get("importance", 0.5)
            new_imp = min(max_importance, old + amount)
            v["importance"] = new_imp
            graph_io.update_node(VALUE_NODE_LABEL, v["uuid"], {"importance": new_imp})
            # --- Audit bump
            rationale = {
                "cause": "bump_value_importance",
                "prev_importance": old,
                "bump_amount": amount,
                "new_importance": new_imp,
                "actor": actor,
                "timestamp": _now()
            }
            audit_log = v.get("audit_log", [])
            if isinstance(audit_log, str):
                try:
                    audit_log = json.loads(audit_log)
                except:
                    audit_log = []
            audit_log.append(rationale)
            graph_io.update_node(VALUE_NODE_LABEL, v["uuid"], {"audit_log": _serialize(audit_log)})
            found = True
    if found:
        update_value_pool(pool, actor, note=f"Bumped importance for {name}")
    else:
        logger.info(f"[value_vector] bump_value_importance: Value '{name}' not found or inactive.")

# === CONFLICT/ALIGNMENT DETECTION & FUSION ===

def value_vector_conflict(vec_a: Dict[str, float], vec_b: Dict[str, float], threshold: float = 0.5) -> Dict[str, Any]:
    names = set(vec_a.keys()) | set(vec_b.keys())
    diffs = {}
    for n in names:
        a = float(vec_a.get(n, 0.0))
        b = float(vec_b.get(n, 0.0))
        diffs[n] = abs(a - b)
    mean_diff = np.mean(list(diffs.values())) if diffs else 0.0
    agreement = 1.0 - mean_diff
    conflict_axes = [n for n, d in diffs.items() if d > threshold]
    peer_review = len(conflict_axes) > 0
    return {
        "conflict_axes": conflict_axes,
        "agreement": round(agreement, 3),
        "max_diff": max(diffs.values()) if diffs else 0.0,
        "peer_review": peer_review,
        "diffs": diffs
    }

def multi_vector_conflict(vectors: List[Dict[str, float]], threshold: float = 0.5) -> Dict[str, Any]:
    if not vectors:
        return {"divergence": [], "conflict_axes": [], "peer_review": False}
    names = list(get_value_names())
    mat = np.zeros((len(vectors), len(names)))
    for i, v in enumerate(vectors):
        for j, n in enumerate(names):
            mat[i, j] = v.get(n, 0.0)
    pairwise_diff = np.abs(mat[:, None, :] - mat[None, :, :])
    axis_conflicts = []
    for idx, name in enumerate(names):
        axis_vals = pairwise_diff[:, :, idx]
        if np.any(axis_vals > threshold):
            axis_conflicts.append(name)
    mean_div = np.mean(pairwise_diff)
    peer_review = len(axis_conflicts) > 0
    return {
        "divergence": pairwise_diff.tolist(),
        "conflict_axes": axis_conflicts,
        "mean_divergence": round(mean_div, 3),
        "peer_review": peer_review
    }

def fuse_value_vectors(vectors: List[Dict[str, float]]) -> Dict[str, float]:
    if not vectors:
        return {}
    names = get_value_names()
    importances = get_value_importances()
    out = {}
    for name in names:
        # Weighted average by value importance
        weighted_scores = [v.get(name, 0.0) * importances.get(name, 0.5) for v in vectors]
        total_weight = sum(importances.get(name, 0.5) for _ in vectors)
        out[name] = float(sum(weighted_scores) / total_weight) if total_weight > 0 else 0.0
    return out

__all__ = [
    "get_current_value_pool",
    "get_value_schema_version",
    "update_value_pool",
    "add_value_node",
    "remove_value_node",
    "edit_value_node",
    "set_value_importance",
    "decay_all_value_importance",
    "run_value_decay_cycle",
    "bump_value_importance",
    "load_pool_from_db",
    "save_pool_to_db",
    "get_audit_log",
    "get_value_names",
    "get_value_importances",
    "extract_and_score_value_vector",
    "score_value_vector",
    "embed_value_vector",
    "get_node_value_vector",
    "value_vector_conflict",
    "multi_vector_conflict",
    "build_llm_value_vector_prompt",
    "fuse_value_vectors"
]
