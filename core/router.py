"""
LUX Query Router

Lightweight classifier that determines whether a user query
needs RAG retrieval or can be handled as a simple chat.
"""

from __future__ import annotations

import logging
import re
from enum import Enum

logger = logging.getLogger("lux.core.router")


class QueryType(Enum):
    """Classification of user queries."""
    RAG_QUERY = "rag_query"    # Needs document retrieval
    CHAT = "chat"              # Simple conversation
    GENERAL = "general"        # General knowledge (no retrieval needed)


# Keywords that suggest the user wants document-based information
_RAG_INDICATORS = [
    "document", "documents", "file", "files", "knowledge base",
    "according to", "based on", "what does", "what do",
    "explain from", "find in", "search for", "look up",
    "in the", "from the", "describe the", "summarize",
    "what is", "what are", "how does", "how do",
    "why is", "why does", "why do", "when was", "when did",
    "who is", "who was", "where is", "where was",
    "tell me about", "information about", "details about",
    "defined as", "definition of", "meaning of",
    "rag", "retrieval", "embedding", "sqlite", "foundry",
    "architecture", "project", "implementation",
]

# Patterns that indicate conversational/non-retrieval queries
_CHAT_INDICATORS = [
    "hello", "hi", "hey", "thanks", "thank you",
    "goodbye", "bye", "good morning", "good evening",
    "how are you", "who are you", "what's your name",
    "rephrase", "rewrite", "translate",
    "can you help", "help me",
]


def classify_query(query: str) -> QueryType:
    """
    Classify a user query into RAG_QUERY, CHAT, or GENERAL.

    Uses keyword heuristics and question detection.
    Errs on the side of performing retrieval when uncertain.

    Args:
        query: The user's raw query text.

    Returns:
        QueryType classification.
    """
    if not query or not query.strip():
        return QueryType.CHAT

    query_lower = query.lower().strip()

    # Check for explicit chat patterns first
    for indicator in _CHAT_INDICATORS:
        if query_lower.startswith(indicator) or query_lower == indicator:
            logger.debug("Query classified as CHAT: '%s'", query[:50])
            return QueryType.CHAT

    # Very short queries (< 3 words) are usually chat
    word_count = len(query_lower.split())
    if word_count <= 2:
        # Unless they're clearly questions
        if query_lower.endswith("?"):
            return QueryType.RAG_QUERY
        return QueryType.CHAT

    # Check for RAG indicators
    for indicator in _RAG_INDICATORS:
        if indicator in query_lower:
            logger.debug("Query classified as RAG_QUERY: '%s'", query[:50])
            return QueryType.RAG_QUERY

    # Questions (ending with ?) default to RAG
    if query_lower.endswith("?"):
        logger.debug("Query classified as RAG_QUERY (question): '%s'", query[:50])
        return QueryType.RAG_QUERY

    # Longer queries (4+ words) that look informational → RAG
    if word_count >= 4:
        return QueryType.RAG_QUERY

    # Default: try retrieval (better to check than miss)
    return QueryType.RAG_QUERY
