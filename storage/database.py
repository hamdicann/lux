"""
LUX Database Manager

Thread-safe SQLite connection management with schema initialization.
All database state is local — no external database required.
"""

from __future__ import annotations

import logging
import sqlite3
import threading
from pathlib import Path
from typing import Optional

logger = logging.getLogger("lux.storage.database")

_SCHEMA_FILE = Path(__file__).parent / "schema.sql"


class DatabaseManager:
    """
    Manages SQLite connections and schema lifecycle.

    Uses thread-local storage so each thread gets its own connection,
    which is required for SQLite's default threading mode.
    """

    def __init__(self, db_path: Path) -> None:
        self.db_path = Path(db_path)
        self._local = threading.local()
        self._initialized = False

    # ── Connection Management ────────────────────────────────

    def _get_connection(self) -> sqlite3.Connection:
        """Return a thread-local connection, creating one if needed."""
        conn = getattr(self._local, "connection", None)
        if conn is None:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            conn = sqlite3.connect(str(self.db_path))
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA foreign_keys=ON")
            self._local.connection = conn
        return conn

    @property
    def conn(self) -> sqlite3.Connection:
        """Public accessor for the current thread's connection."""
        return self._get_connection()

    def initialize(self) -> None:
        """
        Create tables from schema.sql if they don't exist.
        Safe to call multiple times — uses IF NOT EXISTS.
        """
        if self._initialized:
            return

        conn = self._get_connection()
        schema_sql = _SCHEMA_FILE.read_text(encoding="utf-8")
        conn.executescript(schema_sql)
        conn.commit()
        self._initialized = True
        logger.info("Database initialized at %s", self.db_path)

    def close(self) -> None:
        """Close the current thread's connection."""
        conn = getattr(self._local, "connection", None)
        if conn is not None:
            conn.close()
            self._local.connection = None

    # ── Query Helpers ────────────────────────────────────────

    def execute(
        self, sql: str, params: tuple = (), commit: bool = False
    ) -> sqlite3.Cursor:
        """Execute a SQL statement and optionally commit."""
        conn = self._get_connection()
        cursor = conn.execute(sql, params)
        if commit:
            conn.commit()
        return cursor

    def execute_many(
        self, sql: str, param_list: list[tuple], commit: bool = True
    ) -> None:
        """Execute a SQL statement for each set of parameters."""
        conn = self._get_connection()
        conn.executemany(sql, param_list)
        if commit:
            conn.commit()

    def fetch_one(
        self, sql: str, params: tuple = ()
    ) -> Optional[sqlite3.Row]:
        """Execute and return a single row or None."""
        cursor = self.execute(sql, params)
        return cursor.fetchone()

    def fetch_all(
        self, sql: str, params: tuple = ()
    ) -> list[sqlite3.Row]:
        """Execute and return all matching rows."""
        cursor = self.execute(sql, params)
        return cursor.fetchall()

    def commit(self) -> None:
        """Commit the current transaction."""
        self._get_connection().commit()

    # ── Stats ────────────────────────────────────────────────

    def get_stats(self) -> dict:
        """Return knowledge base statistics."""
        doc_count = self.fetch_one(
            "SELECT COUNT(*) as count FROM documents"
        )
        chunk_count = self.fetch_one(
            "SELECT COUNT(*) as count FROM document_chunks"
        )
        conv_count = self.fetch_one(
            "SELECT COUNT(*) as count FROM conversations"
        )
        return {
            "documents": doc_count["count"] if doc_count else 0,
            "chunks": chunk_count["count"] if chunk_count else 0,
            "conversations": conv_count["count"] if conv_count else 0,
            "database_path": str(self.db_path),
            "database_size_mb": round(
                self.db_path.stat().st_size / (1024 * 1024), 2
            ) if self.db_path.exists() else 0,
        }
