from core.graph_io import run_cypher
import re
from neo4j import GraphDatabase

# Define the most dangerous queries that should never be run by an actuator!
NUKE_PATTERNS = [
    r"\bDETACH\s+DELETE\b",      # Delete with detach
    r"\bMATCH\b.*\bDELETE\b",    # Match-delete any node pattern
    r"\bREMOVE\b.*\bLABEL\b",    # Remove labels
    r"\bDROP\b.*\bDATABASE\b",   # Database drop
    r"\bDELETE\b\s+\w+\b",       # Generic delete
]

def is_safe_cypher(query):
    query_upper = query.upper()
    for pattern in NUKE_PATTERNS:
        if re.search(pattern, query_upper, re.IGNORECASE):
            return False
    return True

def execute(action_plan):
    """
    action_plan["params"]["cypher"] is required.
    Returns: dict with status, result or error.
    """
    cypher_query = action_plan.get("params", {}).get("cypher")
    if not cypher_query:
        return {"status": "error", "error": "No Cypher query provided"}
    if not is_safe_cypher(cypher_query):
        return {"status": "error", "error": "Blocked potentially destructive Cypher action"}

    try:
        result = run_cypher(cypher_query)
        return {"status": "success", "result": result}
    except Exception as e:
        return {"status": "error", "error": str(e)}
