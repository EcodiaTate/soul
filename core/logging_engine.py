# core/logging_engine.py — Universal Action & Audit Logger
import logging
import os
from datetime import datetime
import traceback
from core.graph_io import create_node

# --- Config ---
LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "system.log")

import logging
import os

LOG_FILE = "logs/system.log"

def init_logging(app=None):
    """Initializes logging to file and (optionally) Flask app logger."""
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(LOG_FILE, encoding="utf-8"),
            logging.StreamHandler()
        ]
    )
    if app:  # If a Flask app is provided, hook into its logger too.
        app.logger.handlers = logging.getLogger().handlers
        app.logger.setLevel(logging.INFO)

def ensure_log_dir():
    """Ensure the logs directory exists before writing any logs."""
    try:
        os.makedirs(LOG_DIR, exist_ok=True)
    except Exception as e:
        # If log dir fails, fallback: print to stderr (cannot log this error)
        print(f"[LOGGING INIT ERROR] Failed to create log dir: {e}")

# Ensure log directory exists at import/startup (for first and all subsequent writes)
ensure_log_dir()

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    filemode="a"
)

# --- Action Logging ---
def log_action(source: str, action_type: str, message: str, metadata: dict = None) -> bool:
    """Record a standard action taken by the system or an agent."""
    timestamp = datetime.utcnow().isoformat()
    log_data = {
        "id": f"log_{source}_{int(datetime.utcnow().timestamp())}",
        "source": source,
        "type": action_type,
        "message": message,
        "metadata": metadata or {},
        "timestamp": timestamp
    }

    log_to_file(source, action_type, message, log_data["metadata"])
    return log_to_neo4j(log_data)

def log_error(source: str, error_message: str, trace: str = "") -> bool:
    """Log an error, including stack trace if applicable."""
    log_data = {
        "id": f"error_{source}_{int(datetime.utcnow().timestamp())}",
        "source": source,
        "type": "error",
        "message": error_message,
        "metadata": {"trace": trace},
        "timestamp": datetime.utcnow().isoformat()
    }

    log_to_file(source, "ERROR", error_message, {"trace": trace})
    return log_to_neo4j(log_data)

def log_to_file(source: str, level: str, message: str, meta: dict) -> None:
    """Write a message to local system.log. Ensures directory exists every write."""
    try:
        ensure_log_dir()
        if level.lower() == "error":
            logging.error(f"[{source}] {message} | {meta}")
        else:
            logging.info(f"[{source}] {level}: {message} | {meta}")
    except Exception as e:
        # Last resort: print to stderr if even logging fails
        print(f"[LOGGING WRITE ERROR] Could not log to file: {e}")

def log_to_neo4j(log_data: dict) -> bool:
    """Store log entries as nodes in the graph for temporal queries."""
    return create_node("SystemLog", log_data)["status"] == "success"

def get_recent_logs(limit: int = 50) -> list[dict]:
    """Retrieve recent logs for admin display or debugging."""
    from core.graph_io import run_read_query
    query = """
    MATCH (l:SystemLog)
    RETURN l
    ORDER BY l.timestamp DESC
    LIMIT $limit
    """
    return run_read_query(query, {"limit": limit})
