# app.py — SoulOS Entry Point (Production Ready with Gevent)

import gevent.monkey
gevent.monkey.patch_all()

import os
from flask import Flask
from flask_cors import CORS
from flask_socketio import SocketIO
from flask_jwt_extended import JWTManager

from config.settings import load_config
from routes import register_blueprints
from core.logging_engine import init_logging
from core.agent_manager import assign_task
from core.memory_engine import store_event
from core.auth import verify_token

# --- SocketIO (Gevent for production) ---
socketio = SocketIO(cors_allowed_origins="*", async_mode="gevent")

def create_app():
    """
    Create and configure the SoulOS Flask application.
    """
    app = Flask(__name__)

    # Load environment-based settings
    config = load_config()
    app.config.update(config)

    # Enable CORS
    CORS(app)

    # JWT auth setup
    JWTManager(app)

    # Register routes
    register_blueprints(app)

    # Logging
    init_logging(app)

    # Bind SocketIO to app
    socketio.init_app(app)

    return app

# --- SocketIO: Live Chat Events (optional) ---
@socketio.on('chat_message', namespace='/chat')
def handle_chat_message(data):
    """
    Handles live SocketIO chat input: { token, message }
    """
    token = data.get('token')
    user = verify_token(token)
    if not token or 'error' in user:
        socketio.emit('chat_response', {"error": "Unauthorized"}, namespace='/chat')
        return

    message = data.get('message')
    if not message:
        socketio.emit('chat_response', {"error": "No message provided"}, namespace='/chat')
        return

    event = store_event(message, agent_origin=user["username"])
    if not event:
        socketio.emit('chat_response', {"error": "Failed to store event"}, namespace='/chat')
        return

    response = assign_task("claude_reflector", message, context={})
    socketio.emit('chat_response', {
        "response": response.get("response", ""),
        "event": event,
        "agent": "claude_reflector"
    }, namespace='/chat')

@socketio.on('join', namespace='/chat')
def on_join(data):
    room = data.get('room')
    if room:
        from flask_socketio import join_room
        join_room(room)
        socketio.emit('system', {"msg": f"Joined {room}"}, room=room, namespace='/chat')

@socketio.on('leave', namespace='/chat')
def on_leave(data):
    room = data.get('room')
    if room:
        from flask_socketio import leave_room
        leave_room(room)
        socketio.emit('system', {"msg": f"Left {room}"}, room=room, namespace='/chat')

# --- Run Mode ---
if __name__ == '__main__':
    app = create_app()
    socketio.run(app, host='0.0.0.0', port=5000)
