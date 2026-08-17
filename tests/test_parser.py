"""
LUX Unit Tests — Parser

Tests for the text normalization module.
"""

import pytest
from rag.parser import normalize_text, clean_for_embedding


class TestNormalize:
    """Tests for normalize_text."""

    def test_empty(self):
        assert normalize_text("") == ""
        assert normalize_text(None) == ""

    def test_strips_trailing_whitespace(self):
        result = normalize_text("hello   \nworld  ")
        lines = result.split("\n")
        for line in lines:
            assert line == line.rstrip()

    def test_collapses_blank_lines(self):
        text = "hello\n\n\n\n\nworld"
        result = normalize_text(text)
        assert "\n\n\n" not in result

    def test_preserves_paragraph_breaks(self):
        text = "para 1\n\npara 2"
        result = normalize_text(text)
        assert "\n\n" in result

    def test_handles_non_breaking_spaces(self):
        text = "hello\u00a0world"
        result = normalize_text(text)
        assert "\u00a0" not in result
        assert "hello world" in result

    def test_normalizes_windows_newlines(self):
        text = "line1\r\nline2\r\nline3"
        result = normalize_text(text)
        assert "\r" not in result
        assert "line1" in result and "line3" in result


class TestCleanForEmbedding:
    """Tests for clean_for_embedding."""

    def test_removes_bold_markers(self):
        assert clean_for_embedding("**bold**") == "bold"

    def test_removes_italic_markers(self):
        assert clean_for_embedding("*italic*") == "italic"

    def test_removes_inline_code(self):
        assert clean_for_embedding("`code`") == "code"

    def test_preserves_content(self):
        text = "This is important text."
        assert clean_for_embedding(text) == text

    def test_empty(self):
        assert clean_for_embedding("") == ""
