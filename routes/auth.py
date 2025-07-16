# routes/auth.py — Authentication API
from flask import Blueprint, request, jsonify
from core.auth import authenticate_user, verify_token
from core.logging_engine import log_action

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['POST'])
def login():
    """Authenticate user and return JWT token."""
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"error": "Missing credentials"}), 400

    token = authenticate_user(username, password)
    if not token:
        return jsonify({"error": "Invalid username or password"}), 401

    log_action("routes/auth", "login", f"User {username} logged in")
    return jsonify({"token": token})

@auth_bp.route('/verify', methods=['GET'])
def verify():
    """Verify provided JWT token."""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token:
        return jsonify({"error": "Missing token"}), 400

    decoded = verify_token(token)
    if 'error' in decoded:
        return jsonify({"error": decoded['error']}), 401

    log_action("routes/auth", "verify", f"Token verified for user {decoded.get('username')}")
    return jsonify({"user": decoded})
