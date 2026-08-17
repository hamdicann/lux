"""
LUX API Routes

All HTTP endpoints for the LUX local API.
Local-only by default — no external access required.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.config import config

logger = logging.getLogger("lux.api.routes")

router = APIRouter(prefix="/api")


# ── Request / Response Models ────────────────────────────────────

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="User message")
    conversation_id: Optional[int] = Field(None, description="Conversation ID for history")
    debug: Optional[bool] = Field(None, description="Override debug mode")


class ChatResponse(BaseModel):
    answer: str
    sources: list[dict] = []
    retrieval_used: bool = False
    retrieved_chunks: int = 0
    query_type: str = ""
    generation_time: float = 0.0
    total_time: float = 0.0
    model: str = ""
    conversation_id: Optional[int] = None
    debug: Optional[dict] = None


class IngestRequest(BaseModel):
    directory: Optional[str] = Field(None, description="Directory to ingest")
    recursive: bool = True


class IngestResponse(BaseModel):
    total_files: int = 0
    ingested: int = 0
    skipped: int = 0
    failed: int = 0
    total_chunks: int = 0
    duration: float = 0.0
    errors: list[str] = []


class ConversationCreate(BaseModel):
    title: str = "New Conversation"


# ── Health ───────────────────────────────────────────────────────

@router.get("/health")
async def health_check():
    """Check if LUX is running and healthy."""
    from api.server import get_agent
    try:
        agent = get_agent()
        stats = agent.get_knowledge_base_stats()
        return {
            "status": "healthy",
            "knowledge_base": stats,
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


# ── Chat ─────────────────────────────────────────────────────────

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Send a message to LUX and get a response."""
    from api.server import get_agent
    agent = get_agent()

    # Enable debug if requested
    original_debug = config.debug
    if request.debug is not None:
        config.debug = request.debug

    try:
        # Create conversation if needed
        conversation_id = request.conversation_id
        if conversation_id is None:
            title = request.message.strip()
            if len(title) > 30:
                title = title[:27] + "..."
            conversation_id = agent.create_conversation(title=title)

        response = agent.handle(request.message, conversation_id)

        return ChatResponse(
            answer=response.answer,
            sources=response.sources,
            retrieval_used=response.retrieval_used,
            retrieved_chunks=response.retrieved_chunks,
            query_type=response.query_type,
            generation_time=response.generation_time,
            total_time=response.total_time,
            model=response.model,
            conversation_id=conversation_id,
            debug=response.debug,
        )
    finally:
        config.debug = original_debug


# ── Documents ────────────────────────────────────────────────────

@router.post("/documents/ingest", response_model=IngestResponse)
async def ingest_documents(request: IngestRequest):
    """Ingest documents from a directory into the knowledge base."""
    from api.server import get_agent
    from rag.ingestion import IngestionPipeline

    agent = get_agent()

    pipeline = IngestionPipeline(
        config=config,
        db=agent.db,
        embedding_service=agent.embeddings,
    )

    directory = Path(request.directory) if request.directory else config.document_path

    result = pipeline.ingest_directory(
        directory=directory,
        recursive=request.recursive,
    )

    return IngestResponse(
        total_files=result.total_files,
        ingested=result.ingested,
        skipped=result.skipped,
        failed=result.failed,
        total_chunks=result.total_chunks,
        duration=result.duration,
        errors=result.errors,
    )


@router.get("/documents")
async def list_documents():
    """List all indexed documents."""
    from api.server import get_agent
    from storage.repositories import DocumentRepository

    agent = get_agent()
    doc_repo = DocumentRepository(agent.db)
    docs = doc_repo.list_all()

    return {
        "documents": [
            {
                "id": doc.id,
                "filename": doc.filename,
                "file_type": doc.file_type,
                "title": doc.title,
                "num_chunks": doc.num_chunks,
                "created_at": doc.created_at,
            }
            for doc in docs
        ],
        "total": len(docs),
    }


@router.delete("/documents/{doc_id}")
async def delete_document(doc_id: int):
    """Delete a document and its chunks."""
    from api.server import get_agent
    from storage.repositories import DocumentRepository

    agent = get_agent()
    doc_repo = DocumentRepository(agent.db)

    doc = doc_repo.find_by_id(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    doc_repo.delete(doc_id)
    return {"status": "deleted", "document_id": doc_id, "filename": doc.filename}


# ── Knowledge Base ───────────────────────────────────────────────

@router.get("/knowledge-base/status")
async def knowledge_base_status():
    """Get knowledge base statistics."""
    from api.server import get_agent
    agent = get_agent()
    return agent.get_knowledge_base_stats()


# ── Conversations ────────────────────────────────────────────────

@router.post("/conversations")
async def create_conversation(request: ConversationCreate):
    """Create a new conversation."""
    from api.server import get_agent
    agent = get_agent()
    conv_id = agent.create_conversation(request.title)
    return {"conversation_id": conv_id, "title": request.title}


@router.get("/conversations")
async def list_conversations():
    """List all conversations."""
    from api.server import get_agent
    from storage.repositories import ConversationRepository

    agent = get_agent()
    conv_repo = ConversationRepository(agent.db)
    convs = conv_repo.list_conversations()

    return {
        "conversations": [
            {
                "id": c.id,
                "title": c.title,
                "created_at": c.created_at,
                "updated_at": c.updated_at,
            }
            for c in convs
        ],
    }


@router.get("/conversations/{conv_id}/messages")
async def get_messages(conv_id: int):
    """Get messages for a conversation."""
    from api.server import get_agent
    from storage.repositories import ConversationRepository

    agent = get_agent()
    conv_repo = ConversationRepository(agent.db)
    messages = conv_repo.get_messages(conv_id)

    return {
        "messages": [
            {
                "id": m.id,
                "role": m.role,
                "content": m.content,
                "sources": m.sources,
                "created_at": m.created_at,
            }
            for m in messages
        ],
    }


@router.delete("/conversations/{conv_id}")
async def delete_conversation(conv_id: int):
    """Delete a conversation and all its messages."""
    from api.server import get_agent
    from storage.repositories import ConversationRepository

    agent = get_agent()
    conv_repo = ConversationRepository(agent.db)

    conv = conv_repo.get_conversation(conv_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Sohbet bulunamadi")

    conv_repo.delete_conversation(conv_id)
    return {"status": "deleted", "conversation_id": conv_id}
