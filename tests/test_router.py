"""
LUX Unit Tests — Query Router

Tests for the query classification module.
"""

import pytest
from core.router import classify_query, QueryType


class TestQueryRouter:
    """Tests for classify_query."""

    def test_greeting_is_chat(self):
        assert classify_query("hello") == QueryType.CHAT
        assert classify_query("hi") == QueryType.CHAT
        assert classify_query("thanks") == QueryType.CHAT

    def test_question_is_rag(self):
        assert classify_query("What is RAG?") == QueryType.RAG_QUERY
        assert classify_query("How does embedding work?") == QueryType.RAG_QUERY

    def test_document_keywords_trigger_rag(self):
        assert classify_query("search for information about embeddings") == QueryType.RAG_QUERY
        assert classify_query("what does the document say about RAG?") == QueryType.RAG_QUERY

    def test_empty_is_chat(self):
        assert classify_query("") == QueryType.CHAT
        assert classify_query("   ") == QueryType.CHAT

    def test_short_non_question_is_chat(self):
        assert classify_query("ok") == QueryType.CHAT

    def test_question_mark_triggers_rag(self):
        assert classify_query("embeddings?") == QueryType.RAG_QUERY

    def test_longer_statements_are_rag(self):
        """Longer informational queries should default to RAG."""
        result = classify_query("Explain the architecture of the LUX system")
        assert result == QueryType.RAG_QUERY
