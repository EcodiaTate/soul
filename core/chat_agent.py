# core/chat_agent.py

from core.prompts import chat_response_prompt
from core.llm_tools import run_llm  # uses Claude or default
from core.context_engine import format_context_blocks
from core.prompts import get_ecodia_identity, chat_response_prompt

def generate_chat_reply(raw_text: str, context_blocks: list) -> str:
    identity = get_ecodia_identity()
    formatted_blocks = format_context_blocks(context_blocks)
    prompt = chat_response_prompt(identity, raw_text, formatted_blocks)

    response = run_llm(prompt, agent="Claude")
    return response.strip()
