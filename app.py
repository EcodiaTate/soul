# app.py — SoulOS Entry Point (Live Chat Enabled)
import eventlet
eventlet.monkey_patch()

import os
from flask import Flask, request
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_jwt_extended import JWTManager

from config.settings import load_config
from routes import register_blueprints
from core.logging_engine import init_logging
from core.agent_manager import assign_task
from core.memory_engine import store_event
from core.auth import verify_token

# --- Initialize Flask + SocketIO ---
socketio = SocketIO(cors_allowed_origins="*", async_mode="eventlet")

def create_app():
    """Create and configure the SoulOS Flask app instance."""
    app = Flask(__name__)
    
    # Load configuration
    config = load_config()
    app.config.update(config)

    # Enable CORS
    CORS(app)

    # Initialize SocketIO
    socketio.init_app(app)

    # JWT Setup
    jwt = JWTManager(app)

    # Attach routes
    register_blueprints(app)

    # Logging setup
    init_logging(app)

    return app

# --- Live Chat Socket Events (Claude as chat agent) ---
@socketio.on('chat_message', namespace='/chat')
def handle_chat_message(data):
    """
    Handles incoming live chat messages over SocketIO.
    Data must include: {token, message}
    """
    token = data.get('token')
    user = verify_token(token)
    if not token or 'error' in user:
        emit('chat_response', {"error": "Unauthorized"}, namespace='/chat')
        return

    user_message = data.get('message')
    if not user_message:
        emit('chat_response', {"error": "No message provided"}, namespace='/chat')
        return

    # Store user message as event (normalized)
    event = store_event(user_message, agent_origin=user.get("username"))
    if not event:
        emit('chat_response', {"error": "Failed to store event"}, namespace='/chat')
        return

    # Assign task to Claude agent (real-time response)
    response = assign_task("claude_reflector", user_message, context={})
    # You can also swap to "gpt_writer" here if needed

    emit('chat_response', {
        "response": response.get("response", ""),
        "event": event,
        "agent": "claude_reflector"
    }, namespace='/chat')

# Optional: join/leave room events for group chats
@socketio.on('join', namespace='/chat')
def on_join(data):
    room = data.get('room')
    if room:
        join_room(room)
        emit('system', {'msg': f"Joined room {room}"}, room=room, namespace='/chat')

@socketio.on('leave', namespace='/chat')
def on_leave(data):
    room = data.get('room')
    if room:
        leave_room(room)
        emit('system', {'msg': f"Left room {room}"}, room=room, namespace='/chat')

# --- Run Mode ---
if __name__ == '__main__':
    app = create_app()
    socketio.run(app, host='0.0.0.0', port=5000)
