# tests/test_deepmind_engine.py

import pytest
from core import deepmind_engine

@pytest.fixture(autouse=True)
def patch_core(monkeypatch):
    monkeypatch.setattr(deepmind_engine, "create_node", lambda label, props: {"status": "success"})
    monkeypatch.setattr(deepmind_engine, "create_relationship", lambda *a, **k: True)
    monkeypatch.setattr(deepmind_engine, "update_self_concept", lambda *a, **k: True)
    monkeypatch.setattr(deepmind_engine, "embed_text", lambda text, model=None: [0.0, 1.0, 2.0])
    monkeypatch.setattr(deepmind_engine, "run_read_query", lambda q, p=None: [{"id": "node1"}])
    monkeypatch.setattr(deepmind_engine, "log_action", lambda *a, **k: True)

def test_run_meta_audit():
    result = deepmind_engine.run_meta_audit()
    assert isinstance(result, dict)

def test_detect_contradictions():
    out = deepmind_engine.detect_contradictions()
    assert isinstance(out, list)

def test_search_for_patterns():
    result = deepmind_engine.search_for_patterns()
    assert isinstance(result, list)

def test_generate_epiphany():
    out = deepmind_engine.generate_epiphany(["n1", "n2"], "insight")
    assert isinstance(out, dict)

def test_log_deepmind_cycle():
    ok = deepmind_engine.log_deepmind_cycle("summary", ["n1", "n2"])
    assert isinstance(ok, bool)
