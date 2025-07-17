# tests/test_agent_manager.py

import pytest
from core import agent_manager

class DummyModel:
    def __call__(self, prompt, **kwargs):
        return "dummy response"

@pytest.fixture(autouse=True)
def dummy_registry(monkeypatch):
    agent_manager.AGENT_REGISTRY = {}
    yield

def test_register_agent():
    agent_manager.register_agent("test_agent", "reflector", "A test agent", DummyModel())
    assert "test_agent" in agent_manager.AGENT_REGISTRY

def test_assign_task_valid_agent():
    agent_manager.register_agent("test_agent", "reflector", "A test agent", DummyModel())
    result = agent_manager.assign_task("test_agent", "test task", {"context": "info"})
    assert isinstance(result, dict)
    assert "response" in result

def test_assign_task_invalid_agent():
    result = agent_manager.assign_task("no_agent", "task", {})
    assert result is None or "error" in result

def test_run_debate_multiple_agents(monkeypatch):
    agent_manager.register_agent("agent1", "reflector", "desc", DummyModel())
    agent_manager.register_agent("agent2", "reflector", "desc", DummyModel())
    result = agent_manager.run_debate(["agent1", "agent2"], "debate prompt")
    assert isinstance(result, dict)

def test_run_debate_with_judge(monkeypatch):
    agent_manager.register_agent("agent1", "reflector", "desc", DummyModel())
    agent_manager.register_agent("agent2", "reflector", "desc", DummyModel())
    agent_manager.register_agent("judge", "reflector", "desc", DummyModel())
    result = agent_manager.run_debate(["agent1", "agent2"], "debate prompt", judge_id="judge")
    assert isinstance(result, dict)

def test_get_agent_roster():
    agent_manager.register_agent("roster_agent", "reflector", "desc", DummyModel())
    roster = agent_manager.get_agent_roster()
    assert isinstance(roster, list)
    assert any(a["id"] == "roster_agent" for a in roster)

def test_evaluate_agents(monkeypatch):
    agent_manager.register_agent("eval_agent", "reflector", "desc", DummyModel())
    result = agent_manager.evaluate_agents()
    assert isinstance(result, dict)

def test_spawn_role_based_agent():
    agent_id = agent_manager.spawn_role_based_agent("reflector")
    assert isinstance(agent_id, str)
    assert agent_id in agent_manager.AGENT_REGISTRY

def test_get_context_for_agent(monkeypatch):
    # Patch out the Neo4j read
    monkeypatch.setattr(agent_manager, "run_read_query", lambda q, p=None: [{"e": {"id": "event1"}}])
    ctx = agent_manager.get_context_for_agent("some_agent")
    assert "recent_events" in ctx
    assert isinstance(ctx["recent_events"], list)
