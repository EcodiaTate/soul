import os
import uuid
import json
from neo4j import GraphDatabase
from dotenv import load_dotenv
load_dotenv()

NEO4J_URI = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.environ.get("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD", "password")

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
def vector_search(embedding, top_k=8):
    return []

def get_node_summary(node):
    return {
        "summary": "",
        "key_insight": "",
        "origin_metadata": {},
        "relevance_score": 0.0
    }

import uuid
import json

def create_node(label, properties):
    # Add UUID if not present
    if 'id' not in properties:
        properties['id'] = str(uuid.uuid4())
    # Neo4j can't store dicts or list of dicts. Serialize them.
    safe_props = {}
    for k, v in properties.items():
        # Accept bool/int/float/str/list of primitives or None as-is
        if isinstance(v, (str, int, float, bool)) or v is None:
            safe_props[k] = v
        elif isinstance(v, list) and all(isinstance(i, (str, int, float, bool)) or i is None for i in v):
            safe_props[k] = v
        else:
            # For dicts, list of dicts, or anything else, store as JSON string
            safe_props[k] = json.dumps(v)
    with driver.session() as session:
        result = session.run(
            f"CREATE (n:{label} $props) RETURN n",
            props=safe_props
        )
        record = result.single()
        return dict(record["n"]) if record else safe_props

def embed_vector_in_node(node_id, vector):
    # Update an existing node with a new embedding/vector field
    with driver.session() as session:
        session.run(
            "MATCH (n) WHERE n.id = $id SET n.embedding = $vector",
            id=node_id,
            vector=vector
        )
# /core/graph_io.py

def create_relationship(source_id, target_id, rel_type, properties=None):
    """
    Creates a relationship between two nodes in the Neo4j graph.
    - source_id: ID of the source node
    - target_id: ID of the target node
    - rel_type: Relationship type (e.g., 'REVIEWS', 'CONTRADICTS')
    - properties: Dict of relationship properties (optional)
    """
    properties = properties or {}
    # Stub: Just print the intended action for now
    print(f"[graph_io] Create relationship: ({source_id})-[:{rel_type} {properties}]->({target_id})")
    # In production, run Cypher here via Neo4j driver.
    return {"source_id": source_id, "target_id": target_id, "rel_type": rel_type, "properties": properties}

def write_consensus_to_graph(consensus):
    # Create Consensus node; expects dict with required fields
    consensus['id'] = consensus.get('id', str(uuid.uuid4()))
    with driver.session() as session:
        result = session.run(
            "CREATE (n:Consensus $props) RETURN n",
            props=consensus
        )
        record = result.single()
        return dict(record["n"]) if record else consensus
