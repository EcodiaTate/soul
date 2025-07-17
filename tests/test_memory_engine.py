# tests/test_memory_engine.py

import pytest
from core import memory_engine

@pytest.fixture(autouse=True)
def patch_core(monkeypatch):
    # Fake embedding
    monkeypatch.setattr(memory_engine, "embed_text", lambda text, model=None: [0.1, 0.2, 0.3])

    # Wrapped mock for write queries
    monkeypatch.setattr(memory_engine, "run_write_query", lambda *a, **k: {
        "status": "success", "result": [{"id": "node1"}]
    })

    # Wrapped mock for read queries with mock node structure
    monkeypatch.setattr(memory_engine, "run_read_query", lambda *a, **k: {
        "status": "success",
        "result": [{"n": {"raw_text": "Sample text"}}]
    })

    # Dummy logger
    monkeypatch.setattr(memory_engine, "log_action", lambda *a, **k: True)

def test_store_event():
    out = memory_engine.store_event("Something happened", agent_origin="agent1", metadata={"k": "v"})
    assert isinstance(out, dict)
    assert "id" in out

def test_store_dream_node():
    out = memory_engine.store_dream_node(["n1", "n2"], notes="Note here")
    assert isinstance(out, dict)

def test_store_timeline_entry():
    out = memory_engine.store_timeline_entry("summary", ["e1"], 0.8, "reasoning")
    assert isinstance(out, dict)

def test_decay_memory():
    ok = memory_engine.decay_memory("node1")
    assert ok is True

def test_summarize_node():
    out = memory_engine.summarize_node("node1")
    assert isinstance(out, str)
    assert out == "Sample text"

def test_archive_node():
    ok = memory_engine.archive_node("node1")
    assert ok is True
