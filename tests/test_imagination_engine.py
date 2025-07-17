# tests/test_imagination_engine.py

import pytest
from core import imagination_engine

@pytest.fixture(autouse=True)
def patch_core(monkeypatch):
    monkeypatch.setattr(imagination_engine, "create_node", lambda label, props: {"id": "imagine1"})
    monkeypatch.setattr(imagination_engine, "create_relationship", lambda *a, **k: True)
    monkeypatch.setattr(imagination_engine, "run_read_query", lambda q, p=None: [{"id": "node1"}])
    monkeypatch.setattr(imagination_engine, "embed_text", lambda text, model=None: [0.1, 0.2, 0.3])
    monkeypatch.setattr(imagination_engine, "log_action", lambda *a, **k: True)
    monkeypatch.setattr(imagination_engine, "prompt_gpt", lambda prompt, **kwargs: "Imagined scenario")
    monkeypatch.setattr(imagination_engine, "prompt_claude", lambda prompt, **kwargs: "Labeled imagination")

def test_imagine_scenario():
    result = imagination_engine.imagine_scenario("What if?", context_nodes=["n1"])
    assert isinstance(result, dict)

def test_log_imagine_node():
    ok = imagination_engine.log_imagine_node({"id": "imagine1"})
    assert isinstance(ok, bool) or ok is None

def test_simulate_alternatives():
    out = imagination_engine.simulate_alternatives("base_event", num_variants=2)
    assert isinstance(out, list)

def test_get_raw_text():
    text = imagination_engine.get_raw_text("node1")
    assert isinstance(text, str)

def test_label_imagination():
    out = imagination_engine.label_imagination("Prompt?", "Output")
    assert isinstance(out, str)
