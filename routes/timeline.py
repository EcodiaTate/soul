"""
Timeline API: Serve TimelineEntry nodes to frontend
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from core import timeline_engine

timeline_bp = Blueprint('timeline_bp', __name__)

@timeline_bp.route('/api/timeline', methods=['GET'])
def get_timeline():
    """
    GET /api/timeline
    Returns: List of TimelineEntry nodes (public)
    """
    entries = timeline_engine.get_full_timeline()
    return jsonify(entries)

@timeline_bp.route('/api/timeline/<entry_id>', methods=['GET'])
@jwt_required()
def get_timeline_entry(entry_id):
    """
    GET /api/timeline/<id>
    Returns: Full TimelineEntry details (admin only)
    """
    # TODO: implement detail lookup by id
    return jsonify({})
