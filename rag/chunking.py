"""
LUX Document Chunking

Splits documents into overlapping chunks suitable for embedding.
Uses paragraph/section-aware splitting when possible, falling back
to character-based splitting with configurable size and overlap.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger("lux.rag.chunking")


@dataclass
class Chunk:
    """A single chunk of document content with metadata."""
    content: str = ""
    chunk_index: int = 0
    page: Optional[int] = None
    section: Optional[str] = None
    char_count: int = 0
    metadata: dict = field(default_factory=dict)


def chunk_document(
    text: str,
    chunk_size: int = 800,
    chunk_overlap: int = 120,
    pages: Optional[list[dict]] = None,
) -> list[Chunk]:
    """
    Split document text into overlapping chunks.

    Strategy:
    1. If pages/sections are provided, chunk within each page/section.
    2. Within each section, split at paragraph boundaries.
    3. If paragraphs are too large, split at sentence boundaries.
    4. Apply overlap between chunks for context continuity.

    Args:
        text: The full document text.
        chunk_size: Target maximum characters per chunk.
        chunk_overlap: Number of overlapping characters between chunks.
        pages: Optional list of page dicts with 'text', 'page', 'section'.

    Returns:
        List of Chunk objects with content and metadata.
    """
    if not text or not text.strip():
        logger.warning("Empty text provided for chunking")
        return []

    chunks: list[Chunk] = []

    if pages and len(pages) > 1:
        # Chunk within each page/section separately
        for page_info in pages:
            page_text = page_info.get("text", "")
            page_num = page_info.get("page")
            section = page_info.get("section")

            page_chunks = _chunk_text(
                page_text, chunk_size, chunk_overlap
            )
            for pc in page_chunks:
                pc.page = page_num
                pc.section = section
                chunks.append(pc)
    else:
        # Single-page or no page info: chunk the full text
        chunks = _chunk_text(text, chunk_size, chunk_overlap)

    # Assign sequential indices
    for i, chunk in enumerate(chunks):
        chunk.chunk_index = i
        chunk.char_count = len(chunk.content)

    logger.info(
        "Created %d chunks (size=%d, overlap=%d)",
        len(chunks), chunk_size, chunk_overlap,
    )
    return chunks


def _chunk_text(
    text: str, chunk_size: int, chunk_overlap: int
) -> list[Chunk]:
    """
    Core chunking: split text into overlapping segments.

    Prefers splitting at paragraph boundaries, then sentence
    boundaries, and finally at word boundaries.
    """
    if not text.strip():
        return []

    # Split into paragraphs (double newline or more)
    paragraphs = re.split(r"\n\s*\n", text)
    paragraphs = [p.strip() for p in paragraphs if p.strip()]

    chunks: list[Chunk] = []
    current_text = ""

    for para in paragraphs:
        # If adding this paragraph stays within the limit, accumulate
        candidate = (current_text + "\n\n" + para).strip() if current_text else para

        if len(candidate) <= chunk_size:
            current_text = candidate
        else:
            # Save what we have if it's non-empty
            if current_text.strip():
                chunks.append(Chunk(content=current_text.strip()))

            # If the paragraph itself is larger than chunk_size,
            # split it into smaller pieces
            if len(para) > chunk_size:
                sub_chunks = _split_large_text(para, chunk_size, chunk_overlap)
                chunks.extend(sub_chunks)
                current_text = ""
            else:
                # Start new chunk with overlap from previous
                if chunks and chunk_overlap > 0:
                    overlap_text = _get_overlap(
                        chunks[-1].content, chunk_overlap
                    )
                    current_text = overlap_text + "\n\n" + para
                    current_text = current_text.strip()
                else:
                    current_text = para

    # Don't forget the last accumulated text
    if current_text.strip():
        chunks.append(Chunk(content=current_text.strip()))

    return chunks


def _split_large_text(
    text: str, chunk_size: int, chunk_overlap: int
) -> list[Chunk]:
    """Split a large block of text at sentence boundaries."""
    # Try sentence splitting first
    sentences = re.split(r"(?<=[.!?])\s+", text)
    chunks: list[Chunk] = []
    current = ""

    for sentence in sentences:
        candidate = (current + " " + sentence).strip() if current else sentence

        if len(candidate) <= chunk_size:
            current = candidate
        else:
            if current.strip():
                chunks.append(Chunk(content=current.strip()))
            # If a single sentence is too long, force-split at word boundary
            if len(sentence) > chunk_size:
                word_chunks = _split_at_words(sentence, chunk_size, chunk_overlap)
                chunks.extend(word_chunks)
                current = ""
            else:
                if chunks and chunk_overlap > 0:
                    overlap = _get_overlap(chunks[-1].content, chunk_overlap)
                    current = overlap + " " + sentence
                else:
                    current = sentence

    if current.strip():
        chunks.append(Chunk(content=current.strip()))

    return chunks


def _split_at_words(
    text: str, chunk_size: int, chunk_overlap: int
) -> list[Chunk]:
    """Last resort: split at word boundaries."""
    words = text.split()
    chunks: list[Chunk] = []
    current_words: list[str] = []
    current_len = 0

    for word in words:
        if current_len + len(word) + 1 > chunk_size and current_words:
            chunks.append(Chunk(content=" ".join(current_words)))

            # Calculate overlap in words
            overlap_words: list[str] = []
            overlap_len = 0
            for w in reversed(current_words):
                if overlap_len + len(w) + 1 > chunk_overlap:
                    break
                overlap_words.insert(0, w)
                overlap_len += len(w) + 1

            current_words = overlap_words + [word]
            current_len = sum(len(w) + 1 for w in current_words)
        else:
            current_words.append(word)
            current_len += len(word) + 1

    if current_words:
        chunks.append(Chunk(content=" ".join(current_words)))

    return chunks


def _get_overlap(text: str, overlap_size: int) -> str:
    """Extract the last `overlap_size` characters of text."""
    if len(text) <= overlap_size:
        return text
    # Try to break at a word boundary
    overlap = text[-overlap_size:]
    space_idx = overlap.find(" ")
    if space_idx > 0 and space_idx < len(overlap) // 2:
        overlap = overlap[space_idx + 1:]
    return overlap
