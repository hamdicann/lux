"""
LUX — Database Initialization Script

Creates the SQLite database and applies the schema.

Usage:
    python scripts/initialize_db.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

from app.config import config
from storage.database import DatabaseManager
from storage.migrations import run_migrations


def main():
    print("LUX — Database Initialization")
    print("=" * 40)

    config.ensure_directories()

    print(f"Database path: {config.database_path}")

    db = DatabaseManager(config.database_path)
    db.initialize()

    # Run any pending migrations
    run_migrations(db)

    stats = db.get_stats()
    print(f"Documents: {stats['documents']}")
    print(f"Chunks:    {stats['chunks']}")
    print(f"DB Size:   {stats['database_size_mb']} MB")

    db.close()
    print("\nDatabase ready!")


if __name__ == "__main__":
    main()
