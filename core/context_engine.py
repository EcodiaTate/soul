import os
import openai
import json
import logging
from dotenv import load_dotenv

from core.graph_io import (
    get_unprocessed_event_nodes,
    mark_event_processed,
)
from core.value_vector import get_current_value_pool, get_value_schema_version

load_dotenv()
logging.basicConfig(level=logging.INFO)

EMBED_MODEL = os.environ.get("OPENAI_EMBED_MODEL", "text-embedding-ada-002")
LLM_MODEL = os.environ.get("OPENAI_LLM_MODEL", "gpt-3.5-turbo")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
client = openai.OpenAI(api_key=OPENAI_API_KEY)

# -------------------- MAIN --------------------

def process_new_events():
    events = get_unprocessed_event_nodes()
    value_pool = get_current_value_pool()
    schema_version = get_value_schema_version()
    if not events:
        logging.info("[context_engine] No new events to process.")
        return
    for ev in events:
        node_id = ev['id']
        raw_text = ev['raw_text']
        try:
            process_single_event(node_id, raw_text, value_pool, schema_version)
        except Exception as e:
            logging.error(f"[context_engine] ERROR processing event {node_id}: {e}")

def process_single_event(event_id, raw_text, value_pool=None, schema_version=None):
    if value_pool is None:
        value_pool = get_current_value_pool()
    if schema_version is None:
        schema_version = get_value_schema_version()
    try:
        context = compress_event_with_llm(raw_text, value_pool, schema_version)
        if not context:
            raise Exception("LLM returned empty context.")
        context_str = json.dumps(context, ensure_ascii=False)
        embedding = embed_text(context_str)
        if not embedding or not isinstance(embedding, list) or sum(abs(x) for x in embedding) < 1e-6:
            raise Exception("Embedding failed or returned near-zero vector.")
        mark_event_processed(event_id, context, embedding)
        logging.info(f"[context_engine] Processed single event {event_id}")
    except Exception as e:
        logging.error(f"[context_engine] ERROR processing single event {event_id}: {e}")

# -------------------- UTILITIES --------------------

def compress_event_with_llm(raw_text, value_pool, schema_version):
    pool_str = ', '.join([f'"{v}"' for v in value_pool])
    prompt = (
        "You are a high-compression context extractor for an AI memory graph. "
        f"Extract the main actors, actions, topics, decisions, and score each of these values (to 3 decimals) as floats 0.000–10.000: [{pool_str}]. "
        "Respond ONLY with valid JSON as:\n"
        '{"actors": [], "actions": [], "topics": [], "decision": "", '
        f'"value_vector": {{"{value_pool[0]}": 0.000}}, "value_schema_version": "{schema_version}", "keypoints": []}}\n'
        f"Input: {raw_text}"
    )
    try:
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[{"role": "system", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.0,
            max_tokens=384
        )
        text = response.choices[0].message.content
        return json.loads(text)
    except Exception as e:
        logging.error(f"[compress_event_with_llm] ERROR for input: {raw_text[:80]}... | {e}")
        return None

def embed_text(context_text):
    try:
        resp = client.embeddings.create(input=[context_text], model=EMBED_MODEL)
        embedding = resp.data[0].embedding
        if not embedding:
            raise Exception("Embedding result empty.")
        return embedding
    except Exception as e:
        logging.error(f"[embed_text] ERROR: {e}")
        return None

# -------------------- CHAT CONTEXT --------------------

def load_relevant_context(vector):
    # TODO: vector search integration here
    return []

def format_context_blocks(blocks):
    """
    Format a list of context blocks for use in chat prompts.
    Each block should be a dictionary with text content.
    """
    if not blocks:
        return []
    formatted = []
    for b in blocks:
        if isinstance(b, str):
            formatted.append(b)
        elif isinstance(b, dict):
            if 'rationale' in b:
                formatted.append(b['rationale'])
            elif 'text' in b:
                formatted.append(b['text'])
            elif 'raw_text' in b:
                formatted.append(b['raw_text'])
    return formatted
