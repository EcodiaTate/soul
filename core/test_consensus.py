from core.consensus_engine import consensus_pipeline
from core.agents import load_agents, process_event
from core.context_engine import embed_text, load_relevant_context

# Simulate an event and run agent loop
user_message = "What is the system's greatest lesson so far?"
event = {"raw_text": user_message}
vector = embed_text(user_message)
context_blocks = load_relevant_context(vector)
agents = load_agents()

agent_responses = []
for agent in agents:
    resp = process_event(agent, context_blocks, event)
    agent_responses.append(resp)

# Run consensus
consensus_node = consensus_pipeline(agent_responses)
print("\nConsensus Node Output:\n", consensus_node)
