from flask import Blueprint, request, jsonify
from core import (
    graph_io, context_engine, agents, consensus_engine,
    peer_review_engine, memory_engine, actuators, socket_handlers
)
from uuid import uuid4
from datetime import datetime, timezone
from core.socket_handlers import emit_new_event, emit_chat_response

chat_bp = Blueprint('chat', __name__)

@chat_bp.route('/api/chat', methods=['POST'])
def submit_chat():
    data = request.get_json()
    raw_text = data.get("raw_text")
    user_origin = data.get("user_origin", "anonymous")

    # --- Step 1: Validate ---
    if not raw_text or not raw_text.strip():
        return jsonify({"status": "error", "message": "Missing raw_text"}), 400

    # --- Step 2: Create Event Node ---
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

    # --- Step 3: Embed + Context Blocks ---
    vector = context_engine.embed_text(raw_text)
    graph_io.embed_vector_in_node(event_id, vector)
    context_blocks = context_engine.load_relevant_context(vector)

    # --- Step 4: Agent Mesh (run all agents on event) ---
    agent_responses = agents.run_all_agents({
        "id": event_id,
        "raw_text": raw_text,
        "timestamp": timestamp,
        "context_blocks": context_blocks,
        "event_node": event_node
    })

    # --- Step 5: Consensus/Peer Review Pipeline ---
    pipeline_result = consensus_engine.consensus_pipeline(event_id, agent_responses)
    # pipeline_result: {"status": "consensus"|"peer_review", "node": ..., "review_result": ...}

    # --- Step 6: Parse/prepare all data for UI/emit ---
    # Always parse any dict/list fields for frontend safety
    def parse_fields(obj):
        import json
        # Only parse top-level dict/list fields that are stringified
        if isinstance(obj, dict):
            for k, v in obj.items():
                if isinstance(v, str):
                    try:
                        obj[k] = json.loads(v)
                    except Exception:
                        pass
        return obj

    agent_responses_ui = [parse_fields(dict(r)) for r in agent_responses]
    pipeline_result_ui = parse_fields(dict(pipeline_result.get("node", {}) if pipeline_result.get("node") else {}))
    peer_review_result_ui = parse_fields(dict(pipeline_result.get("review_result", {}) if pipeline_result.get("review_result") else {}))

    # --- Step 7: Memory Evaluation (stub, update as needed) ---
    try:
        memory_engine.evaluate_event(event_id)
    except Exception as e:
        print(f"[chat] Memory evaluation failed: {e}")

    # --- Step 8: Emit to Frontend via Sockets (if used) ---
    emit_new_event({"id": event_id, "text": raw_text})
    emit_chat_response({
        "id": event_id,
        "summary": pipeline_result_ui.get("rationale") or peer_review_result_ui.get("status") or "No consensus yet.",
        "pipeline_result": pipeline_result_ui,
        "peer_review": peer_review_result_ui,
        "agent_responses": agent_responses_ui
    })

    # --- Step 9: Compose Response for API ---
    summary = (
        pipeline_result_ui.get("rationale")
        or peer_review_result_ui.get("status")
        or "No consensus reached."
    )
    response_payload = {
        "status": "ok",
        "event_id": event_id,
        "agent_responses": agent_responses_ui,
        "pipeline_result": pipeline_result_ui,
        "peer_review": peer_review_result_ui,
        "summary": summary
    }
    return jsonify(response_payload)
