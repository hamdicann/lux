"""
LUX Document Ingestion Pipeline

Orchestrates the full pipeline: scan directory → detect file type →
load → normalize → chunk → embed → persist in SQLite.
SHA-256 content hashing prevents duplicate ingestion.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from app.config import LuxConfig
from rag.loaders import load_document, get_supported_extensions, compute_file_hash
from rag.parser import normalize_text
from rag.chunking import chunk_document
from storage.database import DatabaseManager
from storage.repositories import (
    DocumentRepository, ChunkRepository,
    Document, DocumentChunk,
)

logger = logging.getLogger("lux.rag.ingestion")


@dataclass
class IngestionResult:
    """Summary of an ingestion run."""
    total_files: int = 0
    ingested: int = 0
    skipped: int = 0
    failed: int = 0
    total_chunks: int = 0
    duration: float = 0.0
    errors: list[str] = field(default_factory=list)
    details: list[dict] = field(default_factory=list)


class IngestionPipeline:
    """
    Complete document ingestion pipeline.

    Scans a directory for supported files, extracts text,
    chunks it, generates embeddings, and stores everything
    in the local SQLite database.
    """

    def __init__(
        self,
        config: LuxConfig,
        db: DatabaseManager,
        embedding_service,  # llm.embeddings.EmbeddingService
    ) -> None:
        self.config = config
        self.db = db
        self.embedding_service = embedding_service
        self.doc_repo = DocumentRepository(db)
        self.chunk_repo = ChunkRepository(db)

    def ingest_directory(
        self,
        directory: Optional[Path] = None,
        recursive: bool = True,
    ) -> IngestionResult:
        """
        Scan a directory and ingest all supported files.

        Args:
            directory: Path to scan. Defaults to config.document_path.
            recursive: Whether to scan subdirectories.

        Returns:
            IngestionResult with summary statistics.
        """
        directory = directory or self.config.document_path
        directory = Path(directory)

        if not directory.exists():
            logger.warning("Document directory not found: %s", directory)
            return IngestionResult(errors=[f"Directory not found: {directory}"])

        start = time.time()
        result = IngestionResult()

        # Find all supported files
        supported = set(get_supported_extensions())
        files = []
        if recursive:
            for ext in supported:
                files.extend(directory.rglob(f"*{ext}"))
        else:
            for ext in supported:
                files.extend(directory.glob(f"*{ext}"))

        result.total_files = len(files)
        logger.info(
            "Found %d supported files in %s", len(files), directory
        )

        for filepath in sorted(files):
            try:
                file_result = self.ingest_file(filepath)
                if file_result == "ingested":
                    result.ingested += 1
                elif file_result == "skipped":
                    result.skipped += 1
            except Exception as e:
                result.failed += 1
                error_msg = f"{filepath.name}: {e}"
                result.errors.append(error_msg)
                logger.error("Failed to ingest '%s': %s", filepath.name, e)

        result.total_chunks = self.chunk_repo.count()
        result.duration = round(time.time() - start, 2)

        logger.info(
            "Ingestion complete: %d ingested, %d skipped, %d failed in %.2fs",
            result.ingested, result.skipped, result.failed, result.duration,
        )
        return result

    def ingest_file(self, filepath: Path) -> str:
        """
        Ingest a single file.

        Returns:
            'ingested' if the file was processed.
            'skipped' if the file was already in the database.
        """
        filepath = Path(filepath)
        logger.info("Processing: %s", filepath.name)

        # Step 1: Check hash for deduplication
        file_hash = compute_file_hash(filepath)
        existing = self.doc_repo.find_by_hash(file_hash)
        if existing:
            logger.info(
                "Skipped '%s' — already ingested (hash match)",
                filepath.name,
            )
            return "skipped"

        # Step 2: Load document
        loaded = load_document(filepath)

        # Step 3: Normalize text
        normalized_text = normalize_text(loaded.text)

        if not normalized_text.strip():
            logger.warning("Skipped '%s' — empty after normalization", filepath.name)
            return "skipped"

        # Step 4: Chunk the document
        chunks = chunk_document(
            text=normalized_text,
            chunk_size=self.config.chunk_size,
            chunk_overlap=self.config.chunk_overlap,
            pages=loaded.pages if loaded.pages else None,
        )

        if not chunks:
            logger.warning("Skipped '%s' — no chunks produced", filepath.name)
            return "skipped"

        # Step 5: Generate embeddings for all chunks
        chunk_texts = [c.content for c in chunks]
        logger.info(
            "Generating embeddings for %d chunks from '%s'",
            len(chunks), filepath.name,
        )
        embeddings = self.embedding_service.embed_batch(chunk_texts)

        # Step 6: Store document
        doc = Document(
            filename=loaded.filename,
            filepath=str(filepath),
            file_hash=file_hash,
            file_type=loaded.file_type,
            title=loaded.title,
            source=str(filepath),
            num_chunks=len(chunks),
        )
        doc_id = self.doc_repo.insert(doc)

        # Step 7: Store chunks with embeddings
        db_chunks = []
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            db_chunks.append(DocumentChunk(
                document_id=doc_id,
                chunk_index=chunk.chunk_index,
                content=chunk.content,
                embedding=embedding,
                metadata=chunk.metadata,
                page=chunk.page,
                section=chunk.section,
                char_count=chunk.char_count,
            ))

        self.chunk_repo.insert_batch(db_chunks)

        logger.info(
            "Ingested '%s': %d chunks, hash=%s",
            filepath.name, len(chunks), file_hash[:12],
        )
        return "ingested"

    def reingest_file(self, filepath: Path) -> str:
        """
        Force re-ingestion of a file (removes old data first).
        """
        filepath = Path(filepath)
        file_hash = compute_file_hash(filepath)

        # Remove existing document + chunks
        existing = self.doc_repo.find_by_hash(file_hash)
        if existing:
            self.doc_repo.delete(existing.id)

        return self.ingest_file(filepath)

    def clear_all(self) -> None:
        """Remove all documents and chunks from the database."""
        self.db.execute("DELETE FROM document_chunks", commit=True)
        self.db.execute("DELETE FROM documents", commit=True)
        logger.info("Cleared all documents and chunks")
