from flask import Blueprint, request, jsonify
from core.memory_engine import store_event
from core.agent_manager import assign_task
from core.logging_engine import log_action
from core.auth import verify_token
from flask_socketio import emit

chat_bp = Blueprint('chat', __name__)

@chat_bp.route('/chat', methods=['POST'])
def chat_with_soul():
    """
    Accept a user message, create event in Neo4j, route to LLM agent, return response.
    """
    try:
        # TEMP AUTH BYPASS (swap with real token verification when needed)
        user = {"username": "test_user"}
        # token = request.headers.get("Authorization", "").replace("Bearer ", "")
        # user = verify_token(token)

        data = request.get_json(silent=True)
        if not data or "message" not in data:
            log_action("chat_route", "bad_request", "Missing 'message' in request body")
            return jsonify({"error": "Missing 'message' in request body"}), 400

        user_message = data["message"]

        # Store event in memory graph
        event = store_event(
            raw_text=user_message,
            agent_origin=user["username"]
        )

        # Assign task to selected agent
        response = assign_task(
            agent_id="gpt_writer",  # hardcoded for now; can later rotate agents
            task="respond",
            context={"event": event}
        )

        # Log full interaction
        log_action("chat_route", "message_exchange", f"{user['username']} → {user_message} → {response}")

        # Optionally emit via SocketIO if UI is real-time
        # emit("chat_response", {"user": user["username"], "message": response}, broadcast=True)

        return jsonify({"response": response})

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
