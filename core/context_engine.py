"""
context_engine.py — Pure Compression Engine for Incoming Events
Author: Ecodia Dev Team
Last updated: 2025-07-16
"""

import os
import json
import logging
from dotenv import load_dotenv
import openai
import numpy as np

from core.graph_io import (
    get_unprocessed_event_nodes,
    mark_event_processed,
    query_nodes,
)

from core.prompts import contextualization_prompt

load_dotenv()
logging.basicConfig(level=logging.INFO)

LLM_MODEL = os.getenv("OPENAI_LLM_MODEL", "gpt-3.5-turbo")
EMBED_MODEL = os.getenv("OPENAI_EMBED_MODEL", "text-embedding-ada-002")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
client = openai.OpenAI(api_key=OPENAI_API_KEY)

# === MAIN ENTRYPOINT ===

def process_new_events():
    events = get_unprocessed_event_nodes()
    if not events:
        logging.info("[context_engine] No new events to process.")
        return
    for ev in events:
        event_id = ev["id"]
        raw_text = ev.get("raw_text", "")
        try:
            process_single_event(event_id, raw_text)
        except Exception as e:
            logging.error(f"[context_engine] ERROR processing event {event_id}: {e}")

def process_single_event(event_id: str, raw_text: str):
    compressed = compress_event(raw_text)
    if not compressed:
        raise Exception("Compression failed or returned empty.")
    embedding = embed_text(compressed)
    if not embedding:
        raise Exception("Embedding failed or empty vector.")
    mark_event_processed(event_id, compressed, embedding)
    logging.info(f"[context_engine] Processed and compressed event {event_id}")

# === CORE COMPRESSION ===

def compress_event(raw_text: str) -> str:
    prompt = contextualization_prompt(raw_text)
    try:
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[{"role": "system", "content": prompt}],
            temperature=0.0,
            max_tokens=384,
        )
        compressed = response.choices[0].message.content.strip()
        if not compressed or len(compressed) < 4:
            raise Exception("Returned compression is empty or invalid.")
        return compressed
    except Exception as e:
        logging.error(f"[compress_event] ERROR: {e}")
        return None

# === EMBEDDING ===

def embed_text(text: str):
    try:
        resp = client.embeddings.create(input=[text], model=EMBED_MODEL)
        vec = resp.data[0].embedding
        if not vec or sum(abs(x) for x in vec) < 1e-6:
            raise Exception("Embedding is near-zero.")
        return vec
    except Exception as e:
        logging.error(f"[embed_text] ERROR: {e}")
        return None

# === CHAT CONTEXT FORMATTING ===

def format_context_blocks(blocks):
    """
    Format a list of memory/context blocks for display or injection into prompts.
    """
    if not blocks:
        return []
    formatted = []
    for b in blocks:
        if isinstance(b, str):
            formatted.append(b)
        elif isinstance(b, dict):
            for key in ("rationale", "text", "summary", "raw_text"):
                if key in b:
                    formatted.append(b[key])
                    break
    return formatted

# === CONTEXT RETRIEVAL ===

def cosine_similarity(vec1, vec2):
    if not vec1 or not vec2:
        return 0.0
    a = np.array(vec1)
    b = np.array(vec2)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-8))

def retrieve_similar_context(vector, top_k=5, node_type="Event"):
    all_nodes = query_nodes({"label": node_type}, limit=100)
    scored = []
    for node in all_nodes:
        emb = node.get("embedding")
        if emb:
            score = cosine_similarity(vector, emb)
            scored.append((score, node))
    scored.sort(reverse=True, key=lambda x: x[0])
    return [node for _, node in scored[:top_k]]


def load_relevant_context(vector, top_k=5):
    """
    Alias for retrieve_similar_context — used by chat.py and agent mesh.
    """
    return retrieve_similar_context(vector, top_k=top_k, node_type="Event")
