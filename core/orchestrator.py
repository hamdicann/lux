"""
LUX Orchestrator

The central coordination layer that ties together:
- Query routing (chat vs. RAG)
- Embedding generation
- Vector retrieval
- Context building
- LLM generation
- Source tracking
- Debug information
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Optional

from app.config import LuxConfig
from core.router import classify_query, QueryType
from core.context import build_messages
from core.policies import should_decline_answer, INSUFFICIENT_CONTEXT_MESSAGE
from core.validators import validate_response, sanitize_response
from llm.foundry_client import FoundryClient
from llm.embeddings import EmbeddingService
from llm.generation import ChatGenerator, GenerationResult
from rag.retrieval import RetrievalEngine, RetrievalResult
from rag.ranking import rank_and_filter
from rag.context_builder import build_context, build_source_list
from storage.database import DatabaseManager
from storage.repositories import ConversationRepository, Message

logger = logging.getLogger("lux.core.orchestrator")


@dataclass
class LuxResponse:
    """Complete response from LUX with metadata."""
    answer: str = ""
    sources: list[dict] = field(default_factory=list)
    retrieval_used: bool = False
    retrieved_chunks: int = 0
    query_type: str = ""
    generation_time: float = 0.0
    total_time: float = 0.0
    model: str = ""
    debug: Optional[dict] = None


class LuxOrchestrator:
    """
    Coordinates the full LUX pipeline:
    user query → routing → [embedding → retrieval → ranking → context] → LLM → response
    """

    def __init__(
        self,
        config: LuxConfig,
        foundry_client: FoundryClient,
        embedding_service: EmbeddingService,
        db: DatabaseManager,
    ) -> None:
        self.config = config
        self.foundry = foundry_client
        self.embeddings = embedding_service
        self.generator = ChatGenerator(foundry_client, config)
        self.retrieval = RetrievalEngine(db)
        self.conversations = ConversationRepository(db)

    def process_query(
        self,
        user_message: str,
        conversation_id: Optional[int] = None,
    ) -> LuxResponse:
        """
        Process a user query through the full LUX pipeline.

        Args:
            user_message: The user's question or message.
            conversation_id: Optional conversation ID for history.

        Returns:
            LuxResponse with answer, sources, and debug info.
        """
        total_start = time.time()
        debug_info = {} if self.config.debug else None

        # ── Step 1: Validate input ───────────────────────────
        if not user_message or not user_message.strip():
            return LuxResponse(
                answer="Please enter a question or message.",
                query_type="invalid",
            )

        user_message = user_message.strip()

        # ── Step 2: Route the query ──────────────────────────
        query_type = classify_query(user_message)
        logger.info("Query type: %s — '%s'", query_type.value, user_message[:80])

        if debug_info is not None:
            debug_info["query"] = user_message
            debug_info["query_type"] = query_type.value

        # ── Step 3: Retrieve context if needed ───────────────
        retrieval_results: list[RetrievalResult] = []
        context_text = ""
        retrieval_used = query_type == QueryType.RAG_QUERY

        if retrieval_used:
            try:
                # Generate query embedding
                embed_start = time.time()
                query_embedding = self.embeddings.embed_text(user_message)
                embed_time = time.time() - embed_start

                if debug_info is not None:
                    debug_info["embedding_time"] = round(embed_time, 3)

                # Search for relevant chunks
                search_start = time.time()
                retrieval_results = self.retrieval.search(
                    query_embedding=query_embedding,
                    top_k=self.config.top_k,
                    min_similarity=self.config.min_similarity,
                )
                search_time = time.time() - search_start

                if debug_info is not None:
                    debug_info["search_time"] = round(search_time, 3)
                    debug_info["raw_results"] = len(retrieval_results)

                # Post-process: deduplicate and apply budget
                retrieval_results = rank_and_filter(
                    retrieval_results,
                    max_chars=self.config.max_context_chars,
                )

                if debug_info is not None:
                    debug_info["filtered_results"] = len(retrieval_results)
                    debug_info["top_results"] = [
                        {
                            "filename": r.filename,
                            "score": r.score,
                            "page": r.page,
                            "section": r.section,
                            "preview": r.content[:100] + "..."
                            if len(r.content) > 100 else r.content,
                        }
                        for r in retrieval_results
                    ]

                # Build formatted context
                context_text = build_context(retrieval_results)

            except Exception as e:
                logger.error("Retrieval failed: %s", e)
                if debug_info is not None:
                    debug_info["retrieval_error"] = str(e)

        # ── Step 4: Check if we should decline ───────────────
        top_score = retrieval_results[0].score if retrieval_results else 0.0
        if should_decline_answer(
            retrieval_used=retrieval_used,
            results_found=len(retrieval_results),
            top_score=top_score,
            min_similarity=self.config.min_similarity,
        ):
            if debug_info is not None:
                debug_info["declined"] = True
                debug_info["reason"] = "insufficient_context"

        # ── Step 5: Get conversation history ─────────────────
        history: list[Message] = []
        if conversation_id:
            try:
                history = self.conversations.get_messages(
                    conversation_id,
                    limit=self.config.max_conversation_turns * 2,
                )
            except Exception as e:
                logger.warning("Could not load conversation history: %s", e)

        # ── Step 6: Build messages for LLM ───────────────────
        messages = build_messages(
            user_question=user_message,
            context=context_text if retrieval_results else None,
            conversation_history=history if history else None,
            max_turns=self.config.max_conversation_turns,
            retrieval_used=retrieval_used,
        )

        if debug_info is not None:
            debug_info["message_count"] = len(messages)
            debug_info["context_chars"] = len(context_text)

        # ── Step 7: Generate response ────────────────────────
        gen_result: GenerationResult = self.generator.generate(messages)

        if debug_info is not None:
            debug_info["model"] = gen_result.model
            debug_info["generation_time"] = gen_result.generation_time
            debug_info["tokens"] = {
                "prompt": gen_result.prompt_tokens,
                "completion": gen_result.completion_tokens,
                "total": gen_result.total_tokens,
            }

        # ── Step 8: Validate and sanitize ────────────────────
        answer = sanitize_response(gen_result.content)
        is_valid, reason = validate_response(answer)
        if not is_valid:
            logger.warning("Response validation failed: %s", reason)
            answer = INSUFFICIENT_CONTEXT_MESSAGE

        # ── Step 9: Build source list ────────────────────────
        sources = build_source_list(retrieval_results) if retrieval_results else []

        # ── Step 10: Save to conversation ────────────────────
        if conversation_id:
            try:
                self.conversations.add_message(
                    conversation_id, "user", user_message
                )
                self.conversations.add_message(
                    conversation_id, "assistant", answer,
                    sources=sources,
                    debug_info=debug_info,
                )
            except Exception as e:
                logger.warning("Could not save to conversation: %s", e)

        total_time = round(time.time() - total_start, 3)

        if debug_info is not None:
            debug_info["total_time"] = total_time

        return LuxResponse(
            answer=answer,
            sources=sources,
            retrieval_used=retrieval_used,
            retrieved_chunks=len(retrieval_results),
            query_type=query_type.value,
            generation_time=gen_result.generation_time,
            total_time=total_time,
            model=gen_result.model,
            debug=debug_info,
        )
