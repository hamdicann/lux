"""
LUX Agent

High-level interface for interacting with LUX.
Manages conversation state and delegates to the orchestrator.
"""

from __future__ import annotations

import logging
from typing import Optional

from app.config import LuxConfig
from core.orchestrator import LuxOrchestrator, LuxResponse
from llm.foundry_client import FoundryClient
from llm.embeddings import EmbeddingService
from llm.model_manager import ModelManager
from storage.database import DatabaseManager
from storage.repositories import ConversationRepository

logger = logging.getLogger("lux.core.agent")


class LuxAgent:
    """
    The main LUX agent — top-level entry point for all interactions.

    Usage:
        agent = LuxAgent(config)
        agent.initialize()
        response = agent.handle("What is RAG?")
    """

    def __init__(self, config: LuxConfig) -> None:
        self.config = config
        self._initialized = False

        # Components (lazily initialized)
        self._db: Optional[DatabaseManager] = None
        self._foundry: Optional[FoundryClient] = None
        self._embeddings: Optional[EmbeddingService] = None
        self._orchestrator: Optional[LuxOrchestrator] = None
        self._conversations: Optional[ConversationRepository] = None
        self._model_manager: Optional[ModelManager] = None

    def initialize(self) -> dict:
        """
        Initialize all LUX components.

        Returns dict with initialization timing info.
        """
        import time
        timings = {}

        logger.info("Initializing LUX agent...")
        start = time.time()

        # 1. Ensure directories exist
        self.config.ensure_directories()

        # 2. Initialize database
        db_start = time.time()
        self._db = DatabaseManager(self.config.database_path)
        self._db.initialize()
        timings["database"] = round(time.time() - db_start, 2)

        # 3. Initialize Foundry Local
        foundry_start = time.time()
        self._foundry = FoundryClient(self.config)
        self._foundry.initialize()
        timings["foundry_init"] = round(time.time() - foundry_start, 2)

        # 4. Load models (warm-up)
        self._model_manager = ModelManager(self._foundry)
        model_timings = self._model_manager.warm_up()
        timings.update(model_timings)

        # 5. Initialize embedding service
        self._embeddings = EmbeddingService(self._foundry, self.config)

        # 6. Initialize orchestrator
        self._orchestrator = LuxOrchestrator(
            config=self.config,
            foundry_client=self._foundry,
            embedding_service=self._embeddings,
            db=self._db,
        )

        # 7. Conversation repository
        self._conversations = ConversationRepository(self._db)

        self._initialized = True
        total = round(time.time() - start, 2)
        timings["total"] = total

        logger.info("LUX agent initialized in %.2fs", total)
        return timings

    def handle(
        self,
        user_message: str,
        conversation_id: Optional[int] = None,
    ) -> LuxResponse:
        """
        Handle a user message and return a LUX response.

        Args:
            user_message: The user's question or message.
            conversation_id: Optional ID for conversation continuity.

        Returns:
            LuxResponse with answer, sources, and metadata.
        """
        self._ensure_initialized()
        return self._orchestrator.process_query(user_message, conversation_id)

    def create_conversation(self, title: str = "") -> int:
        """Create a new conversation and return its ID."""
        self._ensure_initialized()
        return self._conversations.create_conversation(title)

    def get_knowledge_base_stats(self) -> dict:
        """Return knowledge base statistics."""
        self._ensure_initialized()
        stats = self._db.get_stats()
        stats["embedding_model"] = self.config.embedding_model
        stats["chat_model"] = self.config.chat_model
        return stats

    @property
    def db(self) -> DatabaseManager:
        self._ensure_initialized()
        return self._db

    @property
    def foundry(self) -> FoundryClient:
        self._ensure_initialized()
        return self._foundry

    @property
    def embeddings(self) -> EmbeddingService:
        self._ensure_initialized()
        return self._embeddings

    def _ensure_initialized(self) -> None:
        if not self._initialized:
            raise RuntimeError(
                "LuxAgent not initialized. Call initialize() first."
            )
