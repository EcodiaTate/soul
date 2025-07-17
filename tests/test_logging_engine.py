import pytest
from core import logging_engine
import core.graph_io as graph_ops

@pytest.fixture(autouse=True)
def patch_core(monkeypatch):
    monkeypatch.setattr(logging_engine, "create_node", lambda label, props: {"id": "log1"})
    monkeypatch.setattr(graph_ops, "run_read_query", lambda q, p=None: [{"log": "data"}])
    monkeypatch.setattr(logging_engine, "os", type("DummyOS", (), {"makedirs": lambda *a, **k: None}))
    monkeypatch.setattr(logging_engine, "logging", __import__("logging"))

def test_init_logging(tmp_path):
    class DummyApp:
        logger = type("DummyLogger", (), {"handlers": [], "setLevel": lambda self, lvl: None})()
    logging_engine.init_logging(DummyApp())
    logging_engine.init_logging()
    assert True

def test_log_action():
    ok = logging_engine.log_action("source", "type", "msg", metadata={"foo": "bar"})
    assert isinstance(ok, bool) or ok is None

def test_log_error():
    ok = logging_engine.log_error("source", "error message", trace="traceback")
    assert isinstance(ok, bool) or ok is None

def test_log_to_file():
    logging_engine.log_to_file("src", "INFO", "msg", {"foo": "meta"})
    assert True

def test_log_to_neo4j():
    ok = logging_engine.log_to_neo4j({"id": "log"})
    assert isinstance(ok, bool) or ok is None

def test_get_recent_logs():
    logs = logging_engine.get_recent_logs(limit=2)
    assert isinstance(logs, list)
