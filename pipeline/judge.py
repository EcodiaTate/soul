import json
import logging
from core.db import get_session
from ai.prompts import judge_prompt
from ai.agent_utils import run_multi_llm
from core.proposals import save_cypher_suggestion

logging.basicConfig(level=logging.INFO, filename="logs/judge.log")

def fetch_events_for_judge():
    """Find events that have peer reviews but not judged yet."""
    with get_session() as session:
        result = session.run("""
            MATCH (e:Event {status: 'processed'})-[:PEER_REVIEWED]->(p)
            WHERE NOT (e)-[:JUDGED]->()
            RETURN DISTINCT e.id AS id, e.raw_text AS raw_text
        """)
        return [r.data() for r in result]

def fetch_peer_reviews(event_id):
    with get_session() as session:
        result = session.run("""
            MATCH (e:Event {id: $id})-[:PEER_REVIEWED]->(p)
            RETURN p
        """, id=event_id)
        return [r["p"] for r in result]

def fetch_prev_judges(event_id):
    with get_session() as session:
        result = session.run("""
            MATCH (e:Event {id: $id})-[:JUDGED]->(j)
            RETURN j
        """, id=event_id)
        return [r["j"] for r in result]

def save_judge(event_id, agent_name, model, prompt, judge_data, prev_state=None):
    with get_session() as session:
        session.run("""
            MATCH (e:Event {id: $event_id})
            CREATE (j:Judge {
                agent: $agent_name,
                model: $model,
                prompt: $prompt,
                data: $judge_data,
                timestamp: timestamp(),
                prev_state: $prev_state
            })
            CREATE (e)-[:JUDGED]->(j)
        """, event_id=event_id,
           agent_name=agent_name,
           model=model,
           prompt=prompt,
           judge_data=json.dumps(judge_data),
           prev_state=json.dumps(prev_state) if prev_state else None
        )

def main():
    events = fetch_events_for_judge()
    logging.info(f"Found {len(events)} events to judge.")
    for event in events:
        event_id = event['id']
        peer_reviews = fetch_peer_reviews(event_id)
        all_reviews = "\n".join([str(p["data"]) for p in peer_reviews])
        prompt = judge_prompt(event['raw_text'], all_reviews)
        results = run_multi_llm(prompt, agent_type="judge")
        prev_state = fetch_prev_judges(event_id)
        for r in results:
            agent = r["agent"]
            model = r.get("model", agent)
            output = r.get("output")
            if not output:
                logging.warning(f"[{agent}] No valid judge output.")
                continue

            # === SUGGESTION HANDLER ===
            suggestions = output.get("suggestions") if isinstance(output, dict) else []
            for s in suggestions:
                if s.get("action") == "propose_cypher" and "cypher" in s:
                    save_cypher_suggestion(s, source="judge", meta={"event_id": event_id, "agent": agent})

            save_judge(
                event_id=event_id,
                agent_name=agent,
                model=model,
                prompt=prompt,
                judge_data=output,
                prev_state=prev_state
            )
            logging.info(f"[{agent}] Judge decision saved for event {event_id}.")
        print(f"Judge cycle complete for event {event_id}")

if __name__ == "__main__":
    main()
