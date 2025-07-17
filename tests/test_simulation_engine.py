# tests/test_simulation_engine.py

import pytest
from core import simulation_engine

@pytest.fixture(autouse=True)
def patch_core(monkeypatch):
    monkeypatch.setattr("core.simulation_engine.create_node", lambda label, props: {"id": "simnode"})
    monkeypatch.setattr("core.simulation_engine.create_relationship", lambda *a, **k: True)
    monkeypatch.setattr("core.simulation_engine.summarize_sequence", lambda node_ids, title=None: {"summary": "test"})
    monkeypatch.setattr("core.simulation_engine.prompt_gpt", lambda prompt, **kwargs: "Simulated answer")
    monkeypatch.setattr("core.simulation_engine.run_read_query", lambda *a, **k: {
        "status": "success", "result": [{"id": "ev1", "summary": "test"}]
    })
    monkeypatch.setattr("core.simulation_engine.log_action", lambda *a, **k: True)

def test_simulate_timeline_change():
    out = simulation_engine.simulate_timeline_change("event1", mutation={"type": "change"})
    assert isinstance(out, dict)

def test_simulate_policy_shift():
    out = simulation_engine.simulate_policy_shift({"policy": 1.0}, ["test_scope"])
    assert isinstance(out, dict)

def test_generate_simulated_node():
    out = simulation_engine.generate_simulated_node([{"id": "node1"}])
    assert isinstance(out, dict)

def test_log_simulation():
    ok = simulation_engine.log_simulation({"data": "sim"})
    assert isinstance(ok, bool)

def test_get_event_summary():
    summary = simulation_engine.get_event_summary("event1")
    assert isinstance(summary, str)
