"""
/core/socket_handlers.py

Real-Time Socket Handlers for Timeline, Event, Chat, Agent, and Audit Updates.
- Emits all real-time state changes via Flask-SocketIO to the frontend.
- Integrate by calling these emitters after new data is created/updated in the system.

Collaborators:
    - app.py (registers and shares socketio instance)
    - timeline_engine.py, events.py, agents.py, meta_audit.py, consensus_engine.py
    - Frontend: listens on 'timeline_update', 'event_update', 'chat_response', etc.
"""

from flask_socketio import SocketIO

# Import the main socketio instance from app.py (adjust path if needed)
try:
    from app import socketio
except ImportError:
    socketio = None  # To avoid IDE errors during early dev

def emit_timeline_update(entry):
    """
    Emit 'timeline_update' to all subscribed clients when a new TimelineEntry is created.
    """
    if socketio:
        socketio.emit('timeline_update', entry, namespace="/")
    # else: warn or log

def emit_event_update(event):
    """
    Emit 'event_update' when a new or updated event is processed.
    """
    if socketio:
        socketio.emit('event_update', event, namespace="/")

def emit_chat_response(msg_obj):
    """
    Emit 'chat_response' to push live chat output to the UI.
    """
    if socketio:
        socketio.emit('chat_response', msg_obj, namespace="/")

def emit_agent_state(agent_id, state):
    """
    Emit 'agent_update' for mood/energy or state changes to agent dashboard.
    """
    if socketio:
        socketio.emit('agent_update', {'id': agent_id, 'state': state}, namespace="/")

def emit_meta_audit(audit_obj):
    """
    Emit 'meta_audit' for system health checks or audit results.
    """
    if socketio:
        socketio.emit('meta_audit', audit_obj, namespace="/")

# Optional: Add more emitters for custom channels as your system grows.

# Usage Examples:
# After creating a TimelineEntry:
#   from core.socket_handlers import emit_timeline_update
#   emit_timeline_update(entry_dict)
#
# After chat processing:
#   emit_chat_response(response_obj)
#
# In agent logic:
#   emit_agent_state(agent_id, state_dict)
#
# For admin/audit logs:
#   emit_meta_audit(audit_obj)
