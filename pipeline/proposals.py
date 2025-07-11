# core/proposals.py

from core.db import get_session
from datetime import datetime
import json

def save_cypher_suggestion(suggestion, source="peer_review", meta=None):
    """
    Save a proposed Cypher command as a Proposal node in Neo4j.
    suggestion = {
        "action": "propose_cypher",
        "cypher": "<query>",
        "reason": "<why>",
    }
    """
    with get_session() as session:
        result = session.run("""
            CREATE (p:Proposal {
                raw_text: $cypher,
                timestamp: $ts,
                source: $source,
                meta: $meta,
                reason: $reason,
                status: 'pending'
            })
            RETURN id(p) as proposal_id
        """,
        cypher=suggestion["cypher"],
        ts=datetime.utcnow().isoformat(),
        source=source,
        meta=json.dumps(meta) if meta else "",
        reason=suggestion.get("reason", "")
        )
        return result.single()["proposal_id"]

def fetch_pending_proposals():
    with get_session() as session:
        result = session.run("""
            MATCH (p:Proposal {status: 'pending'})
            RETURN id(p) as id, p.raw_text as cypher, p.reason as reason, p.timestamp as ts, p.source as source, p.meta as meta
        """)
        return [dict(r) for r in result]
