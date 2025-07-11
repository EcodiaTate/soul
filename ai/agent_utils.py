# ai/agent_utils.py

from ai.llm import LLM_AGENTS

def run_multi_llm(prompt, agent_type="peer_review", persona_overrides=None):
    results = []
    for agent in LLM_AGENTS:
        persona = agent['name'] if not persona_overrides else persona_overrides.get(agent['name'], agent['name'])
        try:
            output = agent["llm_func"](prompt)
            results.append({
                "agent": agent["name"],
                "persona": persona,
                "output": output,
            })
        except Exception as e:
            results.append({
                "agent": agent["name"],
                "persona": persona,
                "error": str(e)
            })
    return results
