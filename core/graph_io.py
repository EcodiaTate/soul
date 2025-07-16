import os
import uuid
import json
from typing import Any, Dict, List, Optional
from neo4j import GraphDatabase
from dotenv import load_dotenv
from core.context_engine import embed_text  # Provides real embeddings

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASS = os.getenv("NEO4J_PASS")

_driver = None

def get_driver():
    global _driver
    if _driver is None:
        _driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))
    return _driver

COMPLEX_FIELDS = {
    "value_vector", "emotion_vector", "context", "audit_log",
    "action_plan", "topics", "causal_trace", "agent_responses",
    "critiques", "embedding"
}

def _safe_props(properties: Dict[str, Any]) -> Dict[str, Any]:
    safe = {}
    for k, v in properties.items():
        if k in COMPLEX_FIELDS:
            safe[k] = json.dumps(v)
        elif isinstance(v, (str, int, float, bool)) or v is None:
            safe[k] = v
        elif isinstance(v, list) and all(isinstance(i, (str, int, float, bool)) or i is None for i in v):
            safe[k] = v
        else:
            safe[k] = json.dumps(v)
    return safe

def _parse_complex_fields(node: Dict[str, Any]) -> Dict[str, Any]:
    for k in COMPLEX_FIELDS:
        if k in node and isinstance(node[k], str):
            try:
                node[k] = json.loads(node[k])
            except Exception:
                node[k] = {} if k.endswith("_vector") or k == "context" or k == "action_plan" else []
    return node

def create_node(label: str, properties: Dict[str, Any]) -> Dict[str, Any]:
    if 'id' not in properties:
        properties['id'] = str(uuid.uuid4())
    safe_props = _safe_props(properties)
    with get_driver().session() as session:
        result = session.run(f"CREATE (n:{label} $props) RETURN n", props=safe_props)
        record = result.single()
        return _parse_complex_fields(dict(record["n"])) if record else safe_props

def update_node(label: Optional[str], node_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
    safe_updates = _safe_props(updates)
    cypher = f"""
    MATCH (n{':' + label if label else ''} {{id: $id}})
    SET """ + ", ".join([f"n.{k} = ${k}" for k in safe_updates]) + " RETURN n"
    params = {"id": node_id}
    params.update(safe_updates)
    with get_driver().session() as session:
        result = session.run(cypher, params)
        record = result.single()
        return _parse_complex_fields(dict(record["n"])) if record else {}

def get_node(event_id: str) -> Optional[Dict[str, Any]]:
    cypher = "MATCH (n {id: $event_id}) RETURN n LIMIT 1"
    with get_driver().session() as session:
        result = session.run(cypher, event_id=event_id)
        record = result.single()
        return _parse_complex_fields(dict(record["n"])) if record else None

def get_event_by_id(event_id: str) -> Optional[Dict[str, Any]]:
    cypher = "MATCH (e:Event {id: $event_id}) RETURN e"
    with get_driver().session() as session:
        result = session.run(cypher, event_id=event_id)
        record = result.single()
        return _parse_complex_fields(dict(record["e"])) if record else None

def query_nodes(filter_dict: Optional[Dict[str, Any]] = None, sort_by: Optional[str] = None, desc: bool = False, limit: int = 100) -> List[Dict[str, Any]]:
    filter_dict = filter_dict or {}
    label = filter_dict.get('label', '')
    filters = [f"n.{k} = ${k}" for k in filter_dict if k != 'label']
    where_clause = f"WHERE {' AND '.join(filters)}" if filters else ''
    order = f"ORDER BY n.{sort_by} {'DESC' if desc else 'ASC'}" if sort_by else ''
    limit_clause = f"LIMIT {limit}" if limit else ''
    cypher = f"MATCH (n{':' + label if label else ''}) {where_clause} RETURN n {order} {limit_clause}"
    with get_driver().session() as session:
        result = session.run(cypher, {k: v for k, v in filter_dict.items() if k != 'label'})
        return [_parse_complex_fields(dict(record["n"])) for record in result]

def get_all_nodes(label: str = "") -> List[Dict[str, Any]]:
    return query_nodes({"label": label})

def archive_node(node_id: str) -> None:
    cypher = "MATCH (n {id: $id}) SET n.archived = true, n:Archived"
    with get_driver().session() as session:
        session.run(cypher, id=node_id)

def traverse_branch(node_id: str) -> List[str]:
    cypher = "MATCH (start {id: $id})-[*0..]->(n) RETURN DISTINCT n.id as id"
    with get_driver().session() as session:
        result = session.run(cypher, id=node_id)
        return [record["id"] for record in result]

from core.context_engine import embed_text

def search_nodes_by_text(phrase: str, field: str, top_k: int = 5, node_type: str = "Event") -> List[Dict[str, Any]]:
    """
    Embed the phrase, then return top-k nodes where the cosine similarity
    of the node's embedding vector is highest. Only returns nodes with the requested field.
    """
    vector = embed_text(phrase)
    cypher = f"""
    MATCH (n:{node_type})
    WHERE exists(n.embedding) AND exists(n.{field})
    WITH n, gds.similarity.cosine(n.embedding, $vector) AS similarity
    RETURN n {{.*, similarity: similarity }}
    ORDER BY similarity DESC
    LIMIT $top_k
    """
    with get_driver().session() as session:
        result = session.run(cypher, {"vector": vector, "top_k": top_k})
        return [_parse_complex_fields(record["n"]) for record in result]


def embed_vector_in_node(node_id: str, raw_text: str) -> List[float]:
    vector = embed_text(raw_text)
    with get_driver().session() as session:
        session.run("MATCH (n) WHERE n.id = $id SET n.embedding = $vector", id=node_id, vector=vector)
    return vector

def get_unprocessed_event_nodes() -> List[Dict[str, Any]]:
    cypher = "MATCH (e:Event) WHERE NOT EXISTS(e.processed) OR e.processed = false RETURN e"
    with get_driver().session() as session:
        result = session.run(cypher)
        return [_parse_complex_fields(dict(record["e"])) for record in result]

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
    with get_driver().session() as session:
        result = session.run(cypher, id=node_id, context_json=context_json, embedding=embedding)
        record = result.single()
        return _parse_complex_fields(dict(record["e"])) if record else None

def create_relationship(source_id: str, target_id: str, rel_type: str, properties: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    properties = properties or {}
    safe_props = _safe_props(properties)
    cypher = f"""
    MATCH (a {{id: $source_id}}), (b {{id: $target_id}})
    CREATE (a)-[r:{rel_type} $props]->(b)
    RETURN r
    """
    with get_driver().session() as session:
        result = session.run(cypher, source_id=source_id, target_id=target_id, props=safe_props)
        record = result.single()
        return dict(record["r"]) if record else {
            "source_id": source_id,
            "target_id": target_id,
            "rel_type": rel_type,
            "properties": safe_props
        }

def write_consensus_to_graph(consensus: Dict[str, Any]) -> Dict[str, Any]:
    consensus['id'] = consensus.get('id', str(uuid.uuid4()))
    return create_node("Consensus", consensus)

def get_node_summary(node: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "summary": "",
        "key_insight": "",
        "origin_metadata": {},
        "relevance_score": 0.0
    }

def run_cypher(query: str, params: Optional[Dict[str, Any]] = None) -> Any:
    print(f"[run_cypher] Executing: {query}")
    with get_driver().session() as session:
        result = session.run(query, params or {})
        try:
            return [dict(r.data()) for r in result]
        except:
            return {"result": "ok"}
