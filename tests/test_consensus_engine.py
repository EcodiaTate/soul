import pytest
from core import consensus_engine
import core.graph_io as graph_io  # where run_write_query is defined

@pytest.fixture(autouse=True)
def patch_core(monkeypatch):
    # Patch actual graph I/O layer
    monkeypatch.setattr(graph_io, "run_write_query", lambda *a, **k: {"status": "success"})

    # Patch local consensus_engine functions
    monkeypatch.setattr(consensus_engine, "initiate_peer_review", lambda e, a: {"status": "reviewed"})
    monkeypatch.setattr(consensus_engine, "create_node", lambda label, props: {"status": "success"})
    monkeypatch.setattr(consensus_engine, "create_relationship", lambda *a, **k: True)
    monkeypatch.setattr(consensus_engine, "log_action", lambda *a, **k: True)

def test_synthesize_consensus():
    event_id = "event123"
    agent_outputs = [{"output": "yes"}, {"output": "no"}]
    result = consensus_engine.synthesize_consensus(event_id, agent_outputs)
    assert isinstance(result, dict)

def test_score_consensus():
    rationales = ["A good reason.", "A bad reason."]
    score = consensus_engine.score_consensus(rationales)
    assert isinstance(score, float)

def test_log_consensus():
    ok = consensus_engine.log_consensus("event123", {"result": "pass"}, "Rationale here.")
    assert isinstance(ok, bool)

def test_escalate_if_conflict():
    event_id = "event123"
    agent_outputs = [{"output": "yes"}, {"output": "no"}]
    ok = consensus_engine.escalate_if_conflict(event_id, agent_outputs)
    assert isinstance(ok, bool)
