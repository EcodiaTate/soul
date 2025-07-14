from core.context_engine import embed_text, load_relevant_context
v = embed_text("Test input for memory retrieval")
blocks = load_relevant_context(v)
print(blocks)
