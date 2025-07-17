import pytest
from core import identity_memory
import core.graph_io as graph_ops

@pytest.fixture(autouse=True)
def patch_graph(monkeypatch):
    monkeypatch.setattr(identity_memory, "create_node", lambda label, props: {"id": "cluster1"})
    monkeypatch.setattr(identity_memory, "create_relationship", lambda *a, **k: True)
    monkeypatch.setattr(identity_memory, "run_read_query", lambda q, p=None: [{"id": "cluster1"}])
    monkeypatch.setattr(identity_memory, "log_action", lambda *a, **k: True)

    # Patch external graph util
    monkeypatch.setattr(graph_ops, "update_node_properties", lambda *a, **k: True)

def test_create_identity_cluster():
    out = identity_memory.create_identity_cluster("Humanity")
    assert isinstance(out, dict)
    assert "id" in out

def test_assign_identity_cluster():
    ok = identity_memory.assign_identity_cluster("node1", "cluster1", confidence=0.9)
    assert isinstance(ok, bool) or ok is None

def test_update_cluster_description():
    ok = identity_memory.update_cluster_description("cluster1", "A new description")
    assert isinstance(ok, bool) or ok is None

def test_get_identity_clusters():
    out = identity_memory.get_identity_clusters()
    assert isinstance(out, list)

def test_trace_identity_shift():
    out = identity_memory.trace_identity_shift("cluster1")
    assert isinstance(out, list)
