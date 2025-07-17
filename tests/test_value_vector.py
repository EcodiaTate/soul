# tests/test_value_vector.py

import pytest
from core import value_vector

@pytest.fixture(autouse=True)
def patch_core(monkeypatch):
    monkeypatch.setattr("core.value_vector.update_node_properties", lambda *a, **k: True)
    monkeypatch.setattr("core.value_vector.get_node_by_id", lambda node_id: {
        "id": node_id,
        "vector": [0.1] * len(value_vector.default_value_profile)
    })
    monkeypatch.setattr("core.value_vector.log_action", lambda *a, **k: True)

def test_initialize_value_vector():
    base = {"altruism": 1.0, "logic": 0.5}
    vec = value_vector.initialize_value_vector(base)
    assert isinstance(vec, list)
    assert all(isinstance(v, float) for v in vec)

def test_update_value_vector():
    vec = value_vector.update_value_vector("node1", {"altruism": 0.8})
    assert isinstance(vec, list)

def test_compare_values():
    dim = len(value_vector.default_value_profile)
    a = [0.2] * dim
    b = [0.1] * dim
    similarity = value_vector.compare_values(a, b)
    assert isinstance(similarity, float)

def test_detect_value_drift():
    dim = len(value_vector.default_value_profile)
    original = [0.5] * dim
    current = [0.7] * dim
    drift = value_vector.detect_value_drift(original, current)
    assert isinstance(drift, float)

def test_apply_value_influence():
    ok = value_vector.apply_value_influence("agent1", "value1")
    assert isinstance(ok, bool) or ok is None
