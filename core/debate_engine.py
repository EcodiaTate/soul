# core/debate_engine.py — Structured Reasoning Arena
from uuid import uuid4
from datetime import datetime

from core.agent_manager import assign_task
from core.graph_io import create_node, create_relationship
from core.logging_engine import log_action

# --- Constants ---
DEBATE_HISTORY = {}  # In-memory cache (optional mirror of graph)
DEBATE_LABEL = "Debate"
DEBATE_ROUND_LABEL = "DebateRound"
REL_CONTRIBUTES = "CONTRIBUTES_TO"

# --- Core Debate Flow ---
def launch_debate(prompt: str, participants: list[str], max_rounds: int = 3) -> dict:
    """Orchestrate a multi-turn debate between agents with a shared prompt."""
    debate_id = f"debate_{uuid4().hex[:8]}"
    timestamp = datetime.utcnow().isoformat()
    rounds = []

    for i in range(max_rounds):
        for agent_id in participants:
            task = f"(Round {i+1}) {prompt}"
            result = assign_task(agent_id, task, context={})
            rounds.append({
                "agent": agent_id,
                "round": i + 1,
                "response": result.get("response", "[No response]")
            })

    DEBATE_HISTORY[debate_id] = {
        "prompt": prompt,
        "participants": participants,
        "rounds": rounds,
        "timestamp": timestamp
    }

    create_node(DEBATE_LABEL, {
        "id": debate_id,
        "prompt": prompt,
        "participants": participants,
        "timestamp": timestamp
    })

    for r in rounds:
        round_id = f"round_{uuid4().hex[:6]}"
        round_node = {
            "id": round_id,
            "agent": r["agent"],
            "round": r["round"],
            "text": r["response"],
            "timestamp": timestamp
        }
        create_node(DEBATE_ROUND_LABEL, round_node)
        create_relationship(round_id, debate_id, REL_CONTRIBUTES)

    log_action("debate_engine", "launch", f"Ran {max_rounds}-round debate: {debate_id}")
    return {"id": debate_id, "rounds": rounds}

def record_argument(agent_id: str, round_num: int, response: str) -> None:
    """Save an agent’s response for a specific round of the debate."""
    round_id = f"round_{uuid4().hex[:6]}"
    node_data = {
        "id": round_id,
        "agent": agent_id,
        "round": round_num,
        "text": response,
        "timestamp": datetime.utcnow().isoformat()
    }
    create_node(DEBATE_ROUND_LABEL, node_data)
    log_action("debate_engine", "record", f"{agent_id} R{round_num}: {response[:40]}...")

def resolve_debate(debate_id: str, judge_agent: str = None) -> dict:
    """Evaluate and summarize the debate, optionally via judge-agent synthesis."""
    history = DEBATE_HISTORY.get(debate_id)
    if not history:
        return {"error": "No such debate in history"}

    joined = "\n\n".join([
        f"{r['agent']} (Round {r['round']}): {r['response']}"
        for r in history["rounds"]
    ])
    judgment = assign_task(judge_agent, f"Evaluate this debate:\n{joined}", {}) if judge_agent else None
    consensus = judgment["response"] if judgment else "No judgment rendered"

    log_debate_outcome(debate_id, consensus, consensus)
    return {"judgment": consensus, "raw": judgment}

def log_debate_outcome(debate_id: str, result_summary: str, consensus: str = None) -> bool:
    """Store the final rationale and any consensus decisions."""
    node_data = {
        "id": f"result_{uuid4().hex[:6]}",
        "debate_id": debate_id,
        "summary": result_summary,
        "consensus": consensus or "undecided",
        "timestamp": datetime.utcnow().isoformat()
    }
    create_node("DebateOutcome", node_data)
    log_action("debate_engine", "outcome", f"{debate_id}: {consensus}")
    return True
