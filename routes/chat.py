# routes/chat.py — Real-time Chat API (Event Normalization, No SocketIO Emit in REST)
from flask import Blueprint, request, jsonify
from core.memory_engine import store_event
from core.agent_manager import assign_task
from core.logging_engine import log_action
# from core.auth import verify_token  # ⛔️ TEMP DISABLED FOR LOCAL TESTING
import traceback

chat_bp = Blueprint('chat', __name__)

@chat_bp.route('/chat', methods=['POST'])
def chat_with_soul():
    """
    Accept a user message, create event, route to LLM, return response.
    For REST: do NOT emit via socket here! Just return JSON.
    """
    try:
        # TEMP AUTH BYPASS:
        # token = request.headers.get('Authorization', '').replace('Bearer ', '')
        # user = verify_token(token)
        # if 'error' in user:
        #     return jsonify({"error": "Unauthorized"}), 401
        user = {"username": "test_user"}

        data = request.get_json(silent=True)
        if not data or "message" not in data:
            return jsonify({"error": "Malformed or missing JSON body"}), 400

        user_message = data["message"]

        event = store_event(user_message, agent_origin=user["username"])
        if not event or not event.get("id"):
            return jsonify({"error": "Failed to store event"}), 500

        response = assign_task("gpt_writer", user_message, context={})
        log_action("routes/chat", "message", f"User {user['username']} sent message")

        return jsonify({
            "event": event,
            "response": response.get("response", "")
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({
            "error": "Internal Server Error",
            "detail": str(e)
        }), 500

@chat_bp.route('/chat/history', methods=['GET'])
def get_chat_history():
    """
    Return chronological list of recent chat messages/events, normalized.
    """
    try:
        # TEMP AUTH BYPASS:
        # token = request.headers.get('Authorization', '').replace('Bearer ', '')
        # user = verify_token(token)
        # if 'error' in user:
        #     return jsonify({"error": "Unauthorized"}), 401
        user = {"username": "test_user"}

        from core.graph_io import run_read_query
        results = run_read_query("MATCH (e:Event) RETURN e ORDER BY e.timestamp DESC LIMIT 50")

        messages = [
            {
                "text": r["e"].get("raw_text", ""),
                "timestamp": r["e"].get("timestamp", ""),
                "agent_origin": r["e"].get("agent_origin", None),
                "event_id": r["e"].get("id", None),
                "status": r["e"].get("status", None)
            }
            for r in results if isinstance(r, dict) and "e" in r
        ]

        log_action("routes/chat", "history", f"Returned chat history to {user['username']}")

        return jsonify({"history": messages})

    except Exception as e:
        traceback.print_exc()
        return jsonify({
            "error": "Internal Server Error",
            "detail": str(e)
        }), 500
