"""
LUX Result Ranking & Post-Processing

Removes duplicate/near-duplicate chunks, enforces source diversity,
and applies the context budget to prevent overloading the LLM.
"""

from __future__ import annotations

import logging
from typing import Optional

from rag.retrieval import RetrievalResult

logger = logging.getLogger("lux.rag.ranking")


def deduplicate_results(
    results: list[RetrievalResult],
    similarity_threshold: float = 0.95,
) -> list[RetrievalResult]:
    """
    Remove near-duplicate chunks from retrieval results.

    Two chunks are considered duplicates if their text content
    has very high overlap (measured by character-level Jaccard).
    Prefers the higher-scored chunk.
    """
    if len(results) <= 1:
        return results

    unique: list[RetrievalResult] = []
    for result in results:
        is_dup = False
        for existing in unique:
            overlap = _text_overlap(result.content, existing.content)
            if overlap > similarity_threshold:
                is_dup = True
                logger.debug(
                    "Duplicate suppressed: chunk %d (%.2f overlap with chunk %d)",
                    result.chunk_id, overlap, existing.chunk_id,
                )
                break
        if not is_dup:
            unique.append(result)

    if len(unique) < len(results):
        logger.info(
            "Deduplication: %d → %d results", len(results), len(unique)
        )

    return unique


def apply_context_budget(
    results: list[RetrievalResult],
    max_chars: int = 4000,
) -> list[RetrievalResult]:
    """
    Trim results to fit within the context budget.

    Takes results in order of relevance (highest similarity first)
    and includes as many as fit within max_chars.
    """
    if not results:
        return results

    selected: list[RetrievalResult] = []
    total_chars = 0

    for result in results:
        chunk_chars = len(result.content)
        if total_chars + chunk_chars > max_chars and selected:
            # Budget exceeded — stop adding
            logger.info(
                "Context budget reached: %d/%d chars, using %d/%d chunks",
                total_chars, max_chars, len(selected), len(results),
            )
            break
        selected.append(result)
        total_chars += chunk_chars

    return selected


def rank_and_filter(
    results: list[RetrievalResult],
    max_chars: int = 4000,
    dedup_threshold: float = 0.95,
) -> list[RetrievalResult]:
    """
    Full post-processing pipeline: deduplicate then apply budget.
    """
    results = deduplicate_results(results, dedup_threshold)
    results = apply_context_budget(results, max_chars)
    return results


def _text_overlap(text_a: str, text_b: str) -> float:
    """
    Compute character-level Jaccard similarity between two texts.
    Returns 0.0 to 1.0.
    """
    if not text_a or not text_b:
        return 0.0

    # Use character trigrams for more robust comparison
    trigrams_a = set(_get_trigrams(text_a))
    trigrams_b = set(_get_trigrams(text_b))

    if not trigrams_a or not trigrams_b:
        return 0.0

    intersection = len(trigrams_a & trigrams_b)
    union = len(trigrams_a | trigrams_b)

    return intersection / union if union > 0 else 0.0


def _get_trigrams(text: str) -> list[str]:
    """Extract character trigrams from text."""
    text = text.lower().strip()
    return [text[i:i+3] for i in range(len(text) - 2)]
