import os
from core.llm import llm_func
from core.prompts import contextualization_prompt
from core.vector_utils import embed_text
from core.neo4j import store_memory_block


def compress_event_with_llm(event, agent_id):
    """
    Compress a full event into a set of memory blocks (summary, insight, mood).
    """
    context_text = f"Event:\n{event['raw_text']}\n\nMetadata:\n{event.get('metadata', {})}"
    prompt = contextualization_prompt.format(text=context_text)

    response = llm_func(
        prompt=prompt,
        agent_id=agent_id,
        system="compress_context",
        temperature=0.4,
        max_tokens=512,
    )

    blocks = extract_memory_blocks(response)
    embedded_blocks = []

    for block in blocks:
        embedding = embed_text(block["text"])
        block_node = store_memory_block(
            event_id=event["id"],
            text=block["text"],
            type=block["type"],
            embedding=embedding,
            agent_id=agent_id,
        )
        embedded_blocks.append(block_node)

    return embedded_blocks


def extract_memory_blocks(response_text):
    """
    Parse LLM response into block objects. Each block must include a 'type' and 'text'.
    Assumes response is structured like:
    [Summary]
    ...
    [Insight]
    ...
    [Mood]
    ...
    """
    blocks = []
    current_type = None
    buffer = []

    for line in response_text.splitlines():
        if line.strip().startswith("[") and line.strip().endswith("]"):
            if current_type and buffer:
                blocks.append({
                    "type": current_type.lower(),
                    "text": "\n".join(buffer).strip()
                })
            current_type = line.strip().strip("[]")
            buffer = []
        else:
            buffer.append(line)

    if current_type and buffer:
        blocks.append({
            "type": current_type.lower(),
            "text": "\n".join(buffer).strip()
        })

    return blocks


def get_context_blocks(event, agent_id, max_tokens=512):
    """
    Public interface for generating context blocks from an event.
    """
    return compress_event_with_llm(event, agent_id)
