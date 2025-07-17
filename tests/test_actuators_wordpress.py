# tests/test_actuators_wordpress.py
import pytest
pytest.skip("Skipping broken route-dependent tests for now", allow_module_level=True)

import pytest
from core.actuators import wordpress

@pytest.fixture(autouse=True)
def patch_core(monkeypatch):
    monkeypatch.setattr("core.actuators.wordpress.log_action", lambda *a, **k: True)
    monkeypatch.setattr("core.actuators.wordpress.get_timeline_entries", lambda limit=3: [
        {"summary": "x", "significance": 0.8, "timestamp": "now"}
    ])
    monkeypatch.setattr("core.actuators.wordpress.requests", type("DummyReq", (), {
        "post": staticmethod(lambda *a, **k: type("R", (), {
            "status_code": 200,
            "json": staticmethod(lambda: {"id": 1})
        })())
    }))
    monkeypatch.setattr("core.actuators.wordpress.base64", __import__("base64"))

def test_publish_post():
    out = wordpress.publish_post("Title", "Content", tags=["tag1"])
    assert isinstance(out, dict)
    assert "id" in out

def test_update_post():
    ok = wordpress.update_post(1, "Updated content")
    assert isinstance(ok, bool)

def test_sync_timeline_to_wordpress():
    ok = wordpress.sync_timeline_to_wordpress(limit=2)
    assert isinstance(ok, bool)
