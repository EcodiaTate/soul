import logging
import json
import traceback
from ai.living_agent import LivingAgent
from ai.agent_manager import AgentManager
from core.vectors import search_vectors
from actuators.all_outputs import execute_action
from dreamspace.dream import dream_cycle
from core.db import get_session

logging.basicConfig(level=logging.INFO, filename="logs/world_brain.log")

class EcodiaWorldSoul:
    def __init__(self):
        self.agent_manager = AgentManager()
        self.relationships = {}      # {user_id: {...}} for future expansion
        self.action_log = []         # (could move to DB or log file)
        self.global_mood = "hopeful"
        self.init_agents()

    def init_agents(self):
        # Register or verify base agents (do not re-create if already in registry)
        existing = self.agent_manager.all_agents()
        if not existing:
            from ai.llm import openai_llm, gemini_llm, claude_llm
            self.agent_manager.register(self.agent_manager.spawn("EcodiaGPT", openai_llm, "gpt-4"))
            self.agent_manager.register(self.agent_manager.spawn("EcodiaGemini", gemini_llm, "gemini-1.5-pro"))
            self.agent_manager.register(self.agent_manager.spawn("EcodiaClaude", claude_llm, "claude-3-opus"))

    def fetch_unprocessed_events(self):
        with get_session() as session:
            result = session.run("MATCH (e:Event {status:'unprocessed'}) RETURN id(e) as eid, e.raw_text as raw_text, e.embedding as embedding")
            return [dict(r) for r in result]

    def mark_event_processed(self, eid):
        with get_session() as session:
            session.run("MATCH (e:Event) WHERE id(e) = $eid SET e.status = 'processed', e.processed = timestamp()", eid=eid)

    def ingest_and_reflect(self):
        """Main event cycle: Ingest new events, run all agent reflections, debate, decide, act, log."""
        try:
            events = self.fetch_unprocessed_events()
            for event in events:
                context = search_vectors(event['embedding'], top_k=10)
                reflections = []
                for agent in self.agent_manager.all_agents():
                    reflection = agent.reflect(event, context)
                    reflections.append(reflection)
                action_plan = self.debate_and_decide(event, reflections)
                if action_plan:
                    execute_action(action_plan)
                    self.action_log.append(action_plan)
                    logging.info(f"Action taken: {action_plan}")
                self.mark_event_processed(event["eid"])
        except Exception as e:
            logging.error(f"[ingest_and_reflect] Exception: {e}\n{traceback.format_exc()}")

    def debate_and_decide(self, event, reflections):
        """Meta-agent or democratic debate over reflections. Extendable for consensus, voting, etc."""
        try:
            proposals = []
            for ref in reflections:
                if isinstance(ref, dict) and ref.get("proposals"):
                    proposals.extend(ref["proposals"])
            if proposals:
                plan = {
                    "event_id": event.get("eid"),
                    "actions": proposals,
                    "source": "debate_and_decide"
                }
                return plan
            return None
        except Exception as e:
            logging.error(f"[debate_and_decide] Exception: {e}\n{traceback.format_exc()}")
            return None

    def run_dreamspace(self):
        """Dream new ideas, mutate ontology, or spawn new agents."""
        try:
            dreams = dream_cycle(self)
            for dream in dreams:
                execute_action(dream)
                logging.info(f"Dream action: {dream}")
        except Exception as e:
            logging.error(f"[run_dreamspace] Exception: {e}\n{traceback.format_exc()}")

    def full_cycle(self):
        """Run the full living soul pipeline: events, agent society, debate, action, dreams, decay, logging."""
        logging.info("=== Full Ecodia WorldSoul Cycle Start ===")
        self.ingest_and_reflect()
        self.run_dreamspace()
        # Insert future: decay, relationship update, mood drift, time-travel/rollback here.
        logging.info("=== Full Ecodia WorldSoul Cycle End ===")

if __name__ == "__main__":
    soul = EcodiaWorldSoul()
    soul.full_cycle()
    print("Ecodia full world brain cycle complete. Check logs for full trace.")
