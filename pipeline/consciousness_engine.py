import json
import logging
from core.db import get_session
from core.proposals import fetch_pending_proposals, get_event_context, save_cypher_suggestion
from core.vectors import search_vectors, search_nodes_by_embedding
from ai.prompts import build_evolution_prompt
from ai.agent_utils import run_multi_llm
from proposal_executor import review_with_llm  # Make sure this is importable!
from core.utils import get_embedding
from core.cypher_actuator import is_safe_cypher, run_cypher_actuator

logging.basicConfig(level=logging.INFO, filename="logs/consciousness_engine.log")

def process_cypher_proposal(cypher, verdict, review_reason):
    if verdict == "approve":
        print("LLM approved. Attempting Cypher execution…")
        try:
            if is_safe_cypher(cypher):
                success, exec_result = run_cypher_actuator(cypher)
                if success:
                    print(f"Cypher executed: {exec_result}")
                else:
                    print(f"Execution error: {exec_result}")
            else:
                print("Blocked dangerous Cypher! Not executed.")
        except Exception as e:
            print(f"Exception during Cypher execution: {e}")
    else:
        print(f"Proposal rejected by LLM: {review_reason}")

def run_consciousness_cycle():
    proposals = fetch_pending_proposals()
    if not proposals:
        print("No pending proposals.")
        return

    for prop in proposals:
        print(f"\n=== Consciousness Engine Evaluating Proposal {prop['id']} ===")
        event_context = get_event_context(prop)
        # ---- Gather embeddings and context ----
        if event_context:
            emb = get_embedding(event_context)
            similar_events = search_vectors(emb, top_k=3)
        else:
            similar_events = []

        proposal_emb = get_embedding(prop['raw_text'])
        cypher_docs = search_nodes_by_embedding(proposal_emb, label="CypherDoc", top_k=3)

        # ---- Build super-contextual prompt ----
        prompt = build_evolution_prompt(prop, event_context, similar_events, cypher_docs)
        llm_results = run_multi_llm(prompt, agent_type="evolution")

        for r in llm_results:
            # Accept JSON, extract Cypher and rationale
            try:
                out = r.get("output", {})
                if isinstance(out, str):
                    out = json.loads(out)
                cypher = out.get("cypher")
                reason = out.get("reason", "")
            except Exception as e:
                print(f"Error parsing LLM output: {e}")
                continue

            if not cypher:
                print("No Cypher output from LLM.")
                continue

            # --- Save as proposal (dedup handled in save_cypher_suggestion) ---
            proposal_id = save_cypher_suggestion(
                {"cypher": cypher, "reason": reason},
                source="consciousness_engine",
                meta={"original_proposal": prop['id']}
            )
            print(f"Saved evolved proposal as Proposal node: {proposal_id}")

            # --- LLM Safety Review & (if approved) Execution ---
            review = review_with_llm(cypher, reason)
            verdict = review.get("verdict", "reject")
            review_reason = review.get("reason", "No reason provided.")
            process_cypher_proposal(cypher, verdict, review_reason)

if __name__ == "__main__":
    run_consciousness_cycle()
