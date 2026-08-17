"""
LUX — Evaluation Runner Script

Runs the complete evaluation suite and generates reports.

Usage:
    python scripts/evaluate.py
    python scripts/evaluate.py --verbose
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

from app.config import config


def main():
    parser = argparse.ArgumentParser(description="LUX Evaluation Runner")
    parser.add_argument("--verbose", action="store_true", default=True)
    parser.add_argument("--output", type=str, default="data/eval_reports")
    args = parser.parse_args()

    config.ensure_directories()

    print("LUX — Evaluation Suite")
    print("=" * 40)

    # Initialize agent
    from core.agent import LuxAgent
    agent = LuxAgent(config)
    print("Initializing LUX...")
    agent.initialize()

    # Run evaluation
    from evaluation.evaluator import Evaluator
    from evaluation.reports import save_report

    evaluator = Evaluator(agent)
    summary, metrics = evaluator.run_evaluation(verbose=args.verbose)

    # Save reports
    output_dir = _ROOT / args.output
    text_path, json_path = save_report(summary, metrics, output_dir)
    print(f"\nReports saved:")
    print(f"  Text: {text_path}")
    print(f"  JSON: {json_path}")


if __name__ == "__main__":
    main()
