# tests/test_peer_review_engine.py

import pytest
from core import peer_review_engine

@pytest.fixture(autouse=True)
def patch_core(monkeypatch):
    monkeypatch.setattr(peer_review_engine, "assign_task", lambda agent_id, task, ctx: {"response": "mock"})
    monkeypatch.setattr(peer_review_engine, "create_node", lambda label, props: {"id": "peer_review1"})
    monkeypatch.setattr(peer_review_engine, "create_relationship", lambda *a, **k: True)
    monkeypatch.setattr(peer_review_engine, "run_read_query", lambda q, p=None: [{"id": "review1"}])
    monkeypatch.setattr(peer_review_engine, "log_action", lambda *a, **k: True)

def test_initiate_peer_review():
    result = peer_review_engine.initiate_peer_review("event1", ["agent1", "agent2"])
    assert isinstance(result, dict)

def test_critique_rationale():
    target_node = {"id": "node1"}
    result = peer_review_engine.critique_rationale("agent1", target_node)
    assert isinstance(result, dict)

def test_evaluate_peer_consensus():
    reviews = [{"id": "r1"}, {"id": "r2"}]
    result = peer_review_engine.evaluate_peer_consensus(reviews)
    assert isinstance(result, dict)

def test_escalate_if_unresolved():
    result = peer_review_engine.escalate_if_unresolved("event1")
    assert isinstance(result, bool)
