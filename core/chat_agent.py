# core/chat_agent.py

from core.prompts import chat_response_prompt, get_ecodia_identity
from core.llm_tools import run_llm  # This routes to Claude for 'agent="claude"' and 'purpose="chat"'
# from core.context_engine import format_context_blocks 

def generate_chat_reply(raw_text: str) -> str: # ,context_blocks: list
    """
    Generate a fast, high-quality chat reply using Claude (via llm_tools), including full identity context and relevant memory blocks.
    """
    identity = get_ecodia_identity()
    #formatted_blocks = format_context_blocks(context_blocks)
    prompt = chat_response_prompt(identity, raw_text) #,formatted_blocks
    # Explicitly use Claude as agent and purpose="chat"
    response = run_llm(prompt, agent="claude", purpose="chat")
    return response.strip()
