# tests/test_philosophy_log.py

import pytest
from core import philosophy_log

@pytest.fixture(autouse=True)
def patch_core(monkeypatch):
    monkeypatch.setattr("core.philosophy_log.create_node", lambda label, props: {"id": "philosophy1"})
    monkeypatch.setattr("core.philosophy_log.run_read_query", lambda q, p=None: {
        "status": "success",
        "result": [
            {"p": {
                "timestamp": "2025-07-16T14:21:00",
                "type": "shift",
                "text": "I updated my worldview.",
                "actor": "Claude"
            }}
        ]
    })
    monkeypatch.setattr("core.philosophy_log.log_action", lambda *a, **k: True)

def test_log_philosophical_shift():
    ok = philosophy_log.log_philosophical_shift("event", "why", actor="tester")
    assert isinstance(ok, bool) or ok is None

def test_get_recent_reflections():
    out = philosophy_log.get_recent_reflections(limit=2)
    assert isinstance(out, list)
    assert "type" in out[0] or out == []

def test_get_philosophical_timeline():
    out = philosophy_log.get_philosophical_timeline(since="2020-01-01")
    assert isinstance(out, list)

def test_export_philosophy_log():
    out = philosophy_log.export_philosophy_log()
    assert isinstance(out, str)
    assert "Claude" in out or len(out) == 0
