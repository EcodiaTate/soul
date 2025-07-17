import pytest
from core.actuators import gsheet

@pytest.fixture(autouse=True)
def patch_core(monkeypatch):
    # Patch logging function
    monkeypatch.setattr(gsheet, "log_action", lambda *a, **k: True)

    # Patch _get_service with dummy Google Sheets client
    class DummyExecute:
        def execute(self): return {"updates": {"updatedRows": 1}}

    class DummySheet:
        def values(self): return self
        def append(self, spreadsheetId, range, valueInputOption, body): return DummyExecute()

    monkeypatch.setattr(gsheet, "_get_service", lambda: type("Dummy", (), {"spreadsheets": lambda: DummySheet()})())

    # Patch actual usage site if gsheet.py calls timeline_engine.get_timeline_entries
    import core.timeline_engine as timeline_engine
    monkeypatch.setattr(timeline_engine, "get_timeline_entries", lambda limit=50: [
        {"summary": "test", "type": "dream", "timestamp": "now", "significance": 0.9, "linked_nodes": ["a", "b"]}
    ])

def test_append_to_sheet():
    ok = gsheet.append_to_sheet("sheetid", "A1:B2", [["row1"]])
    assert isinstance(ok, bool)

def test_sync_timeline_to_sheet():
    ok = gsheet.sync_timeline_to_sheet("sheetid")
    assert isinstance(ok, bool)

def test_log_value_shift_to_sheet():
    ok = gsheet.log_value_shift_to_sheet("sheetid", {
        "timestamp": "now",
        "type": "shift",
        "summary": "test",
        "significance": 1.0,
        "linked_nodes": []
    })
    assert isinstance(ok, bool)
