"""
LUX Chat Generation

Wraps the OpenAI-compatible chat completions API provided
by Foundry Local. Supports system/user/assistant messages,
temperature control, and response timing.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger("lux.llm.generation")


@dataclass
class GenerationResult:
    """Result of a chat completion request."""
    content: str = ""
    model: str = ""
    finish_reason: str = ""
    generation_time: float = 0.0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class ChatGenerator:
    """
    Generates chat completions through the local Foundry Local LLM.

    Uses the OpenAI-compatible API format so that existing OpenAI
    code patterns work without modification.
    """

    def __init__(self, foundry_client, config) -> None:
        self._foundry = foundry_client
        self._config = config

    def generate(
        self,
        messages: list[dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> GenerationResult:
        """
        Generate a chat completion from the local LLM.

        Args:
            messages: List of message dicts with 'role' and 'content' keys.
                      Roles: 'system', 'user', 'assistant'.
            temperature: Override the default temperature (0.0 = deterministic).
            max_tokens: Override the default max tokens.

        Returns:
            GenerationResult with the generated text and metadata.
        """
        client = self._foundry.get_openai_client()
        temp = temperature if temperature is not None else self._config.temperature
        tokens = max_tokens if max_tokens is not None else self._config.max_tokens

        start = time.time()

        try:
            response = client.chat.completions.create(
                model=self._config.chat_model,
                messages=messages,
                temperature=temp,
                max_tokens=tokens,
            )

            elapsed = time.time() - start
            choice = response.choices[0]
            usage = response.usage

            result = GenerationResult(
                content=choice.message.content or "",
                model=response.model or self._config.chat_model,
                finish_reason=choice.finish_reason or "unknown",
                generation_time=round(elapsed, 3),
                prompt_tokens=usage.prompt_tokens if usage else 0,
                completion_tokens=usage.completion_tokens if usage else 0,
                total_tokens=usage.total_tokens if usage else 0,
            )

            logger.info(
                "Generated response in %.2fs (%d tokens)",
                elapsed, result.total_tokens,
            )
            return result

        except Exception as e:
            elapsed = time.time() - start
            logger.error("Generation failed after %.2fs: %s", elapsed, e)
            return GenerationResult(
                content=f"I encountered an error generating a response: {e}",
                generation_time=round(elapsed, 3),
                finish_reason="error",
            )
