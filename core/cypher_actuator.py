import logging
from core.db import get_session

DANGEROUS_COMMANDS = [
    "DELETE *",
    "DETACH DELETE n",
    "DETACH DELETE r",
    "MATCH (n) DETACH DELETE n",
    "MATCH (r) DELETE r",
    "REMOVE ",
    "DROP ",
]

def is_safe_cypher(cypher):
    # Only block *fully* destructive actions, allow prunes/merges/sets by constraint/ID
    c = cypher.strip().upper().replace("\n", " ")
    for forbidden in DANGEROUS_COMMANDS:
        if forbidden in c:
            return False
    return True

def run_cypher_actuator(cypher, meta=None):
    logging.info(f"Received Cypher for execution: {cypher}")
    if not is_safe_cypher(cypher):
        logging.error("Blocked dangerous Cypher command.")
        return False, "Blocked: Dangerous Cypher command detected."
    try:
        with get_session() as session:
            result = session.run(cypher)
            data = [r.data() for r in result]
        logging.info("Cypher executed successfully.")
        return True, data
    except Exception as e:
        logging.error(f"Cypher execution error: {e}")
        return False, str(e)
