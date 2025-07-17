# tests/test_utils_schema_tools.py

import pytest
from utils import schema_tools

@pytest.fixture(autouse=True)
def patch_core(monkeypatch):
    monkeypatch.setattr("utils.schema_tools.run_read_query", lambda *a, **k: {
        "status": "success", "result": [{"label": "LabelA"}, {"label": "LabelB"}]
    })
    monkeypatch.setattr("utils.schema_tools.run_write_query", lambda *a, **k: {
        "status": "success", "result": [{"migrated_count": 2}]
    })
    monkeypatch.setattr("utils.schema_tools.log_action", lambda *a, **k: True)

def test_list_node_labels():
    out = schema_tools.list_node_labels()
    assert isinstance(out, list)
    assert "LabelA" in out

def test_list_relationship_types():
    out = schema_tools.list_relationship_types()
    assert isinstance(out, list)

def test_find_orphan_nodes():
    out = schema_tools.find_orphan_nodes("LabelA")
    assert isinstance(out, list)

def test_migrate_node_label():
    ok = schema_tools.migrate_node_label("Old", "New")
    assert isinstance(ok, bool)
    assert ok is True
