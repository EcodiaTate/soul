# tests/test_utils_snapshot.py

import pytest
from utils import snapshot

@pytest.fixture(autouse=True)
def patch_core(monkeypatch):
    monkeypatch.setattr("utils.snapshot.get_current_self_concept", lambda: {"purpose": "test"})
    monkeypatch.setattr("utils.snapshot.initialize_value_vector", lambda base: [0.1, 0.2])
    monkeypatch.setattr("utils.snapshot.get_agent_roster", lambda: [{"id": "agent1"}])
    monkeypatch.setattr("utils.snapshot.run_read_query", lambda *a, **k: {
        "status": "success", "result": [{"summary": "clust1"}]
    })
    monkeypatch.setattr("utils.snapshot.log_action", lambda *a, **k: True)
    monkeypatch.setattr("utils.snapshot.os", __import__("os"))
    monkeypatch.setattr("utils.snapshot.json", __import__("json"))
    monkeypatch.setattr("utils.snapshot.open", lambda *a, **k: type("F", (), {
        "write": lambda self, d: None,
        "read": lambda self: "{}",
        "__enter__": lambda self: self,
        "__exit__": lambda *a: False,
    })())

def test_ensure_snapshot_dir():
    snapshot.ensure_snapshot_dir()
    assert True

def test_take_snapshot():
    out = snapshot.take_snapshot("test")
    assert isinstance(out, dict)
    assert "self_concept" in out

def test_save_snapshot_to_file():
    ok = snapshot.save_snapshot_to_file({"snap": "x"}, "snap.json")
    assert isinstance(ok, bool) or ok is None

def test_load_snapshot():
    out = snapshot.load_snapshot("snap.json")
    assert isinstance(out, dict)
