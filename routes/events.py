# routes/events.py — Event Ingestion API (Event Return Normalization)
from flask import Blueprint, request, jsonify
from core.memory_engine import store_event
from core.agent_manager import assign_task
from core.auth import verify_token, is_admin
from core.logging_engine import log_action
from core.graph_io import run_read_query

events_bp = Blueprint('events', __name__)

@events_bp.route('/event', methods=['POST'])
def post_event():
    """Receive raw input, embed, store as event, trigger agent response."""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    user = verify_token(token)
    if 'error' in user:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()
    raw_text = data.get("text")
    agent_origin = user.get("username", "unknown")

    event = store_event(raw_text, agent_origin=agent_origin)
    if not event or not isinstance(event, dict) or not event.get("id"):
        return jsonify({"error": "Failed to store event"}), 500

    response = assign_task("gpt_writer", raw_text, context={})
    log_action("routes/events", "post_event", f"Event stored and task assigned for user {agent_origin}")

    # Always return clean event dict, not Neo4j wrapper
    return jsonify({
        "event": event,
        "response": response
    })

@events_bp.route('/events', methods=['GET'])
def get_all_events():
    """Return all stored events (admin only), normalized."""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    user = verify_token(token)
    if 'error' in user or not is_admin(user):
        return jsonify({"error": "Forbidden"}), 403

    # Always unpack Neo4j objects, only return the event dicts
    results = run_read_query("MATCH (e:Event) RETURN e ORDER BY e.timestamp DESC LIMIT 100")
    events = [r["e"] for r in results if "e" in r and isinstance(r["e"], dict)]
    return jsonify({"events": events})

# If you ever add endpoints to fetch a single event by ID,
# always unpack as above:
# result = run_read_query("MATCH (e:Event {id: $id}) RETURN e LIMIT 1", {"id": event_id})
# event = result[0]["e"] if result else None
# return jsonify({"event": event}) if event else ({"error": "Not found"}, 404)
