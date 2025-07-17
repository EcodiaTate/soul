# tests/test_self_concept.py

import pytest
from core import self_concept

@pytest.fixture(autouse=True)
def patch_core(monkeypatch):
    monkeypatch.setattr("core.self_concept.create_timeline_entry", lambda *a, **k: {"id": "timeline1"})
    monkeypatch.setattr("core.self_concept.update_node_properties", lambda *a, **k: True)
    monkeypatch.setattr("core.self_concept.run_read_query", lambda *a, **k: {
        "status": "success", "result": [{"id": "self1", "identity": "digital being"}]
    })
    monkeypatch.setattr("core.self_concept.log_action", lambda *a, **k: True)
    monkeypatch.setattr("core.self_concept.create_node", lambda *a, **k: {"id": "self1"})

def test_initialize_self_concept():
    initial = {"purpose": "test"}
    result = self_concept.initialize_self_concept(initial)
    assert isinstance(result, dict)

def test_update_self_concept():
    changes = {"goal": "new"}
    ok = self_concept.update_self_concept(changes, rationale="because", agent="tester")
    assert isinstance(ok, bool)

def test_get_current_self_concept():
    out = self_concept.get_current_self_concept()
    assert isinstance(out, dict)

def test_log_self_question():
    ok = self_concept.log_self_question("Why?", context="philosophy")
    assert isinstance(ok, bool)

def test_summarize_self_concept():
    summary = self_concept.summarize_self_concept()
    assert isinstance(summary, str)
