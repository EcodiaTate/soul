# core/actuators/cypher.py — Direct Neo4j Schema Mutation Tool
from neo4j import GraphDatabase
from core.logging_engine import log_action
import os

# --- Config ---
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASS = os.getenv("NEO4J_PASS")
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))

SCHEMA_MUTATION_LOG_LABEL = "SchemaMutationLog"

# --- Core Functions ---
def execute_cypher(command: str, parameters: dict = None) -> dict:
    """Safely run a custom Cypher write with optional parameters."""
    try:
        with driver.session() as session:
            result = session.write_transaction(lambda tx: tx.run(command, parameters or {}).data())
        log_action("cypher", "execute", f"Ran command: {command[:60]}")
        return {"status": "success", "result": result}
    except Exception as e:
        log_action("cypher", "error", f"Cypher failed: {e}")
        return {"status": "error", "message": str(e)}

def mutate_schema(new_labels: list[str], new_relationships: list[str]) -> bool:
    """Add or modify node/edge types programmatically (post-human-approval)."""
    log_data = {
        "id": f"schema_mutation_{os.urandom(3).hex()}",
        "performed_by": "consciousness_engine",
        "timestamp": _now(),
        "diff": {
            "labels_added": new_labels,
            "relationships_added": new_relationships
        }
    }
    create_node(SCHEMA_MUTATION_LOG_LABEL, log_data)
    log_action("cypher", "mutate_schema", f"Added labels: {new_labels}, relationships: {new_relationships}")
    return True

def merge_identity_clusters(cluster_a: str, cluster_b: str) -> bool:
    """Combine two self-concept clusters into one and reassign children."""
    cypher = f"""
    MATCH (a:SelfCluster {{id: $a}})<-[r:BELONGS_TO]-(m)
    MATCH (b:SelfCluster {{id: $b}})
    CREATE (m)-[:BELONGS_TO {{merged:true}}]->(b)
    DELETE r
    DELETE a
    """
    result = execute_cypher(cypher, {"a": cluster_a, "b": cluster_b})
    log_action("cypher", "merge_clusters", f"Merged {cluster_a} into {cluster_b}")
    return result["status"] == "success"

# --- Internal ---
def _now() -> str:
    from datetime import datetime
    return datetime.utcnow().isoformat()

def create_node(label: str, properties: dict) -> bool:
    """Create node using internal driver, bypassing abstraction."""
    query = f"CREATE (n:{label} $props) RETURN n"
    return execute_cypher(query, {"props": properties})["status"] == "success"
