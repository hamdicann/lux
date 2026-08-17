"""
LUX Data Repositories

Data access layer for documents, chunks, conversations, and messages.
Handles embedding serialization (list[float] ↔ BLOB) using struct packing.
"""

from __future__ import annotations

import json
import logging
import struct
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional

from storage.database import DatabaseManager

logger = logging.getLogger("lux.storage.repositories")


# ── Data Classes ─────────────────────────────────────────────────

@dataclass
class Document:
    """Represents an ingested document."""
    id: Optional[int] = None
    filename: str = ""
    filepath: str = ""
    file_hash: str = ""
    file_type: str = ""
    title: str = ""
    source: str = ""
    num_chunks: int = 0
    created_at: str = ""
    updated_at: str = ""


@dataclass
class DocumentChunk:
    """A chunk of a document with its embedding vector."""
    id: Optional[int] = None
    document_id: int = 0
    chunk_index: int = 0
    content: str = ""
    embedding: list[float] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    page: Optional[int] = None
    section: Optional[str] = None
    char_count: int = 0
    created_at: str = ""


@dataclass
class Conversation:
    """A conversation session."""
    id: Optional[int] = None
    title: str = ""
    created_at: str = ""
    updated_at: str = ""


@dataclass
class Message:
    """A single message in a conversation."""
    id: Optional[int] = None
    conversation_id: int = 0
    role: str = ""      # 'user', 'assistant', 'system'
    content: str = ""
    sources: Optional[list[dict]] = None
    debug_info: Optional[dict] = None
    created_at: str = ""


# ── Embedding Serialization ─────────────────────────────────────

def embedding_to_blob(embedding: list[float]) -> bytes:
    """
    Serialize a list of floats to a compact binary BLOB.
    Uses 32-bit floats for space efficiency.
    """
    return struct.pack(f"{len(embedding)}f", *embedding)


def blob_to_embedding(blob: bytes) -> list[float]:
    """Deserialize a BLOB back to a list of floats."""
    count = len(blob) // 4  # 4 bytes per float32
    return list(struct.unpack(f"{count}f", blob))


# ── Document Repository ─────────────────────────────────────────

class DocumentRepository:
    """CRUD operations for the documents table."""

    def __init__(self, db: DatabaseManager) -> None:
        self.db = db

    def insert(self, doc: Document) -> int:
        """Insert a new document and return its ID."""
        now = datetime.utcnow().isoformat()
        cursor = self.db.execute(
            """INSERT INTO documents
               (filename, filepath, file_hash, file_type, title, source,
                num_chunks, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (doc.filename, doc.filepath, doc.file_hash, doc.file_type,
             doc.title, doc.source, doc.num_chunks, now, now),
            commit=True,
        )
        doc.id = cursor.lastrowid
        return doc.id

    def find_by_hash(self, file_hash: str) -> Optional[Document]:
        """Find a document by its content hash."""
        row = self.db.fetch_one(
            "SELECT * FROM documents WHERE file_hash = ?", (file_hash,)
        )
        return self._row_to_doc(row) if row else None

    def find_by_id(self, doc_id: int) -> Optional[Document]:
        """Find a document by ID."""
        row = self.db.fetch_one(
            "SELECT * FROM documents WHERE id = ?", (doc_id,)
        )
        return self._row_to_doc(row) if row else None

    def list_all(self) -> list[Document]:
        """Return all documents."""
        rows = self.db.fetch_all(
            "SELECT * FROM documents ORDER BY created_at DESC"
        )
        return [self._row_to_doc(r) for r in rows]

    def update_chunks_count(self, doc_id: int, count: int) -> None:
        """Update the chunk count for a document."""
        self.db.execute(
            """UPDATE documents
               SET num_chunks = ?, updated_at = datetime('now')
               WHERE id = ?""",
            (count, doc_id),
            commit=True,
        )

    def delete(self, doc_id: int) -> None:
        """Delete a document and its chunks (cascade)."""
        self.db.execute(
            "DELETE FROM documents WHERE id = ?", (doc_id,), commit=True
        )
        logger.info("Deleted document %d", doc_id)

    def delete_by_hash(self, file_hash: str) -> None:
        """Delete a document by its hash."""
        self.db.execute(
            "DELETE FROM documents WHERE file_hash = ?",
            (file_hash,), commit=True,
        )

    @staticmethod
    def _row_to_doc(row) -> Document:
        return Document(
            id=row["id"],
            filename=row["filename"],
            filepath=row["filepath"],
            file_hash=row["file_hash"],
            file_type=row["file_type"],
            title=row["title"],
            source=row["source"],
            num_chunks=row["num_chunks"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )


# ── Chunk Repository ────────────────────────────────────────────

class ChunkRepository:
    """CRUD operations for the document_chunks table."""

    def __init__(self, db: DatabaseManager) -> None:
        self.db = db

    def insert_batch(self, chunks: list[DocumentChunk]) -> None:
        """Insert multiple chunks at once."""
        params = [
            (
                c.document_id,
                c.chunk_index,
                c.content,
                embedding_to_blob(c.embedding),
                json.dumps(c.metadata) if c.metadata else None,
                c.page,
                c.section,
                c.char_count,
            )
            for c in chunks
        ]
        self.db.execute_many(
            """INSERT INTO document_chunks
               (document_id, chunk_index, content, embedding, metadata,
                page, section, char_count)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            params,
        )
        logger.info("Inserted %d chunks", len(chunks))

    def get_all_with_embeddings(self) -> list[dict]:
        """
        Load all chunks with their embeddings for similarity search.
        Returns dicts with 'id', 'document_id', 'chunk_index', 'content',
        'embedding', 'metadata', 'page', 'section'.
        """
        rows = self.db.fetch_all(
            """SELECT dc.*, d.filename, d.filepath, d.title
               FROM document_chunks dc
               JOIN documents d ON dc.document_id = d.id
               ORDER BY dc.document_id, dc.chunk_index"""
        )
        results = []
        for row in rows:
            meta = json.loads(row["metadata"]) if row["metadata"] else {}
            results.append({
                "id": row["id"],
                "document_id": row["document_id"],
                "chunk_index": row["chunk_index"],
                "content": row["content"],
                "embedding": blob_to_embedding(row["embedding"]),
                "metadata": meta,
                "page": row["page"],
                "section": row["section"],
                "filename": row["filename"],
                "filepath": row["filepath"],
                "title": row["title"],
            })
        return results

    def get_by_document_id(self, doc_id: int) -> list[DocumentChunk]:
        """Get all chunks for a specific document."""
        rows = self.db.fetch_all(
            """SELECT * FROM document_chunks
               WHERE document_id = ?
               ORDER BY chunk_index""",
            (doc_id,),
        )
        return [self._row_to_chunk(r) for r in rows]

    def delete_by_document_id(self, doc_id: int) -> None:
        """Delete all chunks for a document."""
        self.db.execute(
            "DELETE FROM document_chunks WHERE document_id = ?",
            (doc_id,), commit=True,
        )

    def count(self) -> int:
        """Return total number of chunks."""
        row = self.db.fetch_one(
            "SELECT COUNT(*) as count FROM document_chunks"
        )
        return row["count"] if row else 0

    @staticmethod
    def _row_to_chunk(row) -> DocumentChunk:
        return DocumentChunk(
            id=row["id"],
            document_id=row["document_id"],
            chunk_index=row["chunk_index"],
            content=row["content"],
            embedding=blob_to_embedding(row["embedding"]),
            metadata=json.loads(row["metadata"]) if row["metadata"] else {},
            page=row["page"],
            section=row["section"],
            char_count=row["char_count"] if "char_count" in row.keys() else 0,
            created_at=row["created_at"],
        )


# ── Conversation Repository ─────────────────────────────────────

class ConversationRepository:
    """CRUD operations for conversations and messages."""

    def __init__(self, db: DatabaseManager) -> None:
        self.db = db

    def create_conversation(self, title: str = "") -> int:
        """Create a new conversation and return its ID."""
        cursor = self.db.execute(
            "INSERT INTO conversations (title) VALUES (?)",
            (title or "New Conversation",),
            commit=True,
        )
        return cursor.lastrowid

    def get_conversation(self, conv_id: int) -> Optional[Conversation]:
        """Get a conversation by ID."""
        row = self.db.fetch_one(
            "SELECT * FROM conversations WHERE id = ?", (conv_id,)
        )
        if not row:
            return None
        return Conversation(
            id=row["id"], title=row["title"],
            created_at=row["created_at"], updated_at=row["updated_at"],
        )

    def list_conversations(self) -> list[Conversation]:
        """List all conversations, newest first."""
        rows = self.db.fetch_all(
            "SELECT * FROM conversations ORDER BY updated_at DESC"
        )
        return [
            Conversation(
                id=r["id"], title=r["title"],
                created_at=r["created_at"], updated_at=r["updated_at"],
            )
            for r in rows
        ]

    def add_message(
        self,
        conversation_id: int,
        role: str,
        content: str,
        sources: Optional[list[dict]] = None,
        debug_info: Optional[dict] = None,
    ) -> int:
        """Add a message to a conversation."""
        cursor = self.db.execute(
            """INSERT INTO messages
               (conversation_id, role, content, sources, debug_info)
               VALUES (?, ?, ?, ?, ?)""",
            (
                conversation_id,
                role,
                content,
                json.dumps(sources) if sources else None,
                json.dumps(debug_info) if debug_info else None,
            ),
            commit=True,
        )
        # Update conversation timestamp
        self.db.execute(
            "UPDATE conversations SET updated_at = datetime('now') WHERE id = ?",
            (conversation_id,),
            commit=True,
        )
        return cursor.lastrowid

    def get_messages(
        self, conversation_id: int, limit: int = 20
    ) -> list[Message]:
        """Get recent messages for a conversation."""
        rows = self.db.fetch_all(
            """SELECT * FROM messages
               WHERE conversation_id = ?
               ORDER BY created_at DESC, id DESC
               LIMIT ?""",
            (conversation_id, limit),
        )
        # Reverse to chronological order
        rows = list(reversed(rows))
        return [
            Message(
                id=r["id"],
                conversation_id=r["conversation_id"],
                role=r["role"],
                content=r["content"],
                sources=json.loads(r["sources"]) if r["sources"] else None,
                debug_info=json.loads(r["debug_info"]) if r["debug_info"] else None,
                created_at=r["created_at"],
            )
            for r in rows
        ]

    def delete_conversation(self, conv_id: int) -> None:
        """Delete a conversation and all its messages (cascade)."""
        self.db.execute(
            "DELETE FROM conversations WHERE id = ?",
            (conv_id,), commit=True,
        )
