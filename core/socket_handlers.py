from flask_socketio import SocketIO
from flask import current_app

# Import the main socketio instance from app.py (adjust path if needed)

def emit_dream_update(dream_obj):
    from app import socketio
    socketio.emit('dream_update', dream_obj, namespace='/')

def emit_new_event(event):
    from app import socketio
    socketio.emit('event_update', event, namespace='/')

def emit_timeline_update(entry):
    from app import socketio
    socketio.emit('timeline_update', entry, namespace='/')

def emit_event_update(event):
    from app import socketio
    socketio.emit('event_update', event, namespace='/')

def emit_chat_response(msg_obj):
    from app import socketio
    socketio.emit('chat_response', msg_obj, namespace='/')

def emit_agent_state(agent_id, state):
    from app import socketio
    socketio.emit('agent_update', {'id': agent_id, 'state': state}, namespace='/')

def emit_meta_audit(audit_obj):
    from app import socketio
    socketio.emit('meta_audit', audit_obj, namespace='/')

def emit_action_update(action_obj):
    from app import socketio
    socketio.emit("action_update", action_obj, namespace="/")

# Optional: Add more emitters as needed for your custom channels.

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
