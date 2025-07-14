from core.graph_io import write_consensus_to_graph as graph_write_consensus

def check_alignment(agent_responses, threshold=0.7):
    """
    Checks if all agent responses are present and returns True if so.
    For this vertical slice: always returns True if nonempty list.
    """
    if not agent_responses or len(agent_responses) == 0:
        print("[consensus_engine] No agent responses provided!")
        return False
    print(f"[consensus_engine] {len(agent_responses)} agent responses received. (Alignment stub: always agree for now)")
    return True

def build_consensus(agent_responses):
    """
    Combines all agent rationales into one consensus rationale, averages scores.
    """
    if not agent_responses:
        print("[consensus_engine] No agent responses to build consensus.")
        return None

    combined_rationale = "\n\n".join(
        [f"[{a['agent_name']}] {a['rationale']}" for a in agent_responses]
    )
    average_score = sum(a.get("score", 1.0) for a in agent_responses) / len(agent_responses)
    consensus = {
        "rationale": combined_rationale,
        "consensus_score": average_score,
        "agent_names": [a["agent_name"] for a in agent_responses]
    }
    print(f"[consensus_engine] Built consensus. Avg score: {average_score:.2f}")
    return consensus

def store_consensus_in_graph(consensus):
    """
    Writes the consensus node to the Neo4j graph.
    """
    if consensus is None:
        print("[consensus_engine] No consensus to write to graph.")
        return None
    node = graph_write_consensus(consensus)
    print(f"[consensus_engine] Consensus node written. ID: {node.get('id', '[no id]')}")
    return node

def consensus_pipeline(event_id, agent_responses):
    """
    Full consensus flow: check alignment, build, write, or trigger peer review if needed.
    """
    if check_alignment(agent_responses):
        consensus = build_consensus(agent_responses)
        node = store_consensus_in_graph(consensus)
        return {"status": "consensus", "node": node}
    else:
        # Add this block:
        from core.peer_review_engine import peer_review_pipeline
        review_result = peer_review_pipeline(event_id, agent_responses)
        return {"status": "peer_review", "review_result": review_result}
