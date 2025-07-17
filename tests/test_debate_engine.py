import pytest
from core import debate_engine
import core.graph_io as graph_io  # run_write_query is actually here

@pytest.fixture(autouse=True)
def patch_core(monkeypatch):
    # Patch actual graph layer
    monkeypatch.setattr(graph_io, "run_write_query", lambda *a, **k: {"status": "success"})

    # Patch local dependencies
    monkeypatch.setattr(debate_engine, "assign_task", lambda agent_id, task, ctx: {"response": "mock"})
    monkeypatch.setattr(debate_engine, "create_node", lambda label, props: {"status": "success"})
    monkeypatch.setattr(debate_engine, "create_relationship", lambda *a, **k: True)
    monkeypatch.setattr(debate_engine, "log_action", lambda *a, **k: True)

def test_launch_debate():
    prompt = "Is AI good?"
    participants = ["agent1", "agent2"]
    result = debate_engine.launch_debate(prompt, participants)
    assert isinstance(result, dict)

def test_record_argument():
    out = debate_engine.record_argument("agent1", 1, "argument text")
    assert out is None or out is True

def test_resolve_debate(monkeypatch):
    monkeypatch.setattr(debate_engine, "get_node_by_id", lambda debate_id: {"id": debate_id})
    result = debate_engine.resolve_debate("debate123", judge_agent="judge1")
    assert isinstance(result, dict)

def test_log_debate_outcome():
    ok = debate_engine.log_debate_outcome("debate123", "summary", "consensus")
    assert isinstance(ok, bool)
