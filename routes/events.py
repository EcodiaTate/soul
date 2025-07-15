from flask import Blueprint, request, jsonify
from datetime import datetime, timezone
from config import settings
from neo4j import GraphDatabase
from core.context_engine import process_single_event
from core.graph_io import get_event_by_id
from core.value_vector import get_current_value_pool, get_value_schema_version  # NEW
from core.agents import gpt_agent_process, gemini_agent_process, claude_agent_process
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

    # 2. PROCESS with context engine (context, embedding, value_vector)
    try:
        value_pool = get_current_value_pool()
        schema_version = get_value_schema_version()
        process_single_event(event_id, raw_text, value_pool, schema_version)
    except Exception as e:
        logging.error(f"[routes.events] Context engine failed: {e}")
        return jsonify({"status": "error", "message": f"Context engine failed: {str(e)}"}), 500

    # 3. Load processed node (context/value_vector only)
    event = get_event_by_id(event_id)
    if not event or not event.get("context"):
        logging.error("[routes.events] Processed event not found or missing context.")
        return jsonify({"status": "error", "message": "Event context missing after processing."}), 500
    context = event["context"]
    value_vector = context.get("value_vector", {}) if isinstance(context, dict) else {}
    schema_version = context.get("value_schema_version") if isinstance(context, dict) else None
    if isinstance(context, str):  # In case still JSON string
        try:
            context = json.loads(context)
            value_vector = context.get("value_vector", {})
            schema_version = context.get("value_schema_version")
        except Exception:
            pass

    # 4. Run each agent on context + value_vector only
    agent_inputs = {"context": context, "value_vector": value_vector, "schema_version": schema_version}
    gpt_output = gpt_agent_process(agent_inputs)
    gemini_output = gemini_agent_process(agent_inputs)
    claude_output = claude_agent_process(agent_inputs)

    # 5. Build agent_responses for consensus pipeline
    agent_responses = [
        {"agent_name": "GPT", **gpt_output},
        {"agent_name": "Gemini", **gemini_output},
        {"agent_name": "Claude", **claude_output}
    ]

    # 6. Consensus pipeline (now on processed context)
    pipeline_result = consensus_pipeline(event_id, agent_responses)
    consensus = ""
    consensus_value_vector = {}
    if pipeline_result.get("status") == "consensus":
        consensus = pipeline_result.get("node", {}).get("rationale")
        consensus_value_vector = pipeline_result.get("node", {}).get("value_vector", {})
    elif pipeline_result.get("status") == "peer_review":
        consensus = "Under peer review—awaiting consensus."
    else:
        consensus = "No consensus reached."

    # 7. Update Event node with agent outputs, value vectors, consensus, and final status
    with driver.session() as session:
        session.run("""
            MATCH (e:Event {id: $id})
            SET e.status = $status,
                e.gpt_rationale = $gpt,
                e.gemini_rationale = $gemini,
                e.claude_rationale = $claude,
                e.consensus_rationale = $consensus,
                e.gpt_value_vector = $gpt_v,
                e.gemini_value_vector = $gemini_v,
                e.claude_value_vector = $claude_v,
                e.consensus_value_vector = $consensus_v,
                e.last_processed = $now,
                e.value_schema_version = $schema_version
        """, {
            "id": event_id,
            "status": pipeline_result.get("status"),
            "gpt": gpt_output.get("rationale", ""),
            "gemini": gemini_output.get("rationale", ""),
            "claude": claude_output.get("rationale", ""),
            "consensus": consensus,
            "gpt_v": json.dumps(gpt_output.get("value_vector", {})),
            "gemini_v": json.dumps(gemini_output.get("value_vector", {})),
            "claude_v": json.dumps(claude_output.get("value_vector", {})),
            "consensus_v": json.dumps(consensus_value_vector),
            "now": datetime.now(timezone.utc).isoformat(),
            "schema_version": schema_version
        })

    # 8. Emit real-time update via socket
    emit_new_event({
        "id": event_id,
        "context": context,
        "embedding": event.get("embedding"),
        "value_vector": value_vector,
        "timestamp": timestamp,
        "status": pipeline_result.get("status"),
        "gpt": gpt_output.get("rationale", ""),
        "gemini": gemini_output.get("rationale", ""),
        "claude": claude_output.get("rationale", ""),
        "consensus": consensus,
        "consensus_value_vector": consensus_value_vector,
        "value_schema_version": schema_version
    })

    # 9. Return pipeline result
    return jsonify({
        "event_id": event_id,
        "status": pipeline_result.get("status"),
        "pipeline_result": pipeline_result,
        "gpt": gpt_output.get("rationale", ""),
        "gemini": gemini_output.get("rationale", ""),
        "claude": claude_output.get("rationale", ""),
        "consensus": consensus,
        "value_vector": value_vector,
        "consensus_value_vector": consensus_value_vector,
        "context": context,
        "value_schema_version": schema_version
    })

# You need to implement get_event_by_id in core/graph_io.py:
# def get_event_by_id(event_id):
#     ...MATCH (e:Event {id: $event_id}) RETURN e...
