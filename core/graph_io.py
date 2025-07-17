# core/graph_io.py — Universal Graph IO Layer (Singleton Neo4j Driver)
import os
import logging
from neo4j import GraphDatabase

# --- Singleton Driver Management ---
class _Neo4jDriverSingleton:
    _driver = None

    @classmethod
    def get_driver(cls):
        if cls._driver is None:
            uri = os.getenv("NEO4J_URI")
            user = os.getenv("NEO4J_USER")
            pwd = os.getenv("NEO4J_PASS")
            if not all([uri, user, pwd]):
                raise RuntimeError("Neo4j credentials not set in environment")
            cls._driver = GraphDatabase.driver(uri, auth=(user, pwd))
        return cls._driver

    @classmethod
    def close(cls):
        if cls._driver is not None:
            cls._driver.close()
            cls._driver = None

def get_neo4j_driver():
    """Access the singleton Neo4j driver (init if needed)."""
    return _Neo4jDriverSingleton.get_driver()

def close_driver():
    """Call to close the Neo4j driver on shutdown/exit."""
    _Neo4jDriverSingleton.close()

# --- Universal Graph I/O Operations ---

def run_write_query(query: str, parameters: dict = None) -> dict:
    """Safely run a Cypher write query and return the result."""
    driver = get_neo4j_driver()
    with driver.session() as session:
        try:
            result = session.write_transaction(lambda tx: tx.run(query, parameters or {}).data())
            return {"status": "success", "result": result}
        except Exception as e:
            logging.error(f"Neo4j Write Error: {e}")
            return {"status": "error", "message": str(e)}

def run_read_query(query: str, parameters: dict = None) -> list[dict]:
    """Run a Cypher read query and return records as a list of dicts."""
    driver = get_neo4j_driver()
    with driver.session() as session:
        try:
            result = session.read_transaction(lambda tx: tx.run(query, parameters or {}).data())
            return result
        except Exception as e:
            logging.error(f"Neo4j Read Error: {e}")
            return []

def create_node(label: str, properties: dict) -> dict:
    """Create a new node with specified label and properties."""
    props = {k: v for k, v in properties.items() if v is not None}
    query = f"CREATE (n:{label} $props) RETURN n"
    return run_write_query(query, {"props": props})

def create_relationship(from_id: str, to_id: str, rel_type: str, properties: dict = None) -> bool:
    """Create a relationship between two nodes by ID with optional properties."""
    props = properties or {}
    query = f"""
    MATCH (a), (b)
    WHERE a.id = $from_id AND b.id = $to_id
    CREATE (a)-[r:{rel_type} $props]->(b)
    RETURN r
    """
    result = run_write_query(query, {"from_id": from_id, "to_id": to_id, "props": props})
    return result["status"] == "success"

def get_node_by_id(node_id: str) -> dict:
    """Retrieve a node and its properties by ID."""
    query = "MATCH (n {id: $node_id}) RETURN n LIMIT 1"
    result = run_read_query(query, {"node_id": node_id})
    return result[0]["n"] if result else {}

def update_node_properties(node_id: str, new_props: dict) -> bool:
    """Merge new properties into an existing node."""
    query = "MATCH (n {id: $node_id}) SET n += $props RETURN n"
    result = run_write_query(query, {"node_id": node_id, "props": new_props})
    return result["status"] == "success"

# Optional: Ensure a graceful shutdown when needed
# Example: in your main app entrypoint, call close_driver() on exit/shutdown

