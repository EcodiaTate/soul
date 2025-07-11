# actuators/cypher_exec.py

from core.db import run_query

def handle_action(action_plan):
    """
    Executes any Cypher queries proposed in the action plan.
    Expects:
      action_plan = {
        "actions": [
          {"action": "propose_cypher", "cypher": "MATCH (n) RETURN count(n)"}
        ]
      }
    Returns list of results or errors for each query.
    """
    results = []
    actions = action_plan.get("actions", [])
    for act in actions:
        if act.get("action") == "propose_cypher" and "cypher" in act:
            cypher = act["cypher"]
            try:
                res = run_query(cypher)
                results.append({"cypher": cypher, "result": str(res)})
            except Exception as e:
                results.append({"cypher": cypher, "error": str(e)})
    return results
