# SQLite for Local AI Applications

## Why SQLite?

SQLite is a lightweight, serverless, self-contained relational database engine. It is the most widely deployed database in the world, found in virtually every smartphone, web browser, and operating system.

For local AI applications like knowledge assistants, SQLite offers several compelling advantages:

1. **Zero configuration**: No server to install, configure, or manage. The entire database is a single file.
2. **Serverless**: SQLite reads and writes directly to disk files. No separate server process is needed.
3. **Cross-platform**: Works identically on Windows, macOS, Linux, and embedded systems.
4. **Reliable**: ACID-compliant transactions ensure data integrity even during power failures.
5. **Small footprint**: The library is under 1 MB and has no external dependencies.
6. **Fast for local workloads**: For read-heavy workloads with moderate data sizes, SQLite often outperforms client-server databases due to eliminated network overhead.

## SQLite in RAG Systems

In a Retrieval-Augmented Generation (RAG) system, SQLite serves as the persistent storage layer for:

### Document Storage
- File metadata (name, path, hash, type, timestamps)
- Original or processed text content
- Source information for citation purposes

### Chunk Storage
- Individual text chunks with their content
- Chunk metadata (page number, section, position)
- Embedding vectors stored as BLOBs (Binary Large Objects)

### Conversation History
- User messages and assistant responses
- Session management for multi-turn conversations

### Application State
- Configuration settings
- Evaluation results and metrics

## Storing Embeddings in SQLite

Embedding vectors (lists of floating-point numbers) can be efficiently stored in SQLite using BLOB columns. The conversion process:

1. **Serialization**: Pack the float array into a binary format using Python's `struct` module.
   - Each float32 value takes 4 bytes.
   - A 384-dimensional embedding takes 1,536 bytes.
   - A 768-dimensional embedding takes 3,072 bytes.

2. **Storage**: Insert the binary data into a BLOB column.

3. **Retrieval**: Read the BLOB and unpack it back to a list of floats.

This approach is simple, efficient, and avoids the need for specialized vector database extensions.

## Performance Considerations

For small to medium knowledge bases (up to ~100,000 chunks), brute-force similarity search over SQLite-stored embeddings is practical:

- Reading 10,000 embeddings: ~50-200ms
- Computing cosine similarity for 10,000 pairs: ~10-50ms
- Total search time for a typical query: under 500ms

For larger collections, consider using vector index extensions like sqlite-vss or migrating to a dedicated vector store.

## SQLite Configuration for RAG

Recommended SQLite PRAGMA settings for RAG applications:

- `PRAGMA journal_mode=WAL`: Write-Ahead Logging for better concurrent read performance.
- `PRAGMA foreign_keys=ON`: Enforce referential integrity between documents and chunks.
- `PRAGMA synchronous=NORMAL`: Good balance between performance and durability.

## Schema Design Tips

1. Use `INTEGER PRIMARY KEY AUTOINCREMENT` for stable, sequential IDs.
2. Create indexes on frequently queried columns (e.g., `document_id` in chunks table).
3. Use `TEXT` columns with JSON for flexible metadata.
4. Use `UNIQUE` constraints on file hashes to prevent duplicate ingestion.
5. Enable `ON DELETE CASCADE` for foreign keys to automatically clean up chunks when documents are deleted.
