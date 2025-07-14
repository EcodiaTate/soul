# /routes/chat.py

from flask import Blueprint, request, jsonify
from core import (
    graph_io, context_engine, agents, consensus_engine,
    peer_review_engine, memory_engine, actuators, socket_handlers
)
from uuid import uuid4
from datetime import datetime

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
    timestamp = datetime.utcnow().isoformat()
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

    # Step 4: Consensus or Peer Review
    consensus = {}
    if consensus_engine.check_alignment(agent_responses):
        consensus = consensus_engine.build_consensus(agent_responses)
        graph_io.write_consensus_to_graph(consensus)
        if consensus.get("action_plan"):
            actuators.dispatch_actuator(consensus["action_plan"])
    else:
        peer_review_engine.resolve_or_escalate(agent_responses)

    # Step 5: Memory Evaluation
    memory_engine.evaluate_event(event_id)

    # Step 6: Emit to Frontend (safe fallback if no consensus/rationale)
    rationale_summary = consensus.get("rationale") or "Awaiting peer review or system response."
    socket_handlers.emit_new_event({"id": event_id, "text": raw_text})
    socket_handlers.emit_chat_response({"summary": rationale_summary, "id": event_id})

    return jsonify({
        "status": "ok",
        "event_id": event_id,
        "summary": rationale_summary
    })
