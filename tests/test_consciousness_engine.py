import pytest
from core import consciousness_engine
import core.graph_io as graph_io  # where run_read_query/write_query are actually defined

@pytest.fixture(autouse=True)
def patch_graph(monkeypatch):
    # Patch graph_io functions used inside consciousness_engine
    monkeypatch.setattr(graph_io, "run_read_query", lambda q, p=None: [{"m": {"id": "mutation1"}}])
    monkeypatch.setattr(graph_io, "run_write_query", lambda q, p=None: {"status": "success"})

    # Patch other local dependencies
    monkeypatch.setattr(consciousness_engine, "create_node", lambda label, props: {"status": "success", "id": "fake"})
    monkeypatch.setattr(consciousness_engine, "create_relationship", lambda *a, **k: True)
    monkeypatch.setattr(consciousness_engine, "update_node_properties", lambda *a, **k: True)
    monkeypatch.setattr(consciousness_engine, "log_action", lambda *a, **k: True)

def test_propose_mutation():
    out = consciousness_engine.propose_mutation("type", {"x": 1}, ["n1"])
    assert isinstance(out, dict)
    assert "mutation_id" in out or "id" in out

def test_evaluate_mutation_impact():
    score = consciousness_engine.evaluate_mutation_impact({"content": "core_value"})
    assert isinstance(score, float)

def test_apply_mutation_if_approved(monkeypatch):
    monkeypatch.setattr(consciousness_engine, "_get_mutation_node", lambda m: {"approved": True, "id": m})
    out = consciousness_engine.apply_mutation_if_approved("mutation1")
    assert isinstance(out, bool)

def test_log_mutation():
    data = {"id": "mut1", "type": "test"}
    ok = consciousness_engine.log_mutation(data)
    assert isinstance(ok, bool)

def test_rollback_last_mutation(monkeypatch):
    monkeypatch.setattr(graph_io, "run_read_query", lambda q, p=None: [{"m": {"id": "mut1"}}])
    ok = consciousness_engine.rollback_last_mutation("revert test")
    assert isinstance(ok, bool)

def test__get_mutation_node():
    node = consciousness_engine._get_mutation_node("mut1")
    assert isinstance(node, dict)
