# /core/consciousness_engine.py

def process_pending_cypher_actions():
    """
    Find all consensus nodes/events with pending cypher action plans,
    execute them safely, log results, and update system.
    """
    # Import all patchable dependencies INSIDE the function for monkeypatching/testing.
    from core.actuators.cypher import execute as cypher_execute
    from core.graph_io import (
        get_pending_cypher_actions,   
        mark_action_executed,         
        create_schema_change_node
    )
    from core.socket_handlers import emit_action_update

    print("[consciousness_engine] Scanning for pending cypher actions...")
    pending = get_pending_cypher_actions()  # Returns [(action_plan, consensus_node), ...]
    if not pending:
        print("[consciousness_engine] No pending cypher actions found.")
        return

    for action_plan, consensus_node in pending:
        print(f"[consciousness_engine] Executing cypher action for consensus node {consensus_node.get('id', '[no id]')}")
        result = cypher_execute(action_plan)

        # Mark action as executed to prevent rerun (attach a flag/property in Neo4j)
        mark_action_executed(consensus_node.get("id"), action_plan)

        # Log this mutation as a SchemaChange node
        schema_change = create_schema_change_node(action_plan, result, consensus_node.get("id"))

        # Emit to socket for frontend logging
        emit_action_update({
            "type": "cypher",
            "status": result.get("status"),
            "details": result.get("result", result.get("error", "")),
            "consensus_node_id": consensus_node.get("id"),
            "schema_change_id": schema_change.get("id")
        })

        print(f"[consciousness_engine] Cypher action processed: {result.get('status')}")

    print(f"[consciousness_engine] All pending cypher actions processed.\n")

# (Optional) You can call this manually, or schedule it via a background task.
# Example: from app.py, call after consensus or every N seconds.
