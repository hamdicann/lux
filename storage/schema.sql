-- ============================================================
-- LUX Database Schema
-- Local SQLite database for documents, chunks, embeddings,
-- conversations, and evaluation data.
-- ============================================================

-- Schema version tracking
CREATE TABLE IF NOT EXISTS schema_version (
    version     INTEGER PRIMARY KEY,
    applied_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

-- ── Documents ───────────────────────────────────────────────
-- Stores metadata about each ingested file.
CREATE TABLE IF NOT EXISTS documents (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    filename    TEXT NOT NULL,
    filepath    TEXT,
    file_hash   TEXT UNIQUE,
    file_type   TEXT,
    title       TEXT,
    source      TEXT,
    num_chunks  INTEGER DEFAULT 0,
    created_at  TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

-- ── Document Chunks ─────────────────────────────────────────
-- Each chunk of a document with its embedding vector stored as BLOB.
CREATE TABLE IF NOT EXISTS document_chunks (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id   INTEGER NOT NULL,
    chunk_index   INTEGER NOT NULL,
    content       TEXT NOT NULL,
    embedding     BLOB NOT NULL,
    metadata      TEXT,           -- JSON: extra info
    page          INTEGER,
    section       TEXT,
    char_count    INTEGER,
    created_at    TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_chunks_document_id ON document_chunks(document_id);

-- ── Conversations ───────────────────────────────────────────
CREATE TABLE IF NOT EXISTS conversations (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    title       TEXT,
    created_at  TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

-- ── Messages ────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS messages (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id   INTEGER NOT NULL,
    role              TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content           TEXT NOT NULL,
    sources           TEXT,        -- JSON: source metadata for RAG answers
    debug_info        TEXT,        -- JSON: debug data when LUX_DEBUG=true
    created_at        TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_messages_conversation ON messages(conversation_id);

-- ── Evaluation Cases ────────────────────────────────────────
CREATE TABLE IF NOT EXISTS evaluation_cases (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    question        TEXT NOT NULL,
    expected_answer TEXT,
    source_file     TEXT,
    category        TEXT CHECK (category IN (
                        'ANSWERABLE', 'PARTIALLY_ANSWERABLE',
                        'UNANSWERABLE', 'EDGE_CASE'
                    )),
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

-- ── Settings ────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS settings (
    key         TEXT PRIMARY KEY,
    value       TEXT NOT NULL,
    updated_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Record initial schema version
INSERT OR IGNORE INTO schema_version (version) VALUES (1);
