# core/actuators/cypher.py — Direct Neo4j Schema Mutation Tool (No direct driver access)
from core.graph_io import run_write_query, create_node
from core.logging_engine import log_action
import os
from datetime import datetime

SCHEMA_MUTATION_LOG_LABEL = "SchemaMutationLog"

def execute_cypher(command: str, parameters: dict = None) -> dict:
    """
    Safely run a custom Cypher write with optional parameters using graph_io universal helper.
    """
    try:
        result = run_write_query(command, parameters or {})
        log_action("cypher", "execute", f"Ran command: {command[:60]}")
        return {"status": "success", "result": result}
    except Exception as e:
        log_action("cypher", "error", f"Cypher failed: {e}")
        return {"status": "error", "message": str(e)}

def mutate_schema(new_labels: list[str], new_relationships: list[str]) -> bool:
    """
    Add or modify node/edge types programmatically (post-human-approval).
    """
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
    """
    Combine two self-concept clusters into one and reassign children.
    """
    cypher = """
    MATCH (a:SelfCluster {id: $a})<-[r:BELONGS_TO]-(m)
    MATCH (b:SelfCluster {id: $b})
    CREATE (m)-[:BELONGS_TO {merged:true}]->(b)
    DELETE r
    DELETE a
    """
    result = execute_cypher(cypher, {"a": cluster_a, "b": cluster_b})
    log_action("cypher", "merge_clusters", f"Merged {cluster_a} into {cluster_b}")
    return result["status"] == "success"

def _now() -> str:
    return datetime.utcnow().isoformat()
