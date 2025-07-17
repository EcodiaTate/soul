# tests/test_timeline_engine.py

import pytest
from core import timeline_engine

@pytest.fixture(autouse=True)
def patch_core(monkeypatch):
    monkeypatch.setattr("core.timeline_engine.create_node", lambda label, props: {"id": "timeline1"})
    monkeypatch.setattr("core.timeline_engine.create_relationship", lambda *a, **k: True)
    monkeypatch.setattr("core.timeline_engine.embed_text", lambda text, model=None: [0.1, 0.2])
    monkeypatch.setattr("core.timeline_engine.log_action", lambda *a, **k: True)
    monkeypatch.setattr("core.timeline_engine.prompt_claude", lambda prompt, **kwargs: "Philosophy log")
    monkeypatch.setattr("core.timeline_engine.run_read_query", lambda *a, **k: {
        "status": "success", "result": [{"id": "entry1", "summary": "x"}]
    })

def test_summarize_sequence():
    out = timeline_engine.summarize_sequence(["node1", "node2"], title="test")
    assert isinstance(out, dict)

def test_add_philosophy_log():
    out = timeline_engine.add_philosophy_log("sum", ["node1"], rationale="r", impact=1.0)
    assert isinstance(out, dict)

def test_create_timeline_entry():
    out = timeline_engine.create_timeline_entry("sum", ["n1"], "why", 0.8)
    assert isinstance(out, dict)

def test_log_timeline_shift():
    ok = timeline_engine.log_timeline_shift("event1", impact="high")
    assert isinstance(ok, bool)

def test_get_timeline_entries():
    out = timeline_engine.get_timeline_entries(limit=2)
    assert isinstance(out, list)

def test_get_timeline_entry_by_id():
    out = timeline_engine.get_timeline_entry_by_id("entry1")
    assert isinstance(out, dict)

def test_get_raw_text():
    text = timeline_engine.get_raw_text("node1")
    assert isinstance(text, str)
