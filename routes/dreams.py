# routes/dreams.py — Dreamscape API
from flask import Blueprint, request, jsonify
from core.graph_io import run_read_query
from core.auth import verify_token
from core.logging_engine import log_action

dreams_bp = Blueprint('dreams', __name__)

@dreams_bp.route('/dreams', methods=['GET'])
def get_all_dreams():
    """Return recent or significant dream nodes."""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    user = verify_token(token)
    if 'error' in user:
        return jsonify({"error": "Unauthorized"}), 401

    limit = int(request.args.get("limit", 20))
    query = """
    MATCH (d:Dream)
    RETURN d
    ORDER BY d.timestamp DESC
    LIMIT $limit
    """
    dreams = run_read_query(query, {"limit": limit})
    log_action("routes/dreams", "list", f"Returned {len(dreams)} dreams")
    return jsonify({"dreams": dreams})

@dreams_bp.route('/dreams/<dream_id>', methods=['GET'])
def get_dream_by_id(dream_id):
    """Return a full view of a specific dream node."""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    user = verify_token(token)
    if 'error' in user:
        return jsonify({"error": "Unauthorized"}), 401

    query = "MATCH (d:Dream {id: $id}) RETURN d LIMIT 1"
    result = run_read_query(query, {"id": dream_id})
    if not result:
        return jsonify({"error": "Not found"}), 404
    log_action("routes/dreams", "get", f"Returned dream {dream_id}")
    return jsonify({"dream": result[0]["d"]})
