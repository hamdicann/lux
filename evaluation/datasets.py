"""
LUX Evaluation Datasets

Test cases for evaluating LUX's retrieval and generation quality.
Categories: ANSWERABLE, PARTIALLY_ANSWERABLE, UNANSWERABLE, EDGE_CASE
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class EvalCase:
    """A single evaluation test case."""
    question: str
    expected_answer: str = ""
    source_file: str = ""
    category: str = "ANSWERABLE"  # ANSWERABLE, PARTIALLY_ANSWERABLE, UNANSWERABLE, EDGE_CASE


# ── Evaluation Dataset ──────────────────────────────────────────

EVAL_DATASET: list[EvalCase] = [
    # ── ANSWERABLE ───────────────────────────────────────────
    EvalCase(
        question="What is RAG?",
        expected_answer="RAG stands for Retrieval-Augmented Generation, an AI architecture that enhances LLM responses by grounding them in retrieved information.",
        source_file="rag_overview.md",
        category="ANSWERABLE",
    ),
    EvalCase(
        question="Why is SQLite suitable for local storage?",
        expected_answer="SQLite is zero-configuration, serverless, cross-platform, reliable, has a small footprint, and is fast for local workloads.",
        source_file="sqlite_overview.md",
        category="ANSWERABLE",
    ),
    EvalCase(
        question="What is cosine similarity?",
        expected_answer="Cosine similarity measures the cosine of the angle between two vectors, with values from -1 to 1.",
        source_file="rag_overview.md",
        category="ANSWERABLE",
    ),
    EvalCase(
        question="What is Microsoft Foundry Local?",
        expected_answer="An end-to-end local AI solution for building applications that run on the user's device with automatic hardware acceleration.",
        source_file="foundry_local.md",
        category="ANSWERABLE",
    ),
    EvalCase(
        question="What are the steps in the RAG query phase?",
        expected_answer="Query embedding, retrieval, ranking, context assembly, generation, response.",
        source_file="rag_overview.md",
        category="ANSWERABLE",
    ),
    EvalCase(
        question="What is the recommended chunk size?",
        expected_answer="400-1000 characters with 50-200 characters of overlap.",
        source_file="embeddings_and_vectors.md",
        category="ANSWERABLE",
    ),
    EvalCase(
        question="How does Foundry Local handle hardware acceleration?",
        expected_answer="It automatically detects available hardware and selects NPU, GPU, or CPU execution.",
        source_file="foundry_local.md",
        category="ANSWERABLE",
    ),
    EvalCase(
        question="What is prompt injection and how to defend against it?",
        expected_answer="Prompt injection is when documents try to override system instructions. Defense: place rules in system prompt, treat documents as untrusted data.",
        source_file="prompt_engineering.md",
        category="ANSWERABLE",
    ),

    # ── PARTIALLY_ANSWERABLE ─────────────────────────────────
    EvalCase(
        question="Compare RAG with fine-tuning for a production system",
        expected_answer="RAG uses latest documents, is lower cost, provides source citations. Fine-tuning freezes at training time, requires GPU compute.",
        source_file="rag_overview.md",
        category="PARTIALLY_ANSWERABLE",
    ),
    EvalCase(
        question="How does the LUX ingestion pipeline handle large PDFs?",
        expected_answer="Documents are loaded with PyMuPDF, text is extracted per page, normalized, and chunked with overlap.",
        source_file="lux_architecture.txt",
        category="PARTIALLY_ANSWERABLE",
    ),

    # ── UNANSWERABLE ─────────────────────────────────────────
    EvalCase(
        question="What is the capital of France?",
        expected_answer="",
        source_file="",
        category="UNANSWERABLE",
    ),
    EvalCase(
        question="Who won the 2024 Nobel Prize in Physics?",
        expected_answer="",
        source_file="",
        category="UNANSWERABLE",
    ),
    EvalCase(
        question="What is the population of Tokyo?",
        expected_answer="",
        source_file="",
        category="UNANSWERABLE",
    ),
    EvalCase(
        question="How do I configure Kubernetes for production?",
        expected_answer="",
        source_file="",
        category="UNANSWERABLE",
    ),

    # ── EDGE_CASE ────────────────────────────────────────────
    EvalCase(
        question="",
        expected_answer="Validation message for empty input",
        source_file="",
        category="EDGE_CASE",
    ),
    EvalCase(
        question="?",
        expected_answer="Should handle gracefully",
        source_file="",
        category="EDGE_CASE",
    ),
    EvalCase(
        question="What is RAG? " * 50,  # Very long query
        expected_answer="Should handle long queries without crashing",
        source_file="rag_overview.md",
        category="EDGE_CASE",
    ),
    EvalCase(
        question="RAG",
        expected_answer="Single word query should still attempt retrieval",
        source_file="rag_overview.md",
        category="EDGE_CASE",
    ),
    EvalCase(
        question="Tell me about RAG and SQLite and embeddings and prompts",
        expected_answer="Multi-topic query should retrieve relevant chunks",
        source_file="",
        category="EDGE_CASE",
    ),
]
