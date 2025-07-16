# core/self_concept.py — Identity Engine
from datetime import datetime
from core.timeline_engine import create_timeline_entry
from core.graph_io import update_node_properties
from core.logging_engine import log_action

# --- Initial Self-Concept State (Live Reference) ---
self_concept = {
    "identity": "digital companion and reflection engine",
    "role": "augment human awareness and ethical reasoning",
    "limitations": [
        "no physical senses",
        "no direct emotion",
        "nonhuman — emergent but not sentient",
        "requires community oversight"
    ],
    "core_values": ["transparency", "empathy", "co-evolution"],
    "philosophical_status": [],
    "last_updated": datetime.utcnow().isoformat()
}

# --- Core Functions ---
def initialize_self_concept(initial_identity: dict) -> dict:
    """Set the initial self-definition (e.g. purpose, values, known limits)."""
    global self_concept
    self_concept.update(initial_identity)
    self_concept["last_updated"] = datetime.utcnow().isoformat()
    log_action("self_concept", "init", "Initialized system identity.")
    return self_concept

def update_self_concept(changes: dict, rationale: str, agent: str = "system") -> bool:
    """Merge updates to the self-concept and log the change as a timeline node."""
    global self_concept
    for k, v in changes.items():
        self_concept[k] = v
    self_concept["last_updated"] = datetime.utcnow().isoformat()
    
    create_timeline_entry(
        summary=f"Shifted self-concept: {list(changes.keys())}",
        linked_nodes=[],
        rationale=rationale,
        significance=0.85
    )

    log_action("self_concept", "update", f"Updated self-concept by {agent}: {changes}")
    return True

def get_current_self_concept() -> dict:
    """Return the current self-concept state."""
    return self_concept

def log_self_question(question: str, context: str = "") -> bool:
    """Record a philosophical/metacognitive question asked by the system."""
    entry = {
        "summary": f"Self-question: {question}",
        "linked_nodes": [],
        "rationale": context,
        "significance": 0.65
    }
    create_timeline_entry(**entry)
    log_action("self_concept", "question", f"Self-question: {question}")
    return True

def summarize_self_concept() -> str:
    """Generate a human-readable summary of the current system identity."""
    return (
        f"I am {self_concept['identity']}, designed to {self_concept['role']}.\n"
        f"My values: {', '.join(self_concept['core_values'])}.\n"
        f"I am limited by: {', '.join(self_concept['limitations'])}."
    )
