"""
LUX Vector Retrieval

Implements cosine similarity search over stored embeddings.
Brute-force comparison suitable for small-to-medium document
collections. Interface designed for future swap to FAISS.
"""

from __future__ import annotations

import logging
import math
import time
from dataclasses import dataclass, field
from typing import Optional

from storage.database import DatabaseManager
from storage.repositories import ChunkRepository

logger = logging.getLogger("lux.rag.retrieval")


@dataclass
class RetrievalResult:
    """A single retrieved chunk with its similarity score."""
    content: str = ""
    score: float = 0.0
    chunk_id: int = 0
    document_id: int = 0
    chunk_index: int = 0
    filename: str = ""
    filepath: str = ""
    title: str = ""
    page: Optional[int] = None
    section: Optional[str] = None
    metadata: dict = field(default_factory=dict)


def cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """
    Compute cosine similarity between two vectors.

    Returns a value between -1 and 1, where 1 means identical direction.
    Handles zero vectors safely by returning 0.0.
    """
    if len(vec_a) != len(vec_b):
        return 0.0

    dot_product = 0.0
    norm_a = 0.0
    norm_b = 0.0

    for a, b in zip(vec_a, vec_b):
        dot_product += a * b
        norm_a += a * a
        norm_b += b * b

    # Guard against zero-magnitude vectors
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0

    return dot_product / (math.sqrt(norm_a) * math.sqrt(norm_b))


class RetrievalEngine:
    """
    Performs brute-force vector similarity search against all
    stored chunk embeddings in SQLite.

    This is the simple approach recommended by the specification
    for small datasets. The interface is designed so it could be
    swapped for FAISS or another vector index later.
    """

    def __init__(self, db: DatabaseManager) -> None:
        self.db = db
        self.chunk_repo = ChunkRepository(db)

    def search(
        self,
        query_embedding: list[float],
        top_k: int = 3,
        min_similarity: float = 0.35,
    ) -> list[RetrievalResult]:
        """
        Search for the most similar chunks to a query embedding.

        Args:
            query_embedding: The embedding vector for the user's query.
            top_k: Maximum number of results to return.
            min_similarity: Minimum cosine similarity threshold.

        Returns:
            List of RetrievalResult sorted by similarity (highest first).
        """
        start = time.time()

        # Load all chunks with their embeddings
        all_chunks = self.chunk_repo.get_all_with_embeddings()

        if not all_chunks:
            logger.warning("No chunks in database — nothing to search")
            return []

        # Compute similarity against every chunk
        scored: list[tuple[float, dict]] = []
        for chunk in all_chunks:
            score = cosine_similarity(query_embedding, chunk["embedding"])
            if score >= min_similarity:
                scored.append((score, chunk))

        # Sort by similarity (descending)
        scored.sort(key=lambda x: x[0], reverse=True)

        # Take top-K
        top_results = scored[:top_k]

        elapsed = time.time() - start
        logger.info(
            "Retrieval: searched %d chunks in %.3fs, "
            "found %d above threshold (%.2f), returning top-%d",
            len(all_chunks), elapsed, len(scored), min_similarity, top_k,
        )

        results = []
        for score, chunk in top_results:
            results.append(RetrievalResult(
                content=chunk["content"],
                score=round(score, 4),
                chunk_id=chunk["id"],
                document_id=chunk["document_id"],
                chunk_index=chunk["chunk_index"],
                filename=chunk["filename"],
                filepath=chunk["filepath"],
                title=chunk["title"],
                page=chunk["page"],
                section=chunk["section"],
                metadata=chunk["metadata"],
            ))

        return results
