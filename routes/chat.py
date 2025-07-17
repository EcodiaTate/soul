from flask import Blueprint, request, jsonify
from core.memory_engine import store_event
from core.agent_manager import assign_task
from core.logging_engine import log_action
from core.auth import verify_token
from flask_socketio import emit

chat_bp = Blueprint('chat', __name__)

@chat_bp.route('/chat', methods=['POST'])
@chat_bp.route('/chat', methods=['POST'])
def chat_with_soul():
    """
    Accept a user message, create event in Neo4j, route to LLM agent, return response.
    """
    try:
        # TEMP AUTH BYPASS (swap with real token verification when ready)
        user = {"username": "test_user"}
        # token = request.headers.get("Authorization", "").replace("Bearer ", "")
        # user = verify_token(token)

        data = request.get_json(silent=True)
        if not data or "message" not in data:
            log_action("chat_route", "bad_request", "Missing 'message' in request body")
            return jsonify({"error": "Missing 'message' in request body"}), 400

        user_message = data["message"]

        # Store event
        event = store_event(
            raw_text=user_message,
            agent_origin=user["username"]
        )

        # Assign task to agent
        response_obj = assign_task(
            agent_id="claude_reflector",
            task="respond",
            context={"event": event}
        )

        # Handle agent failure
        if isinstance(response_obj, dict) and "error" in response_obj:
            log_action("chat_route", "agent_error", str(response_obj["error"]))
            return jsonify({"response": response_obj}), 500

        # Log and return
        final_response = response_obj.get("response") if isinstance(response_obj, dict) else str(response_obj)
        log_action("chat_route", "message_exchange", f"{user['username']} → {user_message} → {final_response}")
        return jsonify({"response": final_response})

    except Exception as e:
        import traceback
        traceback.print_exc()
        log_action("chat_route", "server_error", str(e))
        return jsonify({"error": "Internal server error"}), 500


@chat_bp.route('/chat/history', methods=['GET'])
def get_chat_history():
    """
    Return chronological list of recent chat messages/events (stub).
    """
    return jsonify({"history": []})  # TODO: implement when chat memory UI is ready
