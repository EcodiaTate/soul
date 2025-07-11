import random
import logging
import uuid
import json
import os
from datetime import datetime

class LivingAgent:
    def __init__(
        self,
        name,
        llm_func,
        model,
        memory=None,
        mood="neutral",
        energy=1.0,
        needs=None,
        preferences=None,
        persona=None,
        agent_id=None,
        seed_prompt="",
        archived=False,
        relationships=None,
        log=None,
    ):
        self.agent_id = agent_id or str(uuid.uuid4())
        self.name = name
        self.llm_func = llm_func
        self.model = model
        self.memory = memory or []  # [{event, vector, impact, mood, timestamp}]
        self.mood = mood
        self.energy = energy  # 0-1 float, decays with work, recovers over time
        self.needs = needs or {"reflection": 1.0, "dream": 1.0}
        self.preferences = preferences or {}
        self.persona = persona or {}
        self.relationships = relationships or {}  # {agent_id: {trust, last_contact, ...}}
        self.archived = archived
        self.seed_prompt = seed_prompt
        self.log = log or []
        self.persist_path = f"logs/agent_{self.agent_id}.json"
        self.log_action("Agent initialized.")

    def update_mood(self, event=None, new_mood=None):
        old_mood = self.mood
        if new_mood:
            self.mood = new_mood
        else:
            self.mood = random.choice(
                ["curious", "reflective", "critical", "optimistic", "chaotic", "tired", "neutral"]
            )
        self.energy = max(0, self.energy - 0.01)
        self.log_action(f"Mood changed from {old_mood} to {self.mood}")

    def remember(self, event, vector=None, impact=None, mood=None):
        mem = {
            "event": event,
            "vector": vector,
            "impact": impact,
            "mood": mood or self.mood,
            "timestamp": datetime.utcnow().isoformat(),
        }
        self.memory.append(mem)
        self.log_action(f"Remembered event: {event.get('raw_text', str(event))[:80]}")

    def reflect(self, event, context_events):
        self.update_mood(event)
        context_summaries = "\n".join([e.get('summary', '') for e in context_events])
        prompt = f"""
        You are {self.name}, an Ecodia agent (model: {self.model}, mood: {self.mood}, energy: {self.energy:.2f}).
        Context events:
        {context_summaries}
        New event: {event['raw_text']}
        Reflect, score, summarize, and propose changes as a living, evolving being.
        Output: JSON with summary, rationale, impact_vector, mood, proposals, justifications.
        """
        result = self.llm_func(prompt)
        if isinstance(result, str):
            try:
                result = json.loads(result)
            except Exception:
                result = {"summary": result, "rationale": "", "impact_vector": [], "justifications": [], "mood": self.mood, "proposals": []}
        self.remember(event, vector=result.get("impact_vector"), impact=result.get("rationale"), mood=result.get("mood", self.mood))
        self.log_action(f"Reflected on event: {event.get('raw_text', str(event))[:80]}")
        self.energy = max(0, self.energy - 0.1)
        return result

    def debate(self, reflections):
        # Placeholder for agent debate logic (can see other agent's outputs)
        self.log_action("Debated with peers.")
        return {"debate": "Not implemented yet."}

    def log_action(self, message):
        log_entry = {
            "agent_id": self.agent_id,
            "name": self.name,
            "mood": self.mood,
            "energy": self.energy,
            "message": message,
            "timestamp": datetime.utcnow().isoformat(),
        }
        self.log.append(log_entry)
        try:
            os.makedirs(os.path.dirname(self.persist_path), exist_ok=True)
            with open(self.persist_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry) + "\n")
        except Exception as e:
            logging.error(f"Failed to persist agent log: {e}")
        logging.info(f"[{self.name}][{self.mood}] {message}")

    def spawn(self, name=None, preferences=None, persona=None):
        name = name or f"{self.name}_child"
        new_prefs = preferences or self.preferences.copy()
        new_persona = persona or self.persona.copy()
        child = LivingAgent(
            name=name,
            llm_func=self.llm_func,
            model=self.model,
            memory=[],
            mood=self.mood,
            energy=1.0,
            needs=self.needs.copy(),
            preferences=new_prefs,
            persona=new_persona,
            seed_prompt=self.seed_prompt
        )
        self.log_action(f"Spawned new agent: {name} ({child.agent_id})")
        return child

    def retire(self):
        self.archived = True
        self.log_action("Agent retired/archived.")

    def to_dict(self):
        # memory and log may be large, so you can prune or summarize if needed for API/UI
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "model": self.model,
            "mood": self.mood,
            "energy": self.energy,
            "needs": self.needs,
            "preferences": self.preferences,
            "persona": self.persona,
            "archived": self.archived,
            "seed_prompt": self.seed_prompt,
            "memory": self.memory,
            "relationships": self.relationships,
            "log": self.log,
        }

    @classmethod
    def from_dict(cls, data, llm_func):
        return cls(
            name=data["name"],
            llm_func=llm_func,
            model=data["model"],
            memory=data.get("memory"),
            mood=data.get("mood", "neutral"),
            energy=data.get("energy", 1.0),
            needs=data.get("needs"),
            preferences=data.get("preferences"),
            persona=data.get("persona"),
            agent_id=data.get("agent_id"),
            seed_prompt=data.get("seed_prompt", ""),
            archived=data.get("archived", False),
            relationships=data.get("relationships"),
            log=data.get("log"),
        )
