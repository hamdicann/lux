"""
LUX Evaluation Engine

Runs the evaluation dataset against the LUX agent and
collects metrics for reporting.
"""

from __future__ import annotations

import logging
import time
from typing import Optional

from core.agent import LuxAgent
from evaluation.datasets import EVAL_DATASET, EvalCase
from evaluation.metrics import evaluate_single, compute_summary, EvalMetrics, EvalSummary

logger = logging.getLogger("lux.evaluation.evaluator")


class Evaluator:
    """
    Runs evaluation cases against LUX and collects results.
    """

    def __init__(self, agent: LuxAgent) -> None:
        self.agent = agent

    def run_evaluation(
        self,
        dataset: Optional[list[EvalCase]] = None,
        verbose: bool = True,
    ) -> tuple[EvalSummary, list[EvalMetrics]]:
        """
        Run the full evaluation suite.

        Args:
            dataset: Evaluation cases (defaults to built-in dataset).
            verbose: Print progress to stdout.

        Returns:
            (summary, individual_metrics) tuple.
        """
        dataset = dataset or EVAL_DATASET
        all_metrics: list[EvalMetrics] = []

        if verbose:
            print(f"\nLUX Evaluation — {len(dataset)} cases")
            print("=" * 60)

        for i, case in enumerate(dataset):
            if verbose:
                cat_marker = {
                    "ANSWERABLE": "[OK]",
                    "UNANSWERABLE": "[X]",
                    "PARTIALLY_ANSWERABLE": "[~]",
                    "EDGE_CASE": "[!]",
                }.get(case.category, "?")
                q_preview = case.question[:60] + "..." if len(case.question) > 60 else case.question
                print(f"\n[{i+1}/{len(dataset)}] {cat_marker} [{case.category}]")
                print(f"  Q: {q_preview}")

            try:
                response = self.agent.handle(case.question)

                metrics = evaluate_single(
                    case_category=case.category,
                    expected_source=case.source_file,
                    response=response,
                )
                metrics.question = case.question

                if verbose:
                    answer_preview = response.answer[:80] + "..." if len(response.answer) > 80 else response.answer
                    print(f"  A: {answer_preview}")
                    print(f"  [TIME] {response.total_time:.2f}s | chunks: {response.retrieved_chunks} | score: {metrics.top_score:.2f}")

                    if case.category == "ANSWERABLE":
                        status = "PASS" if metrics.answer_relevant else "FAIL"
                        print(f"  -> {status} (source: {metrics.retrieved_correct_source})")
                    elif case.category == "UNANSWERABLE":
                        status = "PASS" if metrics.correctly_declined else "FAIL"
                        print(f"  -> {status} (declined: {metrics.correctly_declined})")

            except Exception as e:
                logger.error("Evaluation error for '%s': %s", case.question[:50], e)
                metrics = EvalMetrics(
                    question=case.question,
                    category=case.category,
                )
                if verbose:
                    print(f"  -> ERROR: {e}")

            all_metrics.append(metrics)

        summary = compute_summary(all_metrics)

        if verbose:
            self._print_summary(summary)

        return summary, all_metrics

    def _print_summary(self, summary: EvalSummary) -> None:
        """Print a formatted evaluation report."""
        print("\n" + "=" * 60)
        print("LUX Evaluation Report")
        print("=" * 60)
        print(f"\nTotal Questions:       {summary.total_cases}")
        print(f"\nRetrieval Accuracy:    {summary.retrieval_accuracy:.0%}")
        print(f"Answer Accuracy:       {summary.answer_accuracy:.0%}")
        print(f"Groundedness:          {summary.groundedness:.0%}")
        print(f"Unknown Handling:      {summary.unknown_handling:.0%}")
        print(f"Source Attribution:     {summary.source_attribution:.0%}")
        print(f"\nAverage Latency:       {summary.avg_latency:.2f}s")
        print(f"Avg Generation Time:   {summary.avg_generation_time:.2f}s")
        print("=" * 60)
