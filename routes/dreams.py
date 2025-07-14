# /routes/dreams.py
from flask import Blueprint, request, jsonify
from core.dreams import add_dream, get_all_dreams
from core.socket_handlers import emit_dream_update

dreams_bp = Blueprint('dreams', __name__)

@dreams_bp.route('/api/dreams', methods=['GET'])
def get_dreams():
    dreams = get_all_dreams()
    return jsonify({'dreams': dreams}), 200

@dreams_bp.route('/api/dreams', methods=['POST'])
def post_dream():
    data = request.json
    raw_text = data.get('raw_text')
    user_origin = data.get('user_origin')
    meta_notes = data.get('meta_notes')
    node = add_dream(raw_text, user_origin, meta_notes)
    emit_dream_update(node)  # Push live
    return jsonify({'dream': node}), 201
