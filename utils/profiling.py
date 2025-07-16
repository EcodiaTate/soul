# utils/profiling.py — System Performance & Behavior Tracker
import time
import psutil
import os
from functools import wraps
from core.graph_io import run_read_query
from datetime import datetime
from core.logging_engine import log_action

PERF_LOG_DIR = "logs"
PERF_LOG_FILE = os.path.join(PERF_LOG_DIR, "performance.log")
tracked_metrics = ["dreams_per_day", "contradiction_ratio", "epiphanies_per_week"]

def ensure_perf_log_dir():
    """Ensure the logs directory exists before any writes."""
    try:
        os.makedirs(PERF_LOG_DIR, exist_ok=True)
    except Exception as e:
        print(f"[PERF LOG DIR ERROR] Could not create logs directory: {e}")

# Ensure log dir at module import (covers first write, new installs, and cold starts)
ensure_perf_log_dir()

# --- Decorator to measure function latency ---
def track_function_latency(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        end = time.perf_counter()
        latency_ms = (end - start) * 1000
        log_action("profiling", "latency", f"{func.__name__} took {latency_ms:.2f} ms")
        try:
            ensure_perf_log_dir()
            with open(PERF_LOG_FILE, "a") as f:
                f.write(f"{datetime.utcnow().isoformat()} {func.__name__} took {latency_ms:.2f} ms\n")
        except Exception as e:
            print(f"[PERF LOG ERROR] Could not write latency: {e}")
        return result
    return wrapper

# --- System resource load ---
def get_system_load() -> dict:
    """Return current CPU, RAM, disk stats."""
    cpu = psutil.cpu_percent(interval=1)
    ram = psutil.virtual_memory().percent
    disk = psutil.disk_usage('/').percent
    log_action("profiling", "system_load", f"CPU: {cpu}%, RAM: {ram}%, Disk: {disk}%")
    try:
        ensure_perf_log_dir()
        with open(PERF_LOG_FILE, "a") as f:
            f.write(f"{datetime.utcnow().isoformat()} CPU: {cpu}% RAM: {ram}% Disk: {disk}%\n")
    except Exception as e:
        print(f"[PERF LOG ERROR] Could not write system load: {e}")
    return {"cpu_percent": cpu, "ram_percent": ram, "disk_percent": disk}

# --- Graph Metrics ---
def get_graph_metrics() -> dict:
    """Return number of events, dreams, agents, and timeline entries."""
    counts = {}
    for label in ["Event", "Dream", "TimelineEntry", "Agent"]:
        query = f"MATCH (n:{label}) RETURN count(n) AS count"
        result = run_read_query(query)
        counts[label] = result[0]["count"] if result else 0
    log_action("profiling", "graph_metrics", f"Graph counts: {counts}")
    try:
        ensure_perf_log_dir()
        with open(PERF_LOG_FILE, "a") as f:
            f.write(f"{datetime.utcnow().isoformat()} GRAPH_COUNTS: {counts}\n")
    except Exception as e:
        print(f"[PERF LOG ERROR] Could not write graph metrics: {e}")
    return counts

# --- Behavioral Summary ---
def get_behavioral_summary() -> dict:
    """Return insights like dream frequency, epiphany rate, contradiction density."""
    # Placeholder: Needs historical event data or advanced analytics
    summary = {
        "dreams_per_day": 5,
        "epiphanies_per_week": 2,
        "contradiction_ratio": 0.1
    }
    log_action("profiling", "behavioral_summary", f"Behavioral summary: {summary}")
    try:
        ensure_perf_log_dir()
        with open(PERF_LOG_FILE, "a") as f:
            f.write(f"{datetime.utcnow().isoformat()} BEHAVIORAL_SUMMARY: {summary}\n")
    except Exception as e:
        print(f"[PERF LOG ERROR] Could not write behavioral summary: {e}")
    return summary
