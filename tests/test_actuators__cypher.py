# tests/test_actuators_cypher.py

import pytest
from core.actuators import cypher

@pytest.fixture(autouse=True)
def patch_core(monkeypatch):
    monkeypatch.setattr("core.actuators.cypher.run_write_query", lambda cmd, params=None: {"status": "success", "result": [{"id": "x"}]})
    monkeypatch.setattr("core.actuators.cypher.create_node", lambda label, props: {"id": "log1"})
    monkeypatch.setattr("core.actuators.cypher.log_action", lambda *a, **k: True)

def test_execute_cypher():
    result = cypher.execute_cypher("CREATE (n:Test)", {"foo": "bar"})
    assert isinstance(result, dict)
    assert result["status"] == "success"

def test_mutate_schema():
    ok = cypher.mutate_schema(["NewLabel"], ["NEW_REL"])
    assert ok is True

def test_merge_identity_clusters():
    ok = cypher.merge_identity_clusters("clusterA", "clusterB")
    assert isinstance(ok, bool)
