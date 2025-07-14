from flask import Blueprint, request, jsonify
from datetime import datetime
from config import settings
from neo4j import GraphDatabase
from core.agents import gpt_agent_process, gemini_agent_process, claude_agent_process

events_bp = Blueprint('events', __name__)
driver = GraphDatabase.driver(settings.NEO4J_URI, auth=(settings.NEO4J_USER, settings.NEO4J_PASS))

@events_bp.route('/api/event', methods=['POST'])
def create_event():
    data = request.json
    raw_text = data.get("text")
    timestamp = datetime.utcnow().isoformat()

    # 1. Create unprocessed event node
    with driver.session() as session:
        session.run("""
            CREATE (e:Event {
                id: apoc.create.uuid(),
                raw_text: $raw_text,
                timestamp: $timestamp,
                status: "unprocessed"
            })
        """, {"raw_text": raw_text, "timestamp": timestamp})

    # 2. Process with all 3 agents
    gpt_output = gpt_agent_process(raw_text)
    gemini_output = gemini_agent_process(raw_text)
    claude_output = claude_agent_process(raw_text)

    # 3. Determine consensus (basic logic for now)
    rationales = [gpt_output["rationale"], gemini_output["rationale"], claude_output["rationale"]]
    consensus = gpt_output["rationale"] if len(set(rationales)) == 1 else None
    status = "consensus" if consensus else "needs_review"

    # 4. Update the event node with all 3 outputs
    with driver.session() as session:
        session.run("""
            MATCH (e:Event {raw_text: $raw_text, timestamp: $timestamp})
            SET e.status = $status,
                e.gpt_rationale = $gpt,
                e.gemini_rationale = $gemini,
                e.claude_rationale = $claude,
                e.consensus_rationale = $consensus,
                e.mood = $mood
        """, {
            "raw_text": raw_text,
            "timestamp": timestamp,
            "status": status,
            "gpt": gpt_output["rationale"],
            "gemini": gemini_output["rationale"],
            "claude": claude_output["rationale"],
            "consensus": consensus,
            "mood": gpt_output["mood"]
        })

    return jsonify({
        "status": status,
        "consensus": consensus,
        "gpt": gpt_output["rationale"],
        "gemini": gemini_output["rationale"],
        "claude": claude_output["rationale"]
    })
