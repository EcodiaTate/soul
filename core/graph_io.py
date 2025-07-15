import os
import uuid
import json
from typing import Any, Dict, List, Optional, Union
from neo4j import GraphDatabase
from dotenv import load_dotenv
# TODO introduce emotion vectors - static vector with ratings
load_dotenv()

NEO4J_URI = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.environ.get("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.environ.get("NEO4J_PASS", "password")

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

# --- Helper: fields that should always be JSON-encoded if non-primitive ---
COMPLEX_FIELDS = {"value_vector", "context", "audit_log", "action_plan", "topics", "causal_trace"}

def _safe_props(properties: Dict[str, Any]) -> Dict[str, Any]:
    """Serialize all complex fields to JSON strings for Neo4j."""
    safe = {}
    for k, v in properties.items():
        if k in COMPLEX_FIELDS:
            safe[k] = json.dumps(v)
        elif isinstance(v, (str, int, float, bool)) or v is None:
            safe[k] = v
        elif isinstance(v, list) and all(isinstance(i, (str, int, float, bool)) or i is None for i in v):
            safe[k] = v
        else:
            # Fallback for any stray dict or custom object
            safe[k] = json.dumps(v)
    return safe

def _parse_complex_fields(node: Dict[str, Any]) -> Dict[str, Any]:
    """Decode JSON strings for all complex fields (if present and string)."""
    for k in COMPLEX_FIELDS:
        if k in node and isinstance(node[k], str):
            try:
                node[k] = json.loads(node[k])
            except Exception:
                node[k] = {} if k.endswith("_vector") or k == "context" or k == "action_plan" else []
    return node

# === EVENT AND VALUE VECTOR CORE ===

def get_event_by_id(event_id: str) -> Optional[Dict[str, Any]]:
    cypher = "MATCH (e:Event {id: $event_id}) RETURN e"
    with driver.session() as session:
        result = session.run(cypher, event_id=event_id)
        record = result.single()
        if not record:
            return None
        node = dict(record["e"])
        return _parse_complex_fields(node)

def create_node(label: str, properties: Dict[str, Any]) -> Dict[str, Any]:
    if 'id' not in properties:
        properties['id'] = str(uuid.uuid4())
    safe_props = _safe_props(properties)
    with driver.session() as session:
        result = session.run(
            f"CREATE (n:{label} $props) RETURN n",
            props=safe_props
        )
        record = result.single()
        return _parse_complex_fields(dict(record["n"])) if record else safe_props

def update_node(label: Optional[str], node_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
    safe_updates = _safe_props(updates)
    cypher = f"""
    MATCH (n{':' + label if label else ''} {{id: $id}})
    SET """ + ", ".join([f"n.{k} = ${k}" for k in safe_updates]) + " RETURN n"
    params = {"id": node_id}
    params.update(safe_updates)
    with driver.session() as session:
        result = session.run(cypher, params)
        record = result.single()
        return _parse_complex_fields(dict(record["n"])) if record else {}

def query_nodes(filter_dict: Optional[Dict[str, Any]] = None, sort_by: Optional[str] = None, desc: bool = False, limit: int = 100) -> List[Dict[str, Any]]:
    filter_dict = filter_dict or {}
    label = filter_dict.get('label', '')
    filters = [f"n.{k} = ${k}" for k in filter_dict if k != 'label']
    where_clause = f"WHERE {' AND '.join(filters)}" if filters else ''
    order = f"ORDER BY n.{sort_by} {'DESC' if desc else 'ASC'}" if sort_by else ''
    limit_clause = f"LIMIT {limit}" if limit else ''
    cypher = f"MATCH (n{':' + label if label else ''}) {where_clause} RETURN n {order} {limit_clause}"
    with driver.session() as session:
        result = session.run(cypher, {k: v for k, v in filter_dict.items() if k != 'label'})
        return [_parse_complex_fields(dict(record["n"])) for record in result]

def get_all_nodes(label: str = "") -> List[Dict[str, Any]]:
    return query_nodes({"label": label})

def archive_node(node_id: str) -> None:
    cypher = "MATCH (n {id: $id}) SET n.archived = true, n:Archived"
    with driver.session() as session:
        session.run(cypher, id=node_id)

def traverse_branch(node_id: str) -> List[str]:
    cypher = """
    MATCH (start {id: $id})-[*0..]->(n)
    RETURN DISTINCT n.id as id
    """
    with driver.session() as session:
        result = session.run(cypher, id=node_id)
        return [record["id"] for record in result]

def get_value_nodes() -> List[Dict[str, Any]]:
    return query_nodes({"label": "Value", "active": True})

def update_node_schema(label: str, node_list: List[Dict[str, Any]], version: int) -> None:
    cypher = f"""
    MATCH (n:{label})
    WHERE n.uuid IN $uuids
    SET n:Value, n.schema_version = $version
    """
    uuids = [n.get('uuid') for n in node_list]
    with driver.session() as session:
        session.run(cypher, uuids=uuids, version=version)

def get_schema_version(label: str) -> Optional[int]:
    cypher = f"MATCH (n:{label}) RETURN n.schema_version as v ORDER BY v DESC LIMIT 1"
    with driver.session() as session:
        result = session.run(cypher)
        record = result.single()
        return int(record["v"]) if record and record["v"] else None

def set_schema_version(label: str, version: int) -> None:
    cypher = f"MATCH (n:{label}) SET n.schema_version = $version"
    with driver.session() as session:
        session.run(cypher, version=version)

def get_edge_types() -> List[Dict[str, Any]]:
    return query_nodes({"label": "EdgeType"})

def create_relationship(source_id: str, target_id: str, rel_type: str, properties: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    properties = properties or {}
    safe_props = _safe_props(properties)
    cypher = f"""
    MATCH (a {{id: $source_id}}), (b {{id: $target_id}})
    CREATE (a)-[r:{rel_type} $props]->(b)
    RETURN r
    """
    with driver.session() as session:
        result = session.run(cypher, source_id=source_id, target_id=target_id, props=safe_props)
        record = result.single()
        return dict(record["r"]) if record else {"source_id": source_id, "target_id": target_id, "rel_type": rel_type, "properties": safe_props}

def vector_search(query_vector: Dict[str, float], top_k: int = 8) -> List[Dict[str, Any]]:
    return []  # stub

def write_consensus_to_graph(consensus: Dict[str, Any]) -> Dict[str, Any]:
    consensus['id'] = consensus.get('id', str(uuid.uuid4()))
    return create_node("Consensus", consensus)

def get_pending_cypher_actions() -> List[Dict[str, Any]]:
    return []

def mark_action_executed(consensus_node_id: str, action_plan: Any) -> None:
    pass

def create_schema_change_node(action_plan, result, consensus_node_id) -> Dict[str, Any]:
    return {"id": "schema-change-id"}

def run_cypher(query: str, params: Optional[Dict[str, Any]] = None) -> Any:
    print(f"[run_cypher] Executing: {query}")
    with driver.session() as session:
        result = session.run(query, params or {})
        try:
            return [dict(r.data()) for r in result]
        except:
            return {"result": "ok"}

def get_unprocessed_event_nodes() -> List[Dict[str, Any]]:
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
            node = _parse_complex_fields(node)
            nodes.append(node)
    return nodes

def mark_event_processed(node_id: str, context: Any, embedding: List[float]) -> Optional[Dict[str, Any]]:
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
        node = dict(record["e"]) if record else None
        return _parse_complex_fields(node) if node else None

def embed_vector_in_node(node_id: str, raw_text: str) -> List[float]:
    fake_vector = [0.0] * 1536
    if node_id:
        with driver.session() as session:
            session.run("MATCH (n) WHERE n.id = $id SET n.embedding = $vector",
                        id=node_id, vector=fake_vector)
    return fake_vector

def get_node_summary(node: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "summary": "",
        "key_insight": "",
        "origin_metadata": {},
        "relevance_score": 0.0
    }
