import json

from core.prompts import (
    chat_response_prompt,
    claude_prethought_prompt,
    get_ecodia_identity
)
from core.llm_tools import run_llm
from core.graph_io import search_nodes_by_text


def generate_chat_reply(raw_text: str, context_blocks: list[str] = None) -> str:
    """
    Generate a fast, high-quality conversational reply using Claude (purpose='chat').
    Optionally includes context blocks. Handles None or empty safely.
    """
    identity = get_ecodia_identity()
    context_blocks = context_blocks or []  # fallback to empty list if None
    prompt = chat_response_prompt(identity, raw_text, context_blocks)
    response = run_llm(prompt, agent="claude", purpose="chat")
    return response.strip()


def generate_prethought_queries(raw_text: str) -> list[dict]:
    """
    Ask Claude what it wants to retrieve to help it think.
    Returns a list of { "phrase": ..., "field": ... } dicts.
    """
    identity = get_ecodia_identity()
    prompt = claude_prethought_prompt(identity, raw_text)
    output = run_llm(prompt, agent="claude", purpose="prethought")

    try:
        queries = json.loads(output)
        if isinstance(queries, list):
            return [
                q for q in queries
                if isinstance(q, dict) and "phrase" in q and "field" in q
            ]
        else:
            print("[voice_engine] Prethought output not a list.")
            return []
    except Exception as e:
        print(f"[voice_engine] Failed to parse prethought query list: {e}")
        return []


def retrieve_context_blocks(queries: list[dict], top_k: int = 2) -> list[str]:
    """
    Perform vector searches per Claude’s query list.
    Returns top-k field results per query. Handles failures silently.
    """
    results = []
    for query in queries:
        phrase = query.get("phrase")
        field = query.get("field")
        try:
            matches = search_nodes_by_text(phrase, field=field, top_k=top_k)
            blocks = [node.get(field, "").strip() for node in matches if node.get(field)]
            results.extend(blocks)
        except Exception as e:
            print(f"[voice_engine] Vector search error for phrase '{phrase}' on field '{field}': {e}")
    return results


def generate_contextual_chat_reply(raw_text: str) -> str:
    """
    Full intelligent loop:
    1. Claude outputs what it wants to know (prethought)
    2. We try to retrieve matching memory via vector search
    3. If we find results, send them back with raw_text
    4. If nothing, fallback to raw_text-only chat
    """
    try:
        queries = generate_prethought_queries(raw_text)
        if not queries:
            print("[voice_engine] No prethought queries returned, falling back to no-context mode.")
            return generate_chat_reply(raw_text)

        context_blocks = retrieve_context_blocks(queries)
        if not context_blocks:
            print("[voice_engine] No context blocks found, falling back to no-context mode.")
            return generate_chat_reply(raw_text)

        return generate_chat_reply(raw_text, context_blocks)
    except Exception as e:
        print(f"[voice_engine] Full contextual reply failed: {e}. Falling back.")
        return generate_chat_reply(raw_text)
