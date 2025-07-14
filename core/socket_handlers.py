from flask_socketio import SocketIO
from app import socketio
from flask import current_app

# Import the main socketio instance from app.py (adjust path if needed)
try:
    from app import socketio
except ImportError:
    socketio = None  # To avoid IDE errors during early dev

def emit_dream_update(dream_obj):
    # Import socketio from the app context to avoid circular imports
    from app import socketio
    socketio.emit('dream_update', dream_obj, namespace='/')
    
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

def emit_dream_update(dream_obj):
    
    socketio.emit('dream_update', dream_obj, namespace='/')

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
