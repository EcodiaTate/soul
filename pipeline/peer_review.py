import json
import logging
from core.db import get_session
from ai.agent_utils import run_multi_llm
from ai.prompts import peer_review_prompt
from core.proposals import save_cypher_suggestion

logging.basicConfig(level=logging.INFO, filename="logs/peer_review.log")

def fetch_events_for_peer_review():
    """Find events with multiple reflections but no peer reviews yet."""
    with get_session() as session:
        result = session.run("""
            MATCH (e:Event {status: 'processed'})-[:REFLECTED]->(r)
            WITH e, collect(r) as reflections
            WHERE size(reflections) > 1 AND NOT (e)-[:PEER_REVIEWED]->()
            RETURN e.id AS id, e.raw_text AS raw_text
        """)
        return [r.data() for r in result]

def fetch_reflections(event_id):
    """Return all Reflection nodes for the event."""
    with get_session() as session:
        result = session.run("""
            MATCH (e:Event {id: $id})-[:REFLECTED]->(r)
            RETURN r
        """, id=event_id)
        return [r["r"] for r in result]

def fetch_prev_peer_reviews(event_id):
    """For traceability: previous peer reviews if re-run."""
    with get_session() as session:
        result = session.run("""
            MATCH (e:Event {id: $id})-[:PEER_REVIEWED]->(p)
            RETURN p
        """, id=event_id)
        return [r["p"] for r in result]

def save_peer_review(event_id, agent_name, model, prompt, peer_review, prev_state=None):
    with get_session() as session:
        session.run("""
            MATCH (e:Event {id: $event_id})
            CREATE (p:PeerReview {
                agent: $agent_name,
                model: $model,
                prompt: $prompt,
                data: $peer_review,
                timestamp: timestamp(),
                prev_state: $prev_state
            })
            CREATE (e)-[:PEER_REVIEWED]->(p)
        """, event_id=event_id,
           agent_name=agent_name,
           model=model,
           prompt=prompt,
           peer_review=json.dumps(peer_review),
           prev_state=json.dumps(prev_state) if prev_state else None
        )

def main():
    events = fetch_events_for_peer_review()
    logging.info(f"Found {len(events)} events to peer review.")
    for event in events:
        event_id = event['id']
        reflections = fetch_reflections(event_id)
        if len(reflections) < 2:
            logging.info(f"Skipping event {event_id}: not enough reflections.")
            continue
        summaries = "\n".join([
            f"{r.get('source_model', 'LLM')} (score: {r.get('score', 'n/a')}): {r.get('summary', '')}" for r in reflections
        ])
        prompt = peer_review_prompt(event['raw_text'], summaries)
        results = run_multi_llm(prompt, agent_type="peer_review")
        prev_state = fetch_prev_peer_reviews(event_id)  # Traceability

        for r in results:
            if "output" not in r or isinstance(r["output"], str):
                logging.warning(f"[{r['agent']}] No valid output: {r.get('output')}")
                continue
            agent = r["agent"]
            model = r.get("model", agent)
            output = r["output"]

            # === SUGGESTION HANDLER ===
            suggestions = output.get("suggestions") if isinstance(output, dict) else []
            for s in suggestions:
                if s.get("action") == "propose_cypher" and "cypher" in s:
                    save_cypher_suggestion(s, source="peer_review", meta={"event_id": event_id, "agent": agent})

            save_peer_review(
                event_id=event_id,
                agent_name=agent,
                model=model,
                prompt=prompt,
                peer_review=output,
                prev_state=prev_state
            )
            logging.info(f"[{agent}] Peer review saved for event {event_id}.")
        print(f"Peer review completed for event {event_id}")

if __name__ == "__main__":
    main()
