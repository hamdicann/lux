"""
LUX Output Policies

Defines rules for responsible output: grounding enforcement,
hallucination prevention, and source attribution validation.
"""

from __future__ import annotations

import logging

logger = logging.getLogger("lux.core.policies")


# Minimum similarity for a chunk to be considered "relevant"
RELEVANCE_THRESHOLD = 0.35

# If no chunk exceeds this score, declare insufficient context
INSUFFICIENT_CONTEXT_MESSAGE = (
    "I don't have enough information in the local knowledge base "
    "to answer that reliably."
)

ALTERNATIVE_INSUFFICIENT_MESSAGE = (
    "I couldn't find a sufficiently relevant source in the local "
    "knowledge base to answer this question."
)


def check_retrieval_sufficiency(
    scores: list[float],
    min_similarity: float = RELEVANCE_THRESHOLD,
) -> bool:
    """
    Check if retrieved results are sufficiently relevant.

    Returns True if at least one result meets the threshold.
    """
    if not scores:
        return False
    return any(s >= min_similarity for s in scores)


def should_decline_answer(
    retrieval_used: bool,
    results_found: int,
    top_score: float,
    min_similarity: float = RELEVANCE_THRESHOLD,
) -> bool:
    """
    Determine if LUX should decline to answer.

    Returns True if retrieval was used but no relevant results found.
    """
    if not retrieval_used:
        return False  # Chat mode — always respond

    if results_found == 0:
        return True

    if top_score < min_similarity:
        return True

    return False
