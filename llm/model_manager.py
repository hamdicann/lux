"""
LUX Model Manager

Handles model lifecycle: catalog access, download progress,
load/unload, and health status for Foundry Local models.
"""

from __future__ import annotations

import logging
from typing import Optional

logger = logging.getLogger("lux.llm.model_manager")


class ModelManager:
    """
    Manages the lifecycle of local AI models through Foundry Local.

    Provides model discovery, download tracking, and status reporting.
    """

    def __init__(self, foundry_client) -> None:
        self._foundry = foundry_client

    def get_model_info(self) -> dict:
        """Return information about currently configured models."""
        return {
            "chat_model": self._foundry.chat_model_name,
            "embedding_model": self._foundry.embedding_model_name,
            "endpoint": self._foundry.endpoint if self._foundry._initialized else "not initialized",
            "healthy": self._foundry.is_healthy() if self._foundry._initialized else False,
        }

    def warm_up(self) -> dict:
        """
        Warm up both models by loading them.
        Returns timing information.
        """
        import time
        results = {}

        start = time.time()
        try:
            self._foundry.load_chat_model()
            results["chat_model_load_time"] = round(time.time() - start, 2)
        except Exception as e:
            results["chat_model_error"] = str(e)

        start = time.time()
        try:
            self._foundry.load_embedding_model()
            results["embedding_model_load_time"] = round(time.time() - start, 2)
        except Exception as e:
            results["embedding_model_error"] = str(e)

        return results
