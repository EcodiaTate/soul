# core/db.py

import os
import hashlib
from neo4j import GraphDatabase
from dotenv import load_dotenv
from core.utils import get_embedding  # You must have this; uses OpenAI/Gemini/etc

# Load environment variables
load_dotenv()
NEO4J_URI = os.environ.get("NEO4J_URI")
NEO4J_USER = os.environ.get("NEO4J_USER")
NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD")

def get_session():
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    return driver.session()

def run_query(query, **params):
    with get_session() as session:
        result = session.run(query, **params)
        return [r for r in result]

def event_hash(event):
    """Hash unique event fields for deduplication."""
    s = f"{event.get('event_id','')}-{event.get('source','')}-{event.get('raw_text','')}-{event.get('timestamp','')}"
    return hashlib.sha256(s.encode('utf-8')).hexdigest()

def save_event(event, dedupe=True):
    """
    Insert or merge an event node in Neo4j.
    - dedupe: If True, skip if event hash already exists.
    - Adds vector embedding if not present.
    Returns True if event was stored, False if skipped (dedupe).
    """
    if "embedding" not in event:
        event["embedding"] = get_embedding(event["raw_text"])
    event["hash"] = event_hash(event)

    with get_session() as session:
        # Deduplication
        if dedupe:
            existing = session.run(
                "MATCH (e:Event {hash: $hash}) RETURN e LIMIT 1",
                hash=event["hash"]
            ).single()
            if existing:
                return False  # Event already stored

        # Create or update event node
        session.run(
            """
            MERGE (e:Event {hash: $hash})
            SET e += $props
            """,
            hash=event["hash"],
            props=event
        )
    return True

def get_event_by_hash(hash_):
    with get_session() as session:
        result = session.run("MATCH (e:Event {hash: $hash}) RETURN e LIMIT 1", hash=hash_)
        record = result.single()
        return record["e"] if record else None

def get_events(from_ts=None, to_ts=None, source=None):
    with get_session() as session:
        cypher = "MATCH (e:Event) WHERE 1=1"
        params = {}
        if from_ts:
            cypher += " AND e.timestamp >= $from_ts"
            params["from_ts"] = from_ts
        if to_ts:
            cypher += " AND e.timestamp <= $to_ts"
            params["to_ts"] = to_ts
        if source:
            cypher += " AND e.source = $source"
            params["source"] = source
        cypher += " RETURN e ORDER BY e.timestamp"
        result = session.run(cypher, **params)
        return [r['e'] for r in result]
