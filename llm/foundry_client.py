"""
LUX Foundry Local Client

Wrapper around Microsoft Foundry Local SDK.
Handles initialization, model discovery, download, loading,
and provides the OpenAI-compatible endpoint for inference.
"""

from __future__ import annotations

import logging
import time
from typing import Optional

import openai

logger = logging.getLogger("lux.llm.foundry_client")


class FoundryClient:
    """
    Manages the Foundry Local runtime lifecycle.

    Initializes the SDK, downloads/loads models, and exposes
    the OpenAI-compatible client for chat and embedding calls.
    """

    def __init__(self, config) -> None:
        self.config = config
        self._manager = None
        self._chat_model = None
        self._embedding_model = None
        self._openai_client: Optional[openai.OpenAI] = None
        self._initialized = False

    def initialize(self) -> None:
        """
        Initialize the Foundry Local SDK and prepare models.
        Call this once at application startup.
        """
        if self._initialized:
            return

        try:
            from foundry_local_sdk import Configuration, FoundryLocalManager

            logger.info("Initializing Foundry Local SDK...")
            start = time.time()

            sdk_config = Configuration(app_name=self.config.app_name)
            FoundryLocalManager.initialize(sdk_config)
            self._manager = FoundryLocalManager.instance
            
            # Start the web service to expose the API
            self._manager.start_web_service()

            elapsed = time.time() - start
            logger.info("Foundry Local SDK initialized in %.2fs", elapsed)
            self._initialized = True

        except ImportError:
            logger.error(
                "foundry-local-sdk not installed. "
                "Install with: pip install foundry-local-sdk-winml"
            )
            raise RuntimeError(
                "Foundry Local SDK not found. Please install it: "
                "pip install foundry-local-sdk-winml"
            )
        except Exception as e:
            logger.error("Failed to initialize Foundry Local: %s", e)
            raise

    def load_chat_model(self) -> None:
        """Download and load the chat model."""
        self._ensure_initialized()
        model_alias = self.config.chat_model
        logger.info("Loading chat model: %s", model_alias)
        start = time.time()

        try:
            self._chat_model = self._manager.catalog.get_model(model_alias)
            self._chat_model.download(
                lambda p: logger.info("Chat model download: %.1f%%", p)
            )
            self._chat_model.load()
            elapsed = time.time() - start
            logger.info("Chat model '%s' loaded in %.2fs", model_alias, elapsed)
        except Exception as e:
            logger.error("Failed to load chat model '%s': %s", model_alias, e)
            raise

    def load_embedding_model(self) -> None:
        """Download and load the embedding model."""
        self._ensure_initialized()
        model_alias = self.config.embedding_model
        logger.info("Loading embedding model: %s", model_alias)
        start = time.time()

        try:
            self._embedding_model = self._manager.catalog.get_model(model_alias)
            self._embedding_model.download(
                lambda p: logger.info("Embedding model download: %.1f%%", p)
            )
            self._embedding_model.load()
            elapsed = time.time() - start
            logger.info(
                "Embedding model '%s' loaded in %.2fs", model_alias, elapsed
            )
        except Exception as e:
            logger.error(
                "Failed to load embedding model '%s': %s", model_alias, e
            )
            raise

    def get_openai_client(self) -> openai.OpenAI:
        """
        Return an OpenAI client pointed at the local Foundry endpoint.
        Foundry Local exposes an OpenAI-compatible API.
        """
        self._ensure_initialized()
        if self._openai_client is None:
            self._openai_client = openai.OpenAI(
                base_url=self.endpoint,
                api_key="local-no-key-needed",
            )
        return self._openai_client

    @property
    def endpoint(self) -> str:
        """Return the local Foundry endpoint URL."""
        self._ensure_initialized()
        if hasattr(self._manager, 'urls') and self._manager.urls:
            return self._manager.urls[0].rstrip("/") + "/v1"
        return "http://127.0.0.1:58114/v1"  # Default fallback

    @property
    def chat_model_name(self) -> str:
        return self.config.chat_model

    @property
    def embedding_model_name(self) -> str:
        return self.config.embedding_model

    def is_healthy(self) -> bool:
        """Check if the Foundry Local service is responsive."""
        try:
            client = self.get_openai_client()
            client.models.list()
            return True
        except Exception:
            return False

    def _ensure_initialized(self) -> None:
        if not self._initialized:
            raise RuntimeError(
                "FoundryClient not initialized. Call initialize() first."
            )
