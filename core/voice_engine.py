import json

from core.prompts import (
    chat_response_prompt,
    claude_prethought_prompt,
    get_ecodia_identity
)
from core.llm_tools import run_llm
from core.vector_search import search_nodes_by_text


def generate_chat_reply(raw_text: str, context_blocks: list[str] = None) -> str:
    """
    Generate a fast, high-quality conversational reply using Claude (purpose='chat').
    Optionally includes relevant context blocks retrieved via vector search.
    """
    identity = get_ecodia_identity()
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
            print("[chat_agent] Prethought output not a list.")
            return []
    except Exception as e:
        print(f"[chat_agent] Failed to parse prethought query list: {e}")
        return []


def retrieve_context_blocks(queries: list[dict], top_k: int = 2) -> list[str]:
    """
    Perform vector searches per Claude’s query list.
    For each {phrase, field} pair, return relevant field content from top-k matching memory nodes.
    """
    results = []
    for query in queries:
        phrase = query["phrase"]
        field = query["field"]
        try:
            matches = search_nodes_by_text(phrase, field=field, top_k=top_k)
            blocks = [node.get(field, "").strip() for node in matches if node.get(field)]
            results.extend(blocks)
        except Exception as e:
            print(f"[chat_agent] Vector search error for phrase '{phrase}' on field '{field}': {e}")
    return results


def generate_contextual_chat_reply(raw_text: str) -> str:
    """
    Full intelligent loop:
    1. Claude outputs desired retrieval targets (phrases + fields)
    2. We run vector search for each pair
    3. Claude receives curated context snippets for reply
    """
    queries = generate_prethought_queries(raw_text)
    context_blocks = retrieve_context_blocks(queries)
    return generate_chat_reply(raw_text, context_blocks)
