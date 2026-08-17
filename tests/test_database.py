"""
LUX Unit Tests — Database

Tests for the SQLite database manager and repositories.
Uses a temporary in-memory or tempfile database.
"""

import pytest
import tempfile
from pathlib import Path

from storage.database import DatabaseManager
from storage.repositories import (
    DocumentRepository, ChunkRepository, ConversationRepository,
    Document, DocumentChunk,
    embedding_to_blob, blob_to_embedding,
)


@pytest.fixture
def db():
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)

    manager = DatabaseManager(db_path)
    manager.initialize()
    yield manager
    manager.close()
    try:
        db_path.unlink()
    except Exception:
        pass


class TestDatabaseManager:
    def test_initialize(self, db):
        """Database should initialize without errors."""
        stats = db.get_stats()
        assert stats["documents"] == 0
        assert stats["chunks"] == 0

    def test_execute(self, db):
        """Should execute SQL and return results."""
        result = db.fetch_one("SELECT 1 + 1 as sum")
        assert result["sum"] == 2


class TestDocumentRepository:
    def test_insert_and_find(self, db):
        repo = DocumentRepository(db)
        doc = Document(
            filename="test.txt",
            filepath="/test/test.txt",
            file_hash="abc123",
            file_type="txt",
            title="Test",
            source="/test/test.txt",
        )
        doc_id = repo.insert(doc)
        assert doc_id > 0

        found = repo.find_by_hash("abc123")
        assert found is not None
        assert found.filename == "test.txt"

    def test_duplicate_hash_fails(self, db):
        repo = DocumentRepository(db)
        doc = Document(filename="a.txt", file_hash="same_hash", file_type="txt")
        repo.insert(doc)

        doc2 = Document(filename="b.txt", file_hash="same_hash", file_type="txt")
        with pytest.raises(Exception):
            repo.insert(doc2)

    def test_delete(self, db):
        repo = DocumentRepository(db)
        doc = Document(filename="del.txt", file_hash="del_hash", file_type="txt")
        doc_id = repo.insert(doc)
        repo.delete(doc_id)
        assert repo.find_by_id(doc_id) is None

    def test_list_all(self, db):
        repo = DocumentRepository(db)
        repo.insert(Document(filename="a.txt", file_hash="h1", file_type="txt"))
        repo.insert(Document(filename="b.txt", file_hash="h2", file_type="txt"))
        docs = repo.list_all()
        assert len(docs) == 2


class TestChunkRepository:
    def test_insert_and_count(self, db):
        doc_repo = DocumentRepository(db)
        doc_id = doc_repo.insert(Document(filename="t.txt", file_hash="hash1", file_type="txt"))

        chunk_repo = ChunkRepository(db)
        chunks = [
            DocumentChunk(
                document_id=doc_id,
                chunk_index=0,
                content="Hello world",
                embedding=[0.1, 0.2, 0.3],
                char_count=11,
            ),
            DocumentChunk(
                document_id=doc_id,
                chunk_index=1,
                content="Second chunk",
                embedding=[0.4, 0.5, 0.6],
                char_count=12,
            ),
        ]
        chunk_repo.insert_batch(chunks)
        assert chunk_repo.count() == 2

    def test_get_with_embeddings(self, db):
        doc_repo = DocumentRepository(db)
        doc_id = doc_repo.insert(Document(filename="e.txt", file_hash="ehash", file_type="txt"))

        chunk_repo = ChunkRepository(db)
        original_embedding = [0.1, 0.2, 0.3, 0.4, 0.5]
        chunk_repo.insert_batch([
            DocumentChunk(
                document_id=doc_id,
                chunk_index=0,
                content="Test content",
                embedding=original_embedding,
            )
        ])

        results = chunk_repo.get_all_with_embeddings()
        assert len(results) == 1
        restored = results[0]["embedding"]
        assert len(restored) == len(original_embedding)
        for a, b in zip(original_embedding, restored):
            assert abs(a - b) < 1e-5


class TestConversationRepository:
    def test_create_and_list(self, db):
        repo = ConversationRepository(db)
        conv_id = repo.create_conversation("Test Chat")
        assert conv_id > 0

        convs = repo.list_conversations()
        assert len(convs) == 1
        assert convs[0].title == "Test Chat"

    def test_add_and_get_messages(self, db):
        repo = ConversationRepository(db)
        conv_id = repo.create_conversation("Msg Test")

        repo.add_message(conv_id, "user", "Hello")
        repo.add_message(conv_id, "assistant", "Hi there!")

        messages = repo.get_messages(conv_id)
        assert len(messages) == 2
        assert messages[0].role == "user"
        assert messages[1].role == "assistant"
