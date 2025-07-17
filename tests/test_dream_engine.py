import pytest
from core import dream_engine
import core.llm_tools as llm

@pytest.fixture(autouse=True)
def patch_core(monkeypatch):
    monkeypatch.setattr(dream_engine, "create_node", lambda label, props: {"status": "success", "id": "dream1"})
    monkeypatch.setattr(dream_engine, "create_relationship", lambda *a, **k: True)
    monkeypatch.setattr(dream_engine, "embed_text", lambda text, model=None: [0.1, 0.2, 0.3])
    monkeypatch.setattr(dream_engine, "run_read_query", lambda q, p=None: [{"id": "event1"}])
    monkeypatch.setattr(dream_engine, "log_action", lambda *a, **k: True)

    # Correct location for LLM call
    monkeypatch.setattr(llm, "prompt_claude", lambda text, **kwargs: "Dream idea")

def test_generate_dream():
    out = dream_engine.generate_dream(["n1", "n2"], "trigger")
    assert isinstance(out, dict)

def test_select_dream_seeds():
    seeds = dream_engine.select_dream_seeds(limit=2)
    assert isinstance(seeds, list)

def test_score_dream_significance():
    score = dream_engine.score_dream_significance(["id1", "id2"])
    assert isinstance(score, float)

def test_log_dream():
    ok = dream_engine.log_dream({"id": "dream1"})
    assert isinstance(ok, bool)

def test_get_dream_by_id():
    out = dream_engine.get_dream_by_id("dream1")
    assert isinstance(out, dict)

def test_get_recent_dreams():
    out = dream_engine.get_recent_dreams()
    assert isinstance(out, list)

def test_get_raw_text():
    text = dream_engine.get_raw_text("node1")
    assert isinstance(text, str)

def test_synthesize_dream_idea():
    out = dream_engine.synthesize_dream_idea("raw text")
    assert isinstance(out, str)
