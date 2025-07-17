# routes/chat.py — Real-time Chat API (Event Normalization, No SocketIO Emit in REST)

from flask import Blueprint, request, jsonify
from core.agent_manager import assign_task
from core.logging_engine import log_action
import traceback

chat_bp = Blueprint('chat', __name__)

# TEMP MOCK FUNCTION TO SIMULATE EVENT CREATION
def store_event(text, agent_origin=None, metadata=None):
    return {
        "id": "event_dummy",
        "raw_text": text,
        "agent_origin": agent_origin,
        "timestamp": "2025-07-17T00:00:00Z",
        "status": "active"
    }


@chat_bp.route('/chat', methods=['POST'])
def chat_with_soul():
    """
    Accept a user message, create event, route to LLM, return response.
    For REST: do NOT emit via socket here! Just return JSON.
    """
    try:
        user = {"username": "test_user"}  # TEMP AUTH BYPASS

        data = request.get_json(silent=True)
        if not data or "message" not in data:
            log_action("routes/chat", "error", "Missing or malformed JSON in /chat POST")
            return jsonify({"error": "Malformed or missing JSON body"}), 400

        user_message = data["message"]

        event = store_event(user_message, agent_origin=user["username"])
        if not event or not event.get("id"):
            log_action("routes/chat", "error", "Failed to store event")
            return jsonify({"error": "Failed to store event"}), 500

        response = assign_task("claude_reflector", user_message, context={}) or {}
        final_reply = response.get("response", "[No response generated]")

        log_action("routes/chat", "message", f"User {user['username']} sent message")

        return jsonify({
            "event": event,
            "response": final_reply
        })

    except Exception as e:
        log_action("routes/chat", "exception", str(e))
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
        user = {"username": "test_user"}  # TEMP AUTH BYPASS

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
        log_action("routes/chat", "exception", str(e))
        traceback.print_exc()
        return jsonify({
            "error": "Internal Server Error",
            "detail": str(e)
        }), 500
