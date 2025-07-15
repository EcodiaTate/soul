# routes/chat.py — GOD MODE
# Chat intake > vector embed > memory/context > agent mesh > consensus > instant reply

from flask import Blueprint, request, jsonify
from uuid import uuid4
from datetime import datetime, timezone

from core import (
    graph_io,
    context_engine,
    agents,
    consensus_engine,
    memory_engine,
    socket_handlers
)
from core.chat_agent import generate_chat_reply
from core.socket_handlers import emit_new_event, emit_chat_response

chat_bp = Blueprint('chat', __name__)

@chat_bp.route('/api/chat', methods=['POST'])
def submit_chat():
    data = request.get_json()
    raw_text = data.get("raw_text")
    user_origin = data.get("user_origin", "anonymous")

    # --- Step 1: Validate Input ---
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

    # --- Step 3: Embed + Context Block Extraction ---
    vector = context_engine.embed_text(raw_text)
    graph_io.embed_vector_in_node(event_id, vector)
    context_blocks = context_engine.load_relevant_context(vector)

    # --- Step 4: Fast Chat Response (Claude agent) ---
    try:
        chat_reply = generate_chat_reply(raw_text, context_blocks)
        emit_chat_response({"id": event_id, "reply": chat_reply})
    except Exception as e:
        print(f"[chat] Failed to generate fast chat reply: {e}")
        chat_reply = "..."  # Fallback placeholder

    # --- Step 5: Full Agent Mesh ---
    agent_responses = agents.run_all_agents({
        "id": event_id,
        "raw_text": raw_text,
        "timestamp": timestamp,
        "context_blocks": context_blocks,
        "event_node": event_node
    })

    # --- Step 6: Consensus Pipeline ---
    pipeline_result = consensus_engine.consensus_pipeline(event_id, agent_responses)

    # --- Step 7: Parse Output Fields for Safety ---
    def parse_fields(obj):
        import json
        if isinstance(obj, dict):
            for k, v in obj.items():
                if isinstance(v, str):
                    try:
                        obj[k] = json.loads(v)
                    except:
                        pass
        return obj

    agent_responses_ui = [parse_fields(dict(r)) for r in agent_responses]
    pipeline_result_ui = parse_fields(dict(pipeline_result.get("node", {}) if pipeline_result.get("node") else {}))
    peer_review_result_ui = parse_fields(dict(pipeline_result.get("review_result", {}) if pipeline_result.get("review_result") else {}))

    # --- Step 8: Memory Evaluation (non-blocking) ---
    try:
        memory_engine.evaluate_event(event_id)
    except Exception as e:
        print(f"[chat] Memory evaluation failed: {e}")

    # --- Step 9: Emit via WebSocket ---
    socket_handlers.emit_new_event({"id": event_id, "text": raw_text})
    socket_handlers.emit_chat_response({
        "id": event_id,
        "summary": pipeline_result_ui.get("rationale") or peer_review_result_ui.get("status") or "No consensus yet.",
        "pipeline_result": pipeline_result_ui,
        "peer_review": peer_review_result_ui,
        "agent_responses": agent_responses_ui
    })

    # --- Step 10: Return Full API Response ---
    summary = (
        pipeline_result_ui.get("rationale")
        or peer_review_result_ui.get("status")
        or "No consensus reached."
    )
    return jsonify({
        "status": "ok",
        "event_id": event_id,
        "agent_responses": agent_responses_ui,
        "pipeline_result": pipeline_result_ui,
        "peer_review": peer_review_result_ui,
        "summary": summary
    })
