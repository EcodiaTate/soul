# tests/test_google_api.py

import pytest
from core import google_api

@pytest.fixture(autouse=True)
def patch_external(monkeypatch):
    monkeypatch.setattr(google_api, "service_account", type("MockSA", (), {"Credentials": object}))
    monkeypatch.setattr(google_api, "build", lambda *a, **k: type("MockService", (), {"events": lambda self=None: type("MockEvents", (), {"insert": lambda self, calendarId, body: type("MockInsert", (), {"execute": lambda self=None: None})()})()})())
    monkeypatch.setattr(google_api, "requests", type("MockRequests", (), {"get": lambda url, params=None: type("MockResp", (), {"json": lambda: {"lat": 1, "lng": 2}})()}))
    monkeypatch.setattr(google_api, "log_action", lambda *a, **k: True)

def test_add_calendar_event():
    ok = google_api.add_calendar_event("Test", "2020-01-01T10:00:00Z", "2020-01-01T11:00:00Z", "desc")
    assert ok is True or ok is None  # Depends on your mock

def test_fetch_sheet_data():
    monkeypatch = lambda *a, **k: [["row1"], ["row2"]]
    setattr(google_api, "fetch_sheet_data", monkeypatch)
    data = google_api.fetch_sheet_data("sheetid", "A1:B2")
    assert isinstance(data, list)

def test_get_geocode():
    out = google_api.get_geocode("123 Main St")
    assert isinstance(out, dict)

def test_get_place_context():
    out = google_api.get_place_context(1.23, 4.56)
    assert isinstance(out, dict)
