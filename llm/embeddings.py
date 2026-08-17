"""
LUX Embedding Service

Generates text embeddings using the local Foundry Local embedding model
via the OpenAI-compatible API. Supports single text and batch embedding.
"""

from __future__ import annotations

import logging
import time
from typing import Optional

logger = logging.getLogger("lux.llm.embeddings")


class EmbeddingService:
    """
    Generates embeddings locally through Foundry Local.

    Uses the OpenAI-compatible embeddings.create() API
    pointed at the local Foundry endpoint.
    """

    def __init__(self, foundry_client, config) -> None:
        self._foundry = foundry_client
        self._config = config
        self._dimension: Optional[int] = None

    def embed_text(self, text: str) -> list[float]:
        """
        Generate an embedding vector for a single text string.

        Args:
            text: The text to embed.

        Returns:
            A list of floats representing the embedding vector.
        """
        if not text or not text.strip():
            raise ValueError("Cannot embed empty text")

        client = self._foundry.get_openai_client()
        start = time.time()

        response = client.embeddings.create(
            input=text,
            model=self._config.embedding_model,
        )

        embedding = response.data[0].embedding
        elapsed = time.time() - start

        # Cache the embedding dimension on first call
        if self._dimension is None:
            self._dimension = len(embedding)
            logger.info(
                "Embedding dimension: %d (model: %s)",
                self._dimension, self._config.embedding_model,
            )

        logger.debug(
            "Embedded text (%d chars) in %.3fs",
            len(text), elapsed,
        )
        return embedding

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """
        Generate embeddings for multiple texts.

        Sends texts in a single API call for efficiency.

        Args:
            texts: List of strings to embed.

        Returns:
            List of embedding vectors, one per input text.
        """
        if not texts:
            return []

        # Filter out empty strings but track original positions
        valid_texts = []
        valid_indices = []
        for i, text in enumerate(texts):
            if text and text.strip():
                valid_texts.append(text)
                valid_indices.append(i)

        if not valid_texts:
            return [[] for _ in texts]

        client = self._foundry.get_openai_client()
        start = time.time()

        response = client.embeddings.create(
            input=valid_texts,
            model=self._config.embedding_model,
        )

        elapsed = time.time() - start
        logger.info(
            "Batch embedded %d texts in %.3fs (%.1f texts/sec)",
            len(valid_texts), elapsed,
            len(valid_texts) / elapsed if elapsed > 0 else 0,
        )

        # Reconstruct results preserving original ordering
        # The API returns results sorted by index
        sorted_data = sorted(response.data, key=lambda d: d.index)
        embeddings_map = {
            valid_indices[i]: sorted_data[i].embedding
            for i in range(len(valid_texts))
        }

        results = []
        zero_vec = [0.0] * (self._dimension or 1)
        for i in range(len(texts)):
            results.append(embeddings_map.get(i, zero_vec))

        return results

    @property
    def dimension(self) -> Optional[int]:
        """Return the embedding dimension (available after first call)."""
        return self._dimension
