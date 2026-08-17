"""
LUX Unit Tests — Retrieval

Tests for cosine similarity and retrieval engine components.
"""

import pytest
import math
from rag.retrieval import cosine_similarity


class TestCosineSimilarity:
    """Tests for cosine_similarity."""

    def test_identical_vectors(self):
        """Identical vectors should have similarity 1.0."""
        vec = [1.0, 2.0, 3.0]
        assert abs(cosine_similarity(vec, vec) - 1.0) < 1e-6

    def test_orthogonal_vectors(self):
        """Orthogonal vectors should have similarity 0.0."""
        vec_a = [1.0, 0.0, 0.0]
        vec_b = [0.0, 1.0, 0.0]
        assert abs(cosine_similarity(vec_a, vec_b)) < 1e-6

    def test_opposite_vectors(self):
        """Opposite vectors should have similarity -1.0."""
        vec_a = [1.0, 0.0]
        vec_b = [-1.0, 0.0]
        assert abs(cosine_similarity(vec_a, vec_b) - (-1.0)) < 1e-6

    def test_zero_vector(self):
        """Zero vectors should return 0.0 safely."""
        vec_a = [0.0, 0.0, 0.0]
        vec_b = [1.0, 2.0, 3.0]
        assert cosine_similarity(vec_a, vec_b) == 0.0

    def test_different_lengths(self):
        """Vectors of different lengths should return 0.0."""
        vec_a = [1.0, 2.0]
        vec_b = [1.0, 2.0, 3.0]
        assert cosine_similarity(vec_a, vec_b) == 0.0

    def test_similar_vectors(self):
        """Similar vectors should have high similarity."""
        vec_a = [1.0, 1.0, 1.0]
        vec_b = [1.1, 0.9, 1.0]
        sim = cosine_similarity(vec_a, vec_b)
        assert sim > 0.99


class TestEmbeddingSerialization:
    """Tests for embedding BLOB conversion."""

    def test_roundtrip(self):
        """Embedding should survive serialize → deserialize roundtrip."""
        from storage.repositories import embedding_to_blob, blob_to_embedding

        original = [0.1, 0.2, -0.3, 0.0, 1.0]
        blob = embedding_to_blob(original)
        restored = blob_to_embedding(blob)

        assert len(restored) == len(original)
        for a, b in zip(original, restored):
            assert abs(a - b) < 1e-6

    def test_blob_size(self):
        """BLOB should be 4 bytes per float."""
        from storage.repositories import embedding_to_blob

        vec = [0.0] * 384
        blob = embedding_to_blob(vec)
        assert len(blob) == 384 * 4
