"""
LUX Context Assembly

Merges system instructions, conversation history, retrieved knowledge,
and current query into a structured message list for the LLM.
Enforces context budget and conversation turn limits.
"""

from __future__ import annotations

import logging
from typing import Optional

from core.prompts import SYSTEM_PROMPT, build_rag_prompt, build_chat_prompt, build_no_results_prompt
from storage.repositories import Message

logger = logging.getLogger("lux.core.context")


def build_messages(
    user_question: str,
    context: Optional[str] = None,
    conversation_history: Optional[list[Message]] = None,
    max_turns: int = 10,
    retrieval_used: bool = False,
) -> list[dict[str, str]]:
    """
    Assemble the complete message list for the LLM.

    Message structure:
    1. System prompt (LUX identity + rules)
    2. Conversation history (truncated to max_turns)
    3. Current user message (with or without retrieved context)

    Args:
        user_question: The current user query.
        context: Formatted retrieved context (if any).
        conversation_history: Previous messages in this conversation.
        max_turns: Maximum number of history turns to include.
        retrieval_used: Whether retrieval was performed.

    Returns:
        List of message dicts ready for the OpenAI chat API.
    """
    messages: list[dict[str, str]] = []

    # 1. System prompt — always first
    messages.append({
        "role": "system",
        "content": SYSTEM_PROMPT,
    })

    # 2. Conversation history — limited to recent turns
    if conversation_history:
        # Take the most recent turns (each turn = user + assistant)
        recent = conversation_history[-(max_turns * 2):]
        for msg in recent:
            if msg.role in ("user", "assistant"):
                messages.append({
                    "role": msg.role,
                    "content": msg.content,
                })

    # 3. Current query — with or without context
    if retrieval_used and context:
        # RAG mode: include retrieved context
        user_content = build_rag_prompt(context, user_question)
    elif retrieval_used and not context:
        # Retrieval was attempted but nothing found
        user_content = build_no_results_prompt(user_question)
    else:
        # Chat mode: no retrieval
        user_content = build_chat_prompt(user_question)

    messages.append({
        "role": "user",
        "content": user_content,
    })

    logger.debug(
        "Built message list: %d messages, retrieval=%s",
        len(messages), retrieval_used,
    )
    return messages
