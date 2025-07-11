import os
import json
from ai.living_agent import LivingAgent
from ai.llm import openai_llm, gemini_llm, claude_llm

class AgentManager:
    def __init__(self, persist_path="logs/agent_registry.json"):
        self.agents = {}  # {agent_id: agent}
        self.persist_path = persist_path
        self.load_registry()

    def register(self, agent):
        self.agents[agent.agent_id] = agent
        self.save_registry()

    def spawn(self, name, llm_func, model, persona=None, mood="neutral", preferences=None, seed_prompt=""):
        agent = LivingAgent(
            name=name,
            llm_func=llm_func,
            model=model,
            memory=[],
            mood=mood,
            preferences=preferences,
            persona=persona,
            seed_prompt=seed_prompt
        )
        self.register(agent)
        return agent

    def retire(self, agent_id):
        agent = self.agents.get(agent_id)
        if agent:
            agent.retire()
            self.save_registry()
            return True
        return False

    def all_agents(self, include_archived=False):
        return [a for a in self.agents.values() if include_archived or not a.archived]

    def get(self, agent_id=None, name=None):
        if agent_id:
            return self.agents.get(agent_id)
        if name:
            # Supports lookup by name (for backwards compat / easy find)
            for agent in self.agents.values():
                if agent.name == name:
                    return agent
        return None

    def save_registry(self):
        data = {agent_id: agent.to_dict() for agent_id, agent in self.agents.items()}
        with open(self.persist_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def load_registry(self):
        if not os.path.exists(self.persist_path):
            return
        try:
            with open(self.persist_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            for agent_id, agent_data in data.items():
                model = agent_data["model"]
                if model == "gpt-4":
                    llm_func = openai_llm
                elif "gemini" in model:
                    llm_func = gemini_llm
                elif "claude" in model:
                    llm_func = claude_llm
                else:
                    llm_func = openai_llm
                agent = LivingAgent.from_dict(agent_data, llm_func)
                self.agents[agent_id] = agent
        except Exception as e:
            print(f"Failed to load agent registry: {e}")

    # Utility for API endpoints/UI
    def list_agents_dict(self, include_archived=False):
        return [agent.to_dict() for agent in self.all_agents(include_archived=include_archived)]

def create_seed_agents():
    """
    Create an AgentManager with EcodiaGPT, EcodiaGemini, EcodiaClaude if none exist.
    Safe to call at startup.
    """
    manager = AgentManager()
    if not manager.agents:
        manager.register(LivingAgent("EcodiaGPT", openai_llm, "gpt-4"))
        manager.register(LivingAgent("EcodiaGemini", gemini_llm, "gemini-1.5-pro"))
        manager.register(LivingAgent("EcodiaClaude", claude_llm, "claude-3-opus"))
    return manager
