from flask import Blueprint, request, jsonify
from datetime import datetime, timezone
from config import settings
from neo4j import GraphDatabase
from core.context_engine import process_single_event
from core.graph_io import get_event_by_id
from core.value_vector import get_current_value_pool, get_value_schema_version
from core.agents import run_all_agents
from core.consensus_engine import consensus_pipeline
from core.socket_handlers import emit_new_event
from dotenv import load_dotenv
import uuid
import logging
import json

load_dotenv()
logging.basicConfig(level=logging.INFO)

events_bp = Blueprint('events', __name__)
driver = GraphDatabase.driver(settings.NEO4J_URI, auth=(settings.NEO4J_USER, settings.NEO4J_PASS))

@events_bp.route('/api/event', methods=['POST'])
def create_event():
    data = request.json
    raw_text = data.get("text")
    if not raw_text or not isinstance(raw_text, str) or not raw_text.strip():
        return jsonify({"status": "error", "message": "Missing or invalid 'text' in request body"}), 400

    timestamp = datetime.now(timezone.utc).isoformat()
    event_id = str(uuid.uuid4())

    # 1. Insert raw Event node as UNPROCESSED
    with driver.session() as session:
        session.run("""
            CREATE (e:Event {
                id: $id,
                raw_text: $raw_text,
                timestamp: $timestamp,
                processed: false,
                status: "unprocessed"
            })
        """, {"id": event_id, "raw_text": raw_text, "timestamp": timestamp})

    # 2. Context engine processing (embedding, context, value vector)
    try:
        value_pool = get_current_value_pool()
        schema_version = get_value_schema_version()
        process_single_event(event_id, raw_text, value_pool, schema_version)
    except Exception as e:
        logging.error(f"[routes.events] Context engine failed: {e}")
        return jsonify({"status": "error", "message": f"Context engine failed: {str(e)}"}), 500

    # 3. Load event with updated context
    event = get_event_by_id(event_id)
    if not event or not event.get("context"):
        return jsonify({"status": "error", "message": "Missing event context"}), 500

    context = event.get("context", {})
    if isinstance(context, str):
        try:
            context = json.loads(context)
        except Exception:
            context = {}

    value_vector = context.get("value_vector", {})
    schema_version = context.get("value_schema_version", schema_version)

    # 4. Run agents using updated universal agent mesh
    agent_input = {
        "id": event_id,
        "raw_text": raw_text,
        "context_blocks": context,
        "value_vector": value_vector,
        "value_schema_version": schema_version,
        "timestamp": timestamp
    }
    agent_responses = run_all_agents(agent_input)

    # 5. Consensus pipeline
    pipeline_result = consensus_pipeline(event_id, agent_responses)
    status = pipeline_result.get("status", "unknown")
    consensus = ""
    consensus_value_vector = {}

    if status == "consensus":
        node = pipeline_result.get("node", {})
        consensus = node.get("rationale", "")
        consensus_value_vector = node.get("value_vector", {})
    elif status == "peer_review":
        consensus = "Under peer review—awaiting consensus."
    else:
        consensus = "No consensus reached."

    # 6. Update Event node with all agent rationales/vectors and consensus
    update_fields = {
        "status": status,
        "consensus_rationale": consensus,
        "consensus_value_vector": json.dumps(consensus_value_vector),
        "last_processed": datetime.now(timezone.utc).isoformat(),
        "value_schema_version": schema_version
    }

    for agent in agent_responses:
        name = agent.get("agent_name", "unknown").lower()
        update_fields[f"{name}_rationale"] = agent.get("rationale", "")
        update_fields[f"{name}_value_vector"] = json.dumps(agent.get("value_vector", {}))

    set_clause = ",\n".join([f"e.{k} = ${k}" for k in update_fields])
    with driver.session() as session:
        session.run(f"""
            MATCH (e:Event {{id: $id}})
            SET {set_clause}
        """, {"id": event_id, **update_fields})

    # 7. Emit event update to frontend
    emit_new_event({
        "id": event_id,
        "context": context,
        "embedding": event.get("embedding"),
        "value_vector": value_vector,
        "timestamp": timestamp,
        "status": status,
        "consensus": consensus,
        "consensus_value_vector": consensus_value_vector,
        "value_schema_version": schema_version,
        "agent_outputs": agent_responses
    })

    # 8. Respond to API call
    return jsonify({
        "event_id": event_id,
        "status": status,
        "pipeline_result": pipeline_result,
        "consensus": consensus,
        "value_vector": value_vector,
        "consensus_value_vector": consensus_value_vector,
        "context": context,
        "value_schema_version": schema_version,
        "agent_responses": agent_responses
    })
