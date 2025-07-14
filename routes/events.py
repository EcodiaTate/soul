from flask import Blueprint, request, jsonify
from datetime import datetime, timezone
from config import settings
from neo4j import GraphDatabase
from core.agents import gpt_agent_process, gemini_agent_process, claude_agent_process
from core.consensus_engine import consensus_pipeline
from dotenv import load_dotenv
import uuid

load_dotenv()

events_bp = Blueprint('events', __name__)
driver = GraphDatabase.driver(settings.NEO4J_URI, auth=(settings.NEO4J_USER, settings.NEO4J_PASS))

@events_bp.route('/api/event', methods=['POST'])
def create_event():
    data = request.json
    raw_text = data.get("text")
    timestamp = datetime.now(timezone.utc).isoformat()
    event_id = str(uuid.uuid4())

    # 1. Create unprocessed Event node and return id
    with driver.session() as session:
        session.run("""
            CREATE (e:Event {
                id: $id,
                raw_text: $raw_text,
                timestamp: $timestamp,
                status: "unprocessed"
            })
        """, {"id": event_id, "raw_text": raw_text, "timestamp": timestamp})

    # 2. Get agent outputs
    gpt_output = gpt_agent_process(raw_text)
    gemini_output = gemini_agent_process(raw_text)
    claude_output = claude_agent_process(raw_text)

    # 3. Build agent_responses for pipeline
    agent_responses = [
        {"agent_name": "GPT", **gpt_output},
        {"agent_name": "Gemini", **gemini_output},
        {"agent_name": "Claude", **claude_output}
    ]

    # 4. Run consensus/peer review pipeline
    pipeline_result = consensus_pipeline(event_id, agent_responses)

    # 5. Extract consensus rationale if present
    if pipeline_result.get("status") == "consensus":
        consensus = pipeline_result.get("node", {}).get("rationale")
    elif pipeline_result.get("status") == "peer_review":
        consensus = "Under peer review—awaiting consensus."
    else:
        consensus = "No consensus reached."

    # 6. Update Event node with rationales and result
    with driver.session() as session:
        session.run("""
            MATCH (e:Event {id: $id})
            SET e.status = $status,
                e.gpt_rationale = $gpt,
                e.gemini_rationale = $gemini,
                e.claude_rationale = $claude,
                e.consensus_rationale = $consensus
        """, {
            "id": event_id,
            "status": pipeline_result.get("status"),
            "gpt": gpt_output["rationale"],
            "gemini": gemini_output["rationale"],
            "claude": claude_output["rationale"],
            "consensus": consensus
        })

    # 7. Return pipeline_result for full trace
    return jsonify({
        "event_id": event_id,
        "status": pipeline_result.get("status"),
        "pipeline_result": pipeline_result,
        "gpt": gpt_output["rationale"],
        "gemini": gemini_output["rationale"],
        "claude": claude_output["rationale"],
        "consensus": consensus
    })
