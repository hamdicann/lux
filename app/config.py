"""
LUX Configuration Module

Centralizes all application settings. Values are loaded from environment
variables or a .env file, with sensible defaults for local operation.
Never hard-code configuration values elsewhere in the codebase.
"""

from __future__ import annotations

import os
from pathlib import Path
from dataclasses import dataclass, field
from dotenv import load_dotenv

# Load .env file from project root if it exists
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_PROJECT_ROOT / ".env")


def _env(key: str, default: str = "") -> str:
    """Read an environment variable with a fallback default."""
    return os.getenv(key, default)


def _env_int(key: str, default: int) -> int:
    """Read an integer environment variable."""
    raw = os.getenv(key)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _env_float(key: str, default: float) -> float:
    """Read a float environment variable."""
    raw = os.getenv(key)
    if raw is None:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def _env_bool(key: str, default: bool) -> bool:
    """Read a boolean environment variable."""
    raw = os.getenv(key)
    if raw is None:
        return default
    return raw.strip().lower() in ("true", "1", "yes")


@dataclass
class LuxConfig:
    """
    Complete LUX application configuration.

    All tunable parameters are defined here. Modify defaults or
    override via environment variables / .env file.
    """

    # ── Project Paths ────────────────────────────────────────────
    project_root: Path = field(default_factory=lambda: _PROJECT_ROOT)
    database_path: Path = field(
        default_factory=lambda: _PROJECT_ROOT / _env("LUX_DATABASE_PATH", "data/lux.db")
    )
    document_path: Path = field(
        default_factory=lambda: _PROJECT_ROOT / _env("LUX_DOCUMENT_PATH", "documents/")
    )
    log_path: Path = field(
        default_factory=lambda: _PROJECT_ROOT / _env("LUX_LOG_PATH", "data/lux.log")
    )

    # ── Model Configuration ──────────────────────────────────────
    chat_model: str = field(
        default_factory=lambda: _env("LUX_CHAT_MODEL", "phi-3.5-mini")
    )
    embedding_model: str = field(
        default_factory=lambda: _env("LUX_EMBEDDING_MODEL", "qwen3-embedding-0.6b")
    )
    app_name: str = "lux"

    # ── Chunking ─────────────────────────────────────────────────
    chunk_size: int = field(
        default_factory=lambda: _env_int("LUX_CHUNK_SIZE", 800)
    )
    chunk_overlap: int = field(
        default_factory=lambda: _env_int("LUX_CHUNK_OVERLAP", 120)
    )

    # ── Retrieval ────────────────────────────────────────────────
    top_k: int = field(
        default_factory=lambda: _env_int("LUX_TOP_K", 3)
    )
    min_similarity: float = field(
        default_factory=lambda: _env_float("LUX_MIN_SIMILARITY", 0.35)
    )
    max_context_chars: int = field(
        default_factory=lambda: _env_int("LUX_MAX_CONTEXT_CHARS", 4000)
    )

    # ── Generation ───────────────────────────────────────────────
    temperature: float = field(
        default_factory=lambda: _env_float("LUX_TEMPERATURE", 0.2)
    )
    max_tokens: int = field(
        default_factory=lambda: _env_int("LUX_MAX_TOKENS", 1024)
    )

    # ── Conversation ─────────────────────────────────────────────
    max_conversation_turns: int = field(
        default_factory=lambda: _env_int("LUX_MAX_CONVERSATION_TURNS", 10)
    )

    # ── Server ───────────────────────────────────────────────────
    host: str = field(
        default_factory=lambda: _env("LUX_HOST", "127.0.0.1")
    )
    port: int = field(
        default_factory=lambda: _env_int("LUX_PORT", 8000)
    )

    # ── Debug & Logging ──────────────────────────────────────────
    debug: bool = field(
        default_factory=lambda: _env_bool("LUX_DEBUG", False)
    )
    log_level: str = field(
        default_factory=lambda: _env("LUX_LOG_LEVEL", "INFO")
    )

    def ensure_directories(self) -> None:
        """Create required directories if they don't exist."""
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self.document_path.mkdir(parents=True, exist_ok=True)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        (self.document_path / "sample").mkdir(parents=True, exist_ok=True)
        (self.document_path / "user").mkdir(parents=True, exist_ok=True)


# Global singleton — import this everywhere
config = LuxConfig()
