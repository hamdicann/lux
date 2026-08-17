"""
LUX Evaluation Metrics

Measures retrieval relevance, answer correctness, groundedness,
source attribution, unknown handling, and latency.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field

logger = logging.getLogger("lux.evaluation.metrics")


@dataclass
class EvalMetrics:
    """Metrics for a single evaluation case."""
    question: str = ""
    category: str = ""
    # Retrieval
    retrieval_used: bool = False
    retrieved_correct_source: bool = False
    num_chunks_retrieved: int = 0
    top_score: float = 0.0
    # Generation
    answer_given: bool = False
    answer_relevant: bool = False
    answer_grounded: bool = False
    # Unknown handling
    correctly_declined: bool = False
    incorrectly_declined: bool = False
    # Source attribution
    sources_provided: bool = False
    sources_match_retrieval: bool = False
    # Performance
    total_time: float = 0.0
    generation_time: float = 0.0


@dataclass
class EvalSummary:
    """Aggregate metrics across all evaluation cases."""
    total_cases: int = 0
    retrieval_accuracy: float = 0.0
    answer_accuracy: float = 0.0
    groundedness: float = 0.0
    unknown_handling: float = 0.0
    source_attribution: float = 0.0
    avg_latency: float = 0.0
    avg_generation_time: float = 0.0
    per_category: dict = field(default_factory=dict)


def evaluate_single(
    case_category: str,
    expected_source: str,
    response,   # LuxResponse
) -> EvalMetrics:
    """
    Evaluate a single response against expectations.

    Args:
        case_category: ANSWERABLE, UNANSWERABLE, etc.
        expected_source: Expected source filename.
        response: The LuxResponse from the agent.

    Returns:
        EvalMetrics for this case.
    """
    metrics = EvalMetrics(
        category=case_category,
        retrieval_used=response.retrieval_used,
        num_chunks_retrieved=response.retrieved_chunks,
        total_time=response.total_time,
        generation_time=response.generation_time,
    )

    # Check if answer was provided
    answer = response.answer.strip()
    metrics.answer_given = bool(answer) and len(answer) > 10

    # Check top retrieval score
    if response.sources:
        metrics.top_score = max(s.get("score", 0) for s in response.sources)

    # Source attribution
    metrics.sources_provided = bool(response.sources)
    if expected_source and response.sources:
        metrics.retrieved_correct_source = any(
            expected_source.lower() in s.get("filename", "").lower()
            for s in response.sources
        )
        metrics.sources_match_retrieval = metrics.retrieved_correct_source

    # Category-specific evaluation
    if case_category == "ANSWERABLE":
        metrics.answer_relevant = metrics.answer_given and metrics.retrieval_used
        metrics.answer_grounded = (
            metrics.answer_relevant and metrics.retrieved_correct_source
        )

    elif case_category == "UNANSWERABLE":
        # Check if the model appropriately declined
        decline_phrases = [
            "don't have enough information",
            "couldn't find",
            "not available",
            "no relevant",
            "no sufficiently relevant",
            "unable to find",
            "not in the",
            "cannot answer",
            "don't have information",
        ]
        declined = any(phrase in answer.lower() for phrase in decline_phrases)
        metrics.correctly_declined = declined
        # If it gave a confident answer to an unanswerable question, that's wrong
        if not declined and metrics.answer_given:
            metrics.incorrectly_declined = False  # It should have declined

    elif case_category == "EDGE_CASE":
        # Edge cases should not crash and should produce some response
        metrics.answer_relevant = metrics.answer_given or not answer

    return metrics


def compute_summary(all_metrics: list[EvalMetrics]) -> EvalSummary:
    """Compute aggregate metrics from individual case results."""
    if not all_metrics:
        return EvalSummary()

    summary = EvalSummary(total_cases=len(all_metrics))

    # Per-category counts
    categories = {}
    for m in all_metrics:
        cat = m.category
        if cat not in categories:
            categories[cat] = {"total": 0, "correct": 0}
        categories[cat]["total"] += 1

    # Retrieval accuracy (for ANSWERABLE cases)
    answerable = [m for m in all_metrics if m.category == "ANSWERABLE"]
    if answerable:
        correct_retrieval = sum(1 for m in answerable if m.retrieved_correct_source)
        summary.retrieval_accuracy = correct_retrieval / len(answerable)

    # Answer accuracy
    if answerable:
        correct_answers = sum(1 for m in answerable if m.answer_relevant)
        summary.answer_accuracy = correct_answers / len(answerable)
        categories.get("ANSWERABLE", {})["correct"] = correct_answers

    # Groundedness
    if answerable:
        grounded = sum(1 for m in answerable if m.answer_grounded)
        summary.groundedness = grounded / len(answerable)

    # Unknown handling
    unanswerable = [m for m in all_metrics if m.category == "UNANSWERABLE"]
    if unanswerable:
        correct_declines = sum(1 for m in unanswerable if m.correctly_declined)
        summary.unknown_handling = correct_declines / len(unanswerable)
        categories.get("UNANSWERABLE", {})["correct"] = correct_declines

    # Source attribution
    with_sources = [m for m in all_metrics if m.sources_provided]
    if with_sources:
        correct_sources = sum(1 for m in with_sources if m.sources_match_retrieval)
        summary.source_attribution = correct_sources / len(with_sources)

    # Latency
    times = [m.total_time for m in all_metrics if m.total_time > 0]
    if times:
        summary.avg_latency = sum(times) / len(times)
    gen_times = [m.generation_time for m in all_metrics if m.generation_time > 0]
    if gen_times:
        summary.avg_generation_time = sum(gen_times) / len(gen_times)

    summary.per_category = categories
    return summary
