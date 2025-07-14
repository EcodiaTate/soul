# /core/dreams.py
import uuid, datetime
from .graph_io import create_node, query_nodes, embed_vector_in_node

def add_dream(raw_text, user_origin=None, meta_notes=None):
    """Creates a Dream node, embeds, and stores in Neo4j."""
    dream_id = str(uuid.uuid4())
    timestamp = datetime.datetime.utcnow().isoformat()
    embedding = embed_vector_in_node(None, raw_text)  # This should call your vectorizer, returns [float]
    node = create_node('Dream', {
        'id': dream_id,
        'raw_text': raw_text,
        'timestamp': timestamp,
        'embedding': embedding,
        'significance': 0.5,  # Start mid, adjust later
        'user_origin': user_origin or "system",
        'meta_notes': meta_notes or ""
    })
    return node

def get_all_dreams():
    """Returns all Dream nodes, sorted by timestamp desc."""
    dreams = query_nodes({'label': 'Dream'}, sort_by='timestamp', desc=True)
    return dreams
