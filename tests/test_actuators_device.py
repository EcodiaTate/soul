# tests/test_actuators_device.py

import pytest
from core.actuators import device

@pytest.fixture(autouse=True)
def patch_core(monkeypatch):
    monkeypatch.setattr("core.actuators.device.log_action", lambda *a, **k: True)
    monkeypatch.setattr("core.actuators.device.requests", type("MockRequests", (), {
        "post": staticmethod(lambda *a, **k: type("Resp", (), {"status_code": 200})())
    }))
    monkeypatch.setattr("core.actuators.device.json", __import__("json"))

def test_send_signal():
    ok = device.send_signal("dev1", "reboot", {"data": 1})
    assert isinstance(ok, bool)

def test_trigger_environmental_state_change():
    ok = device.trigger_environmental_state_change("state1")
    assert isinstance(ok, bool)

def test_sync_with_sensor_feed():
    out = device.sync_with_sensor_feed("temperature", "http://sensor.url")
    assert isinstance(out, dict)
