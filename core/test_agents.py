from core.agents import load_agents, process_event
from core.context_engine import embed_text, load_relevant_context

# 1. Simulate a user message/event
user_message = "What is the system's greatest lesson so far?"
event = {"raw_text": user_message}

# 2. Get embedding
vector = embed_text(user_message)

# 3. Retrieve context blocks (could be empty if no Neo4j connection)
context_blocks = load_relevant_context(vector)

# 4. Load your agents
agents = load_agents()

# 5. Call process_event for each agent
for agent in agents:
    print(f"\n=== Running Agent: {agent['name']} ===")
    response = process_event(agent, context_blocks, event)
    print(f"Agent Response: {response}\n")
