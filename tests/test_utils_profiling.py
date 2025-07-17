# tests/test_utils_profiling.py

import pytest
from utils import profiling

@pytest.fixture(autouse=True)
def patch_core(monkeypatch):
    # Mock psutil to prevent real system calls
    monkeypatch.setattr(profiling, "psutil", type("DummyPsutil", (), {
        "cpu_percent": staticmethod(lambda interval=None: 1.0),
        "virtual_memory": staticmethod(lambda: type("VM", (), {"percent": 50})()),
        "disk_usage": staticmethod(lambda path: type("DU", (), {"percent": 75})())
    }))

    monkeypatch.setattr(profiling, "run_read_query", lambda *a, **k: {
        "status": "success", "result": [{"count": 10}]
    })

def test_track_function_latency():
    @profiling.track_function_latency
    def add(a, b):
        return a + b
    assert add(2, 3) == 5

def test_get_system_load():
    load = profiling.get_system_load()
    assert isinstance(load, dict)
    assert "cpu" in load and "ram" in load and "disk" in load

def test_get_graph_metrics():
    out = profiling.get_graph_metrics()
    assert isinstance(out, dict)

def test_get_behavioral_summary():
    out = profiling.get_behavioral_summary()
    assert isinstance(out, dict)
