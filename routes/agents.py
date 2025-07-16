# routes/agents.py — Admin Agent Management API
from flask import Blueprint, request, jsonify
from core.agent_manager import get_agent_roster
from core.auth import verify_token, is_admin
from core.logging_engine import log_action

agents_bp = Blueprint('agents', __name__)

@agents_bp.route('/agents', methods=['GET'])
def get_all_agents():
    """Return metadata for all registered agents (admin only)."""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    user = verify_token(token)
    if 'error' in user or not is_admin(user):
        return jsonify({"error": "Forbidden"}), 403

    agents = get_agent_roster()
    log_action("routes/agents", "list", f"Returned {len(agents)} agents")
    return jsonify({"agents": agents})

@agents_bp.route('/agents/<agent_id>/logs', methods=['GET'])
def get_agent_logs(agent_id):
    """Return action logs for a specific agent."""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    user = verify_token(token)
    if 'error' in user or not is_admin(user):
        return jsonify({"error": "Forbidden"}), 403

    from core.logging_engine import get_recent_logs
    logs = get_recent_logs(limit=100)
    agent_logs = [log for log in logs if log.get("source") == agent_id]
    log_action("routes/agents", "logs", f"Returned logs for {agent_id}")
    return jsonify({"logs": agent_logs})

@agents_bp.route('/agents/<agent_id>/retire', methods=['POST'])
def retire_agent(agent_id):
    """Retire an agent and remove from active roster (admin only)."""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    user = verify_token(token)
    if 'error' in user or not is_admin(user):
        return jsonify({"error": "Forbidden"}), 403

    # In this prototype, we'll mark agent status inactive
    from core.agent_manager import AGENT_REGISTRY
    if agent_id in AGENT_REGISTRY:
        AGENT_REGISTRY[agent_id]["status"] = "retired"
        log_action("routes/agents", "retire", f"Agent {agent_id} retired by admin")
        return jsonify({"status": "success", "message": f"Agent {agent_id} retired"})
    else:
        return jsonify({"error": "Agent not found"}), 404
