# routes/timeline.py — Timeline Narrative API
from flask import Blueprint, request, jsonify
from core.timeline_engine import get_timeline_entries
from core.auth import verify_token
from core.logging_engine import log_action

timeline_bp = Blueprint('timeline', __name__)

@timeline_bp.route('/timeline', methods=['GET'])
def get_timeline():
    """Return recent timeline entries for UI rendering."""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    user = verify_token(token)
    if 'error' in user:
        return jsonify({"error": "Unauthorized"}), 401

    limit = int(request.args.get("limit", 50))
    entries = get_timeline_entries(limit=limit)
    log_action("routes/timeline", "get_timeline", f"Returned {len(entries)} entries")
    return jsonify({"timeline": entries})

@timeline_bp.route('/timeline/<entry_id>', methods=['GET'])
def get_timeline_entry(entry_id):
    """Return a single timeline entry by ID (if needed for deep display)."""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    user = verify_token(token)
    if 'error' in user:
        return jsonify({"error": "Unauthorized"}), 401

    from core.graph_io import run_read_query
    result = run_read_query("MATCH (t:TimelineEntry {id: $id}) RETURN t LIMIT 1", {"id": entry_id})
    if not result:
        return jsonify({"error": "Not found"}), 404
    log_action("routes/timeline", "get_entry", f"Returned timeline entry {entry_id}")
    return jsonify({"entry": result[0]["t"]})
