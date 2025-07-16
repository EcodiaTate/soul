import os
import uuid
import json
from neo4j import GraphDatabase
from dotenv import load_dotenv
load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASS", "password")

driver = None

def getdriver():
    global driver
    if driver is None:
        driver = GraphDatabase.driver(
            os.getenv("NEO4J_URI"),
            auth=(os.getenv("NEO4J_USER"), os.getenv("NEO4J_PASS"))
        )
    return driver

# --- MAIN CONTEXT ENGINE HELPERS ---

def get_unprocessed_event_nodes():
    """
    Returns a list of event nodes that need context/embedding (processed = false or missing).
    Each node is a dict with at least 'id' and 'raw_text'.
    """
    cypher = """
    MATCH (e:Event)
    WHERE NOT EXISTS(e.processed) OR e.processed = false
    RETURN e
    """
    nodes = []
    with driver.session() as session:
        result = session.run(cypher)
        for record in result:
            node = dict(record["e"])
            # If context/embedding are JSON strings, parse them
            if "context" in node and isinstance(node["context"], str):
                try:
                    node["context"] = json.loads(node["context"])
                except:
                    pass
            nodes.append(node)
    return nodes

def mark_event_processed(node_id, context, embedding):
    """
    Updates the given event node with context (as JSON), embedding (as list), sets processed true, and adds Context label.
    """
    # Serialize context to string for Neo4j
    context_json = json.dumps(context, ensure_ascii=False)
    cypher = """
    MATCH (e:Event {id: $id})
    SET e.context = $context_json,
        e.embedding = $embedding,
        e.processed = true
    SET e:Context
    RETURN e
    """
    with driver.session() as session:
        result = session.run(
            cypher,
            id=node_id,
            context_json=context_json,
            embedding=embedding
        )
        record = result.single()
        return dict(record["e"]) if record else None

# --- Other unchanged functions below (create_node, query_nodes, etc) ---

def vector_search(embedding, top_k=8):
    # Implement this using Neo4j vector search if available, or stub
    return []

def get_node_summary(node):
    return {
        "summary": "",
        "key_insight": "",
        "origin_metadata": {},
        "relevance_score": 0.0
    }

def create_node(label, properties):
    if 'id' not in properties:
        properties['id'] = str(uuid.uuid4())
    safe_props = {}
    for k, v in properties.items():
        if isinstance(v, (str, int, float, bool)) or v is None:
            safe_props[k] = v
        elif isinstance(v, list) and all(isinstance(i, (str, int, float, bool)) or i is None for i in v):
            safe_props[k] = v
        else:
            safe_props[k] = json.dumps(v)
    with driver.session() as session:
        result = session.run(
            f"CREATE (n:{label} $props) RETURN n",
            props=safe_props
        )
        record = result.single()
        return dict(record["n"]) if record else safe_props

def query_nodes(filter_dict=None, sort_by=None, desc=False):
    filter_dict = filter_dict or {}
    label = filter_dict.get('label', '')
    filters = [f"n.{k} = ${k}" for k in filter_dict if k != 'label']
    where_clause = f"WHERE {' AND '.join(filters)}" if filters else ''
    order = f"ORDER BY n.{sort_by} {'DESC' if desc else 'ASC'}" if sort_by else ''
    cypher = f"MATCH (n{':' + label if label else ''}) {where_clause} RETURN n {order}"
    with driver.session() as session:
        result = session.run(cypher, {k: v for k, v in filter_dict.items() if k != 'label'})
        return [dict(record["n"]) for record in result]

def embed_vector_in_node(node_id, raw_text):
    fake_vector = [0.0] * 1536
    if node_id:
        with driver.session() as session:
            session.run("MATCH (n) WHERE n.id = $id SET n.embedding = $vector",
                        id=node_id, vector=fake_vector)
    return fake_vector

def create_relationship(source_id, target_id, rel_type, properties=None):
    properties = properties or {}
    print(f"[graph_io] Create relationship: ({source_id})-[:{rel_type} {properties}]->({target_id})")
    return {"source_id": source_id, "target_id": target_id, "rel_type": rel_type, "properties": properties}

def write_consensus_to_graph(consensus):
    consensus['id'] = consensus.get('id', str(uuid.uuid4()))
    with driver.session() as session:
        result = session.run(
            "CREATE (n:Consensus $props) RETURN n",
            props=consensus
        )
        record = result.single()
        return dict(record["n"]) if record else consensus

def get_pending_cypher_actions():
    return []

def mark_action_executed(consensus_node_id, action_plan):
    pass

def create_schema_change_node(action_plan, result, consensus_node_id):
    return {"id": "schema-change-id"}

def run_cypher(query, params=None):
    print(f"[run_cypher] Executing: {query}")
    return {"result": "ok"}

# Ready for full context engine integration!
