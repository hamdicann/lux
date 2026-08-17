"""
LUX Schema Migrations

Simple migration system for evolving the database schema.
Each migration is a function that takes a DatabaseManager.
"""

from __future__ import annotations

import logging
from storage.database import DatabaseManager

logger = logging.getLogger("lux.storage.migrations")


def get_current_version(db: DatabaseManager) -> int:
    """Get the current schema version."""
    try:
        row = db.fetch_one(
            "SELECT MAX(version) as version FROM schema_version"
        )
        return row["version"] if row and row["version"] else 0
    except Exception:
        return 0


def run_migrations(db: DatabaseManager) -> None:
    """Run any pending migrations."""
    current = get_current_version(db)
    migrations = _get_migrations()

    for version, migrate_fn in migrations:
        if version > current:
            logger.info("Running migration %d...", version)
            migrate_fn(db)
            db.execute(
                "INSERT INTO schema_version (version) VALUES (?)",
                (version,), commit=True,
            )
            logger.info("Migration %d complete", version)


def _get_migrations() -> list[tuple[int, callable]]:
    """
    Return an ordered list of (version, migration_function) tuples.
    Add new migrations here as the schema evolves.
    """
    return [
        # Initial schema is version 1, created by schema.sql
        # Future migrations go here:
        # (2, _migration_002_add_tags),
    ]
