"""
LUX Dependency Management

Singleton access to shared services: Foundry Local manager,
database connections, embedding service, and the LUX agent.
Avoids re-initializing expensive resources on every request.
"""

from __future__ import annotations

import logging
from typing import Optional

from app.config import config

logger = logging.getLogger("lux.dependencies")

# ── Singletons ───────────────────────────────────────────────────
_db_manager: Optional[object] = None
_foundry_client: Optional[object] = None
_embedding_service: Optional[object] = None
_lux_agent: Optional[object] = None


def get_db():
    """Return the shared DatabaseManager instance."""
    global _db_manager
    if _db_manager is None:
        from storage.database import DatabaseManager
        _db_manager = DatabaseManager(config.database_path)
        _db_manager.initialize()
        logger.info("Database initialized at %s", config.database_path)
    return _db_manager


def get_foundry_client():
    """Return the shared FoundryClient instance."""
    global _foundry_client
    if _foundry_client is None:
        from llm.foundry_client import FoundryClient
        _foundry_client = FoundryClient(config)
        _foundry_client.initialize()
        logger.info("Foundry client initialized")
    return _foundry_client


def get_embedding_service():
    """Return the shared EmbeddingService instance."""
    global _embedding_service
    if _embedding_service is None:
        from llm.embeddings import EmbeddingService
        client = get_foundry_client()
        _embedding_service = EmbeddingService(client, config)
        logger.info("Embedding service initialized")
    return _embedding_service


def get_agent():
    """Return the shared LuxAgent instance."""
    global _lux_agent
    if _lux_agent is None:
        from core.agent import LuxAgent
        _lux_agent = LuxAgent(config)
        logger.info("LUX agent initialized")
    return _lux_agent


def reset_all() -> None:
    """Reset all singletons (useful for testing)."""
    global _db_manager, _foundry_client, _embedding_service, _lux_agent
    _db_manager = None
    _foundry_client = None
    _embedding_service = None
    _lux_agent = None
