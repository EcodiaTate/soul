# core/imagination_engine.py — Visionary Projection Layer
from datetime import datetime

from core.llm_tools import prompt_gpt, prompt_claude
from core.graph_io import create_node, create_relationship, run_read_query
from core.vector_ops import embed_text
from core.logging_engine import log_action

# --- Constants ---
IMAGINE_NODE_LABEL = "Imagine"
REL_IMAGINES = "IMAGINES"
default_imagination_prompt = "What if the system abandoned hierarchy completely?"

# --- Core Functions ---
def imagine_scenario(prompt: str, context_nodes: list[str] = None, temperature: float = 0.9) -> dict:
    """Generate a speculative or visionary output from a scenario prompt."""
    context_text = "\n".join(get_raw_text(nid) for nid in context_nodes) if context_nodes else ""
    full_prompt = f"{context_text}\n\n{prompt}" if context_text else prompt

    response = prompt_claude(
        full_prompt,
        system_prompt="You are a speculative imagination engine. Dream, but with structure.",
        temperature=temperature
    )

    node = {
        "id": f"imagine_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
        "scenario": prompt,
        "generated_text": response,
        "source_context": context_nodes or [],
        "timestamp": datetime.utcnow().isoformat(),
        "label": label_imagination(prompt, response)
    }

    create_node(IMAGINE_NODE_LABEL, node)
    for nid in context_nodes or []:
        create_relationship(nid, node["id"], REL_IMAGINES)

    log_action("imagination_engine", "imagine", f"Imagined: {prompt[:40]}...")
    return node

def log_imagine_node(imagine_data: dict) -> bool:
    """Store an imagination node with metadata and source links."""
    if not imagine_data.get("generated_text"):
        return False
    create_node(IMAGINE_NODE_LABEL, imagine_data)
    for src in imagine_data.get("source_context", []):
        create_relationship(src, imagine_data["id"], REL_IMAGINES)
    log_action("imagination_engine", "log", f"Logged imagined node {imagine_data['id']}")
    return True

def simulate_alternatives(base_event_id: str, num_variants: int = 3) -> list[dict]:
    """Branch possible futures from a single event or belief node."""
    base_text = get_raw_text(base_event_id)
    branches = []
    for i in range(num_variants):
        prompt = f"Alternative future #{i+1}:\nBased on this event: {base_text}\nWhat could happen if it unfolded differently?"
        alt_text = prompt_gpt(prompt)
        alt_node = {
            "id": f"alt_{base_event_id[-6:]}_{i}",
            "scenario": prompt,
            "generated_text": alt_text,
            "source_context": [base_event_id],
            "timestamp": datetime.utcnow().isoformat(),
            "label": f"alt_future_{i+1}"
        }
        create_node(IMAGINE_NODE_LABEL, alt_node)
        create_relationship(base_event_id, alt_node["id"], REL_IMAGINES)
        branches.append(alt_node)
        log_action("imagination_engine", "simulate_alternative", f"From {base_event_id} → alt_{i}")
    return branches

# --- Internal Helpers ---
def get_raw_text(node_id: str) -> str:
    query = "MATCH (n {id: $id}) RETURN n.raw_text AS text LIMIT 1"
    result = run_read_query(query, {"id": node_id})
    return result[0]["text"] if result else ""

def label_imagination(prompt: str, output: str) -> str:
    """Generate a human-readable label using Claude."""
    from core.llm_tools import prompt_claude
    task = f"Label the following speculative idea with a 2-4 word poetic summary:\n{output}"
    return prompt_claude(task, system_prompt="You're an imagination labeler.")[:64]
