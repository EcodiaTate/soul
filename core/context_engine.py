import os
import openai
from .graph_io import vector_search, get_node_summary
from dotenv import load_dotenv
load_dotenv()  # By default, loads .env from current working dir

# CONFIG
EMBED_MODEL = os.environ.get("OPENAI_EMBED_MODEL", "text-embedding-ada-002")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")

client = openai.OpenAI(api_key=OPENAI_API_KEY)  # Uses env var or you can override

def embed_text(raw_text):
    print(f"[embed_text] Input: {raw_text!r}")
    try:
        resp = client.embeddings.create(input=[raw_text], model=EMBED_MODEL)
        embedding = resp.data[0].embedding
        print(f"[embed_text] Success! First 5 dims: {embedding[:5]}")
        return embedding
    except Exception as e:
        print(f"[embed_text] ERROR: {e}")
        return [0.0] * 1536

def load_relevant_context(vector, agent_id=None, max_tokens=2048):
    print(f"[load_relevant_context] Input vector (first 5): {vector[:5]}")
    # 1. Vector search for top-k nodes (events, core memories)
    nodes = vector_search(vector, top_k=8)
    print(f"[load_relevant_context] Retrieved {len(nodes)} nodes from Neo4j")
    # 2. Compress to prompt-ready blocks
    context_blocks = []
    for i, n in enumerate(nodes):
        block = get_node_summary(n)
        print(f"[load_relevant_context] Block {i+1}: {block}")
        context_blocks.append(block)
    # 3. Enforce token budget (rough estimate: 3 tokens per word)
    total_tokens = sum(len(block["summary"].split()) * 3 for block in context_blocks)
    print(f"[load_relevant_context] Total estimated tokens: {total_tokens}")
    if total_tokens > max_tokens:
        print(f"[load_relevant_context] Context exceeds max tokens ({max_tokens}). Compressing.")
        context_blocks = context_blocks[:4]
        context_blocks.append({
            "summary": "Additional relevant context compressed for token limit.",
            "key_insight": "",
            "origin_metadata": {},
            "relevance_score": 0.0
        })
    return context_blocks

def structure_context_for_prompt(context_blocks):
    print(f"[structure_context_for_prompt] Formatting {len(context_blocks)} blocks")
    prompt = ""
    for i, block in enumerate(context_blocks):
        prompt += (
            f"[Memory {i+1}]\n"
            f"Summary: {block.get('summary', '')}\n"
            f"Key Insight: {block.get('key_insight', '')}\n"
            f"Metadata: {block.get('origin_metadata', {})}\n\n"
        )
    print(f"[structure_context_for_prompt] Final prompt length: {len(prompt)} chars")
    return prompt
