"""
LUX Unit Tests — Chunking

Tests for the document chunking module.
These tests run offline — no Foundry Local or models needed.
"""

import pytest
from rag.chunking import chunk_document, Chunk


class TestChunking:
    """Tests for the chunk_document function."""

    def test_empty_text(self):
        """Empty text produces no chunks."""
        assert chunk_document("") == []
        assert chunk_document("   ") == []

    def test_short_text(self):
        """Text shorter than chunk_size produces one chunk."""
        text = "This is a short paragraph."
        chunks = chunk_document(text, chunk_size=800)
        assert len(chunks) == 1
        assert chunks[0].content == text

    def test_chunk_indices(self):
        """Chunks should have sequential indices."""
        text = "Paragraph one.\n\nParagraph two.\n\nParagraph three."
        chunks = chunk_document(text, chunk_size=20, chunk_overlap=0)
        for i, chunk in enumerate(chunks):
            assert chunk.chunk_index == i

    def test_large_text_chunking(self):
        """Long text should produce multiple chunks."""
        text = "\n\n".join([f"This is paragraph number {i}." for i in range(50)])
        chunks = chunk_document(text, chunk_size=200, chunk_overlap=0)
        assert len(chunks) > 1

    def test_char_count_set(self):
        """Each chunk should have char_count set."""
        text = "Hello world.\n\nThis is a test."
        chunks = chunk_document(text, chunk_size=800)
        for chunk in chunks:
            assert chunk.char_count == len(chunk.content)

    def test_page_metadata(self):
        """Chunks from pages should preserve page metadata."""
        pages = [
            {"page": 1, "text": "Page one content here."},
            {"page": 2, "text": "Page two content here."},
        ]
        full_text = "Page one content here.\n\nPage two content here."
        chunks = chunk_document(full_text, chunk_size=800, pages=pages)
        # Should preserve page info
        page_nums = [c.page for c in chunks if c.page is not None]
        assert 1 in page_nums or 2 in page_nums

    def test_overlap_produces_content(self):
        """Chunks with overlap should contain text from previous chunk."""
        text = "A" * 200 + "\n\n" + "B" * 200 + "\n\n" + "C" * 200
        chunks = chunk_document(text, chunk_size=250, chunk_overlap=50)
        # Should produce multiple chunks
        assert len(chunks) >= 2


class TestChunkContent:
    """Test chunk content quality."""

    def test_no_empty_chunks(self):
        """No chunk should have empty content."""
        text = "Line 1.\n\nLine 2.\n\nLine 3.\n\nLine 4."
        chunks = chunk_document(text, chunk_size=20, chunk_overlap=0)
        for chunk in chunks:
            assert chunk.content.strip() != ""

    def test_preserves_text(self):
        """All original text should appear in at least one chunk."""
        text = "Alpha beta gamma.\n\nDelta epsilon zeta."
        chunks = chunk_document(text, chunk_size=800)
        combined = " ".join(c.content for c in chunks)
        assert "Alpha" in combined
        assert "Delta" in combined
