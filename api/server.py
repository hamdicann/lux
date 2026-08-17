"""
LUX API Server

FastAPI application with lifespan events for model warm-up,
static file serving for the web UI, and CORS configuration.
"""

from __future__ import annotations

import logging
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import config

# Configure logging
logging.basicConfig(
    level=getattr(logging, config.log_level.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("lux.api.server")

# Shared agent instance
_agent = None


def get_agent():
    """Return the initialized LUX agent."""
    global _agent
    if _agent is None:
        raise RuntimeError("Agent not initialized")
    return _agent


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan: initialize on startup, cleanup on shutdown.
    Warms up models at startup to avoid cold-start on first request.
    """
    global _agent

    logger.info("=" * 60)
    logger.info("  LUX — Local AI Knowledge Assistant")
    logger.info("=" * 60)

    # Ensure directories exist
    config.ensure_directories()

    # Initialize the agent (loads models)
    from core.agent import LuxAgent
    _agent = LuxAgent(config)

    logger.info("Initializing LUX (this may take a moment for model download)...")
    timings = _agent.initialize()

    stats = _agent.get_knowledge_base_stats()
    logger.info("Knowledge base: %d documents, %d chunks", stats["documents"], stats["chunks"])
    logger.info("Chat model: %s", config.chat_model)
    logger.info("Embedding model: %s", config.embedding_model)
    logger.info("Initialization timings: %s", timings)
    logger.info("LUX is ready at http://%s:%d", config.host, config.port)
    logger.info("=" * 60)

    yield  # Application runs here

    # Cleanup
    logger.info("Shutting down LUX...")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="LUX",
        description="Local AI Knowledge Assistant",
        version="1.0.0",
        lifespan=lifespan,
    )

    # CORS — allow local browser access
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Mount API routes
    from api.routes import router
    app.include_router(router)

    # Serve the web UI as static files
    ui_path = Path(__file__).parent.parent / "ui"
    if ui_path.exists():
        app.mount("/", StaticFiles(directory=str(ui_path), html=True), name="ui")

    return app


# Create the app instance
app = create_app()
