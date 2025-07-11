import json
import numpy as np
from core.db import get_session
from ai.llm import openai_llm
from core.values import get_active_values

def get_nodes_for_vector_update():
    with get_session() as session:
        result = session.run("""
            MATCH (n:Event)
            WHERE exists(n.raw_text)
            RETURN id(n) as nid, labels(n) as labels, n.raw_text as raw_text, n.impact_vector as old_vector
        """)
        return [dict(r) for r in result]

def rescore_node_with_llm(n, llm_func=openai_llm):
    values = get_active_values()
    prompt = (
        f"Ecodia’s current value system is: {values}.\n"
        f"For this node, rate its impact along each value (0-1) and justify nonzero scores. "
        f"Node text: '''{n.get('raw_text','') or json.dumps(n)}'''\n"
        "Output as: {impact_vector: [...], justifications: [...], agent: 'openai_gpt4', model: 'gpt-4', prompt: '...'}"
    )
    result = llm_func(prompt)
    if isinstance(result, str):
        try:
            result = json.loads(result)
        except Exception:
            result = {
                'impact_vector': [],
                'justifications': [],
                'agent': 'openai_gpt4',
                'model': 'gpt-4',
                'prompt': prompt,
                'llm_output': result
            }
    result.setdefault('agent', 'openai_gpt4')
    result.setdefault('model', 'gpt-4')
    result.setdefault('prompt', prompt)
    result.setdefault('impact_vector', [])
    result.setdefault('justifications', [])
    return result

def update_node_vector(nid, impact_vector, justifications, prev_vector=None, agent=None, model=None, prompt=None):
    with get_session() as session:
        session.run("""
            MATCH (n) WHERE id(n) = $nid
            SET n.impact_vector = $impact_vector,
                n.justifications = $justifications,
                n.prev_vector = $prev_vector,
                n.last_vector_update = timestamp(),
                n.vector_agent = $agent,
                n.vector_model = $model,
                n.vector_prompt = $prompt
        """, 
        nid=nid,
        impact_vector=json.dumps(impact_vector),
        justifications=json.dumps(justifications),
        prev_vector=json.dumps(prev_vector) if prev_vector is not None else None,
        agent=agent,
        model=model,
        prompt=prompt
        )

def search_vectors(query_embedding, top_k=10):
    """
    Return the top_k most similar nodes/events to the given embedding, using cosine similarity.
    Assumes all events/nodes have an 'embedding' property stored as list of floats.
    """
    sims = []
    events = []
    with get_session() as session:
        result = session.run("MATCH (n:Event) WHERE exists(n.embedding) RETURN id(n) as nid, n.raw_text as raw_text, n.embedding as embedding")
        for r in result:
            emb = r['embedding']
            if isinstance(emb, str):
                emb = json.loads(emb)
            events.append({"nid": r['nid'], "raw_text": r['raw_text'], "embedding": emb})

    if not events:
        return []

    query = np.array(query_embedding)
    for e in events:
        vec = np.array(e['embedding'])
        # cosine similarity with small epsilon to avoid div by zero
        sim = float(np.dot(query, vec) / (np.linalg.norm(query) * np.linalg.norm(vec) + 1e-6))
        sims.append((sim, e))

    top = sorted(sims, key=lambda x: -x[0])[:top_k]
    return [event for score, event in top]

def search_nodes_by_embedding(query_embedding, label="Event", top_k=5):
    """
    Returns the top_k nodes of type `label` most similar to the embedding.
    """
    sims = []
    nodes = []
    with get_session() as session:
        result = session.run(f"MATCH (n:{label}) WHERE exists(n.embedding) RETURN id(n) as nid, n.raw_text as raw_text, n.embedding as embedding")
        for r in result:
            emb = r['embedding']
            if isinstance(emb, str):
                emb = json.loads(emb)
            nodes.append({"nid": r['nid'], "raw_text": r['raw_text'], "embedding": emb})

    if not nodes:
        return []

    query = np.array(query_embedding)
    for n in nodes:
        vec = np.array(n['embedding'])
        sim = float(np.dot(query, vec) / (np.linalg.norm(query) * np.linalg.norm(vec) + 1e-6))
        sims.append((sim, n))

    top = sorted(sims, key=lambda x: -x[0])[:top_k]
    return [node for score, node in top]
