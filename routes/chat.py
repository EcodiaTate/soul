from flask import Blueprint, request, jsonify
from core import (
    graph_io, context_engine, agents, consensus_engine,
    peer_review_engine, memory_engine, actuators, socket_handlers
)
from uuid import uuid4
from datetime import datetime, timezone

chat_bp = Blueprint('chat', __name__)

@chat_bp.route('/api/chat', methods=['POST'])
def submit_chat():
    data = request.get_json()
    raw_text = data.get("raw_text")
    user_origin = data.get("user_origin", "anonymous")

    # Early validation
    if not raw_text or not raw_text.strip():
        return jsonify({"status": "error", "message": "Missing raw_text"}), 400

    # Step 1: Create Event node
    event_id = str(uuid4())
    timestamp = datetime.now(timezone.utc).isoformat()
    event_node = graph_io.create_node("Event", {
        "id": event_id,
        "raw_text": raw_text,
        "timestamp": timestamp,
        "agent_origin": user_origin,
        "type": "chat",
        "status": "unprocessed"
    })

    # Step 2: Embed + Context
    vector = context_engine.embed_text(raw_text)
    graph_io.embed_vector_in_node(event_id, vector)
    context_blocks = context_engine.load_relevant_context(vector)

    # Step 3: Run Agent Reflections
    agent_responses = []
    for agent in agents.load_agents():
        response = agents.process_event(agent, context_blocks, event_node)
        agent_responses.append(response)
        graph_io.create_node("Rationale", response)

    # Step 4: Consensus or Peer Review (pipeline does both)
    pipeline_result = consensus_engine.consensus_pipeline(event_id, agent_responses)

    # Optionally handle action plans (for actuators)
    if pipeline_result.get("status") == "consensus":
        node = pipeline_result.get("node", {})
        if node.get("action_plan"):
            actuators.dispatch_actuator(node["action_plan"])

    # Choose rationale summary for UI
    if pipeline_result.get("status") == "consensus":
        rationale_summary = pipeline_result.get("node", {}).get("rationale")
    elif pipeline_result.get("status") == "peer_review":
        rationale_summary = "Under peer review—awaiting consensus."
    else:
        rationale_summary = "No consensus reached."

    # Step 5: Memory Evaluation
    memory_engine.evaluate_event(event_id)

    # Step 6: Emit to Frontend (safe fallback if no consensus/rationale)
    socket_handlers.emit_new_event({"id": event_id, "text": raw_text})
    socket_handlers.emit_chat_response({"summary": rationale_summary, "id": event_id})

    # Step 7: Return everything
    return jsonify({
        "status": "ok",
        "event_id": event_id,
        "pipeline_result": pipeline_result,
        "summary": rationale_summary
    })
