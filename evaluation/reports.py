"""
LUX Evaluation Report Generator

Generates formatted text and JSON reports from evaluation results.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from evaluation.metrics import EvalSummary, EvalMetrics


def generate_text_report(
    summary: EvalSummary,
    metrics: list[EvalMetrics],
    config: Optional[object] = None,
) -> str:
    """Generate a human-readable text report."""
    lines = [
        "=" * 60,
        "LUX EVALUATION REPORT",
        f"Generated: {datetime.utcnow().isoformat()}",
        "=" * 60,
        "",
        f"Total Questions:       {summary.total_cases}",
        "",
        "── Metrics ────────────────────────────",
        f"Retrieval Accuracy:    {summary.retrieval_accuracy:.0%}",
        f"Answer Accuracy:       {summary.answer_accuracy:.0%}",
        f"Groundedness:          {summary.groundedness:.0%}",
        f"Unknown Handling:      {summary.unknown_handling:.0%}",
        f"Source Attribution:    {summary.source_attribution:.0%}",
        "",
        "── Performance ────────────────────────",
        f"Average Latency:       {summary.avg_latency:.2f}s",
        f"Avg Generation Time:   {summary.avg_generation_time:.2f}s",
        "",
        "── Details ────────────────────────────",
    ]

    for m in metrics:
        status = "PASS" if (m.answer_relevant or m.correctly_declined) else "FAIL"
        q = m.question[:60] + "..." if len(m.question) > 60 else m.question
        lines.append(f"[{status}] [{m.category}] {q}")
        lines.append(f"       time={m.total_time:.2f}s score={m.top_score:.2f} chunks={m.num_chunks_retrieved}")

    lines.append("")
    lines.append("=" * 60)
    return "\n".join(lines)


def generate_json_report(
    summary: EvalSummary,
    metrics: list[EvalMetrics],
) -> dict:
    """Generate a JSON report for programmatic use."""
    return {
        "generated_at": datetime.utcnow().isoformat(),
        "summary": {
            "total_cases": summary.total_cases,
            "retrieval_accuracy": round(summary.retrieval_accuracy, 4),
            "answer_accuracy": round(summary.answer_accuracy, 4),
            "groundedness": round(summary.groundedness, 4),
            "unknown_handling": round(summary.unknown_handling, 4),
            "source_attribution": round(summary.source_attribution, 4),
            "avg_latency": round(summary.avg_latency, 3),
            "avg_generation_time": round(summary.avg_generation_time, 3),
        },
        "cases": [
            {
                "question": m.question[:100],
                "category": m.category,
                "retrieval_used": m.retrieval_used,
                "correct_source": m.retrieved_correct_source,
                "answer_relevant": m.answer_relevant,
                "grounded": m.answer_grounded,
                "correctly_declined": m.correctly_declined,
                "top_score": round(m.top_score, 4),
                "total_time": round(m.total_time, 3),
            }
            for m in metrics
        ],
    }


def save_report(
    summary: EvalSummary,
    metrics: list[EvalMetrics],
    output_dir: Path,
) -> tuple[Path, Path]:
    """Save both text and JSON reports to the output directory."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

    text_path = output_dir / f"eval_report_{timestamp}.txt"
    text_path.write_text(generate_text_report(summary, metrics), encoding="utf-8")

    json_path = output_dir / f"eval_report_{timestamp}.json"
    json_path.write_text(
        json.dumps(generate_json_report(summary, metrics), indent=2),
        encoding="utf-8",
    )

    return text_path, json_path
