"""
LUX Context Builder

Assembles retrieved chunks into a human-readable context block
for the LLM prompt. Each source includes content, score, and
available metadata (filename, page, section).
"""

from __future__ import annotations

import logging
from typing import Optional

from rag.retrieval import RetrievalResult

logger = logging.getLogger("lux.rag.context_builder")


def build_context(results: list[RetrievalResult]) -> str:
    """
    Build a formatted context string from retrieval results.

    Format:
        --- SOURCE 1 ---
        File: project_plan.pdf
        Page: 8
        Similarity: 0.84

        [chunk content]

        --- SOURCE 2 ---
        ...

    Only includes metadata fields that are actually available.
    Never fabricates metadata.
    """
    if not results:
        return ""

    parts = []
    for i, result in enumerate(results, 1):
        header_lines = [f"--- SOURCE {i} ---"]

        # Only include metadata that exists
        if result.filename:
            header_lines.append(f"File: {result.filename}")
        if result.page is not None:
            header_lines.append(f"Page: {result.page}")
        if result.section:
            header_lines.append(f"Section: {result.section}")
        header_lines.append(f"Similarity: {result.score:.2f}")

        header = "\n".join(header_lines)
        parts.append(f"{header}\n\n{result.content}")

    context = "\n\n".join(parts)
    logger.debug(
        "Built context: %d sources, %d chars", len(results), len(context)
    )
    return context


def build_source_list(results: list[RetrievalResult]) -> list[dict]:
    """
    Build a structured source list for the API response.

    Returns a list of dicts with source metadata.
    Never fabricates page numbers or filenames.
    """
    sources = []
    seen = set()

    for result in results:
        # Deduplicate by filename + page
        key = (result.filename, result.page)
        if key in seen:
            continue
        seen.add(key)

        source = {
            "filename": result.filename,
            "score": result.score,
        }
        if result.page is not None:
            source["page"] = result.page
        if result.section:
            source["section"] = result.section
        if result.title:
            source["title"] = result.title
        source["chunk_id"] = result.chunk_id
        source["document_id"] = result.document_id

        sources.append(source)

    return sources


def format_sources_for_display(sources: list[dict]) -> str:
    """
    Format sources for user-facing display.

    Example:
        Sources:
        - project_plan.pdf — page 8
        - architecture.md
    """
    if not sources:
        return ""

    lines = ["Sources:"]
    for source in sources:
        entry = f"- {source.get('filename', 'unknown')}"
        if "page" in source:
            entry += f" — page {source['page']}"
        if "section" in source:
            entry += f" ({source['section']})"
        lines.append(entry)

    return "\n".join(lines)
