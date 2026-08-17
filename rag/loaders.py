"""
LUX Document Loaders

File-type-specific text extractors for TXT, Markdown, and PDF.
Each loader returns normalized text and metadata. Designed so
additional formats can be added by implementing a new loader class.
"""

from __future__ import annotations

import hashlib
import logging
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger("lux.rag.loaders")


@dataclass
class LoadedDocument:
    """Result of loading a document: text content + metadata."""
    text: str = ""
    filename: str = ""
    filepath: str = ""
    file_type: str = ""
    title: str = ""
    source: str = ""
    file_hash: str = ""
    pages: list[dict] = field(default_factory=list)
    # pages: [{"page": 1, "text": "...", "section": "..."}]


def compute_file_hash(filepath: Path) -> str:
    """Compute SHA-256 hash of file contents for deduplication."""
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        for block in iter(lambda: f.read(8192), b""):
            sha256.update(block)
    return sha256.hexdigest()


class BaseLoader(ABC):
    """Abstract base class for document loaders."""

    @abstractmethod
    def load(self, filepath: Path) -> LoadedDocument:
        """Load a document and return its text with metadata."""
        ...

    @abstractmethod
    def supported_extensions(self) -> list[str]:
        """Return list of file extensions this loader handles."""
        ...

    def _base_metadata(self, filepath: Path, file_type: str) -> dict:
        """Compute common metadata fields."""
        return {
            "filename": filepath.name,
            "filepath": str(filepath),
            "file_type": file_type,
            "title": filepath.stem.replace("_", " ").replace("-", " ").title(),
            "source": str(filepath),
            "file_hash": compute_file_hash(filepath),
        }


class TextLoader(BaseLoader):
    """Loader for plain text files (.txt)."""

    def supported_extensions(self) -> list[str]:
        return [".txt"]

    def load(self, filepath: Path) -> LoadedDocument:
        logger.info("Loading text file: %s", filepath.name)
        meta = self._base_metadata(filepath, "txt")
        text = filepath.read_text(encoding="utf-8", errors="replace")

        return LoadedDocument(
            text=text,
            pages=[{"page": 1, "text": text}],
            **meta,
        )


class MarkdownLoader(BaseLoader):
    """Loader for Markdown files (.md)."""

    def supported_extensions(self) -> list[str]:
        return [".md", ".markdown"]

    def load(self, filepath: Path) -> LoadedDocument:
        logger.info("Loading markdown file: %s", filepath.name)
        meta = self._base_metadata(filepath, "markdown")
        text = filepath.read_text(encoding="utf-8", errors="replace")

        # Extract title from first heading if present
        title = meta["title"]
        for line in text.split("\n"):
            stripped = line.strip()
            if stripped.startswith("# "):
                title = stripped[2:].strip()
                break

        # Split by headings to preserve section info
        sections = self._extract_sections(text)

        return LoadedDocument(
            text=text,
            title=title,
            pages=sections if sections else [{"page": 1, "text": text}],
            filename=meta["filename"],
            filepath=meta["filepath"],
            file_type=meta["file_type"],
            source=meta["source"],
            file_hash=meta["file_hash"],
        )

    def _extract_sections(self, text: str) -> list[dict]:
        """Split markdown by headings into sections."""
        sections = []
        current_section = ""
        current_heading = ""
        idx = 1

        for line in text.split("\n"):
            if line.strip().startswith("#"):
                # Save previous section
                if current_section.strip():
                    sections.append({
                        "page": idx,
                        "text": current_section.strip(),
                        "section": current_heading,
                    })
                    idx += 1
                current_heading = line.strip().lstrip("#").strip()
                current_section = line + "\n"
            else:
                current_section += line + "\n"

        # Save last section
        if current_section.strip():
            sections.append({
                "page": idx,
                "text": current_section.strip(),
                "section": current_heading,
            })

        return sections


class PDFLoader(BaseLoader):
    """Loader for PDF files (.pdf) using PyMuPDF."""

    def supported_extensions(self) -> list[str]:
        return [".pdf"]

    def load(self, filepath: Path) -> LoadedDocument:
        logger.info("Loading PDF file: %s", filepath.name)
        meta = self._base_metadata(filepath, "pdf")

        try:
            import fitz  # PyMuPDF
        except ImportError:
            raise ImportError(
                "PyMuPDF is required for PDF support. "
                "Install with: pip install pymupdf"
            )

        pages = []
        full_text_parts = []

        try:
            doc = fitz.open(str(filepath))
            title = doc.metadata.get("title", "") or meta["title"]

            for page_num in range(len(doc)):
                page = doc[page_num]
                page_text = page.get_text("text")
                if page_text.strip():
                    pages.append({
                        "page": page_num + 1,
                        "text": page_text.strip(),
                    })
                    full_text_parts.append(page_text.strip())

            doc.close()
        except Exception as e:
            logger.error("Failed to parse PDF '%s': %s", filepath.name, e)
            raise ValueError(f"Malformed PDF: {filepath.name} — {e}")

        full_text = "\n\n".join(full_text_parts)

        if not full_text.strip():
            logger.warning("PDF '%s' contains no extractable text", filepath.name)

        return LoadedDocument(
            text=full_text,
            title=title,
            pages=pages,
            filename=meta["filename"],
            filepath=meta["filepath"],
            file_type=meta["file_type"],
            source=meta["source"],
            file_hash=meta["file_hash"],
        )


# ── Loader Factory ───────────────────────────────────────────────

# Registry of available loaders
_LOADERS: list[BaseLoader] = [
    TextLoader(),
    MarkdownLoader(),
    PDFLoader(),
]

# Build extension → loader mapping
_EXTENSION_MAP: dict[str, BaseLoader] = {}
for loader in _LOADERS:
    for ext in loader.supported_extensions():
        _EXTENSION_MAP[ext.lower()] = loader


def get_loader(filepath: Path) -> Optional[BaseLoader]:
    """
    Select the appropriate loader for a file based on its extension.

    Returns None if the file type is not supported.
    """
    ext = filepath.suffix.lower()
    return _EXTENSION_MAP.get(ext)


def get_supported_extensions() -> list[str]:
    """Return all supported file extensions."""
    return list(_EXTENSION_MAP.keys())


def load_document(filepath: Path) -> LoadedDocument:
    """
    Load a document using the appropriate loader.

    Raises ValueError if the file type is not supported.
    """
    loader = get_loader(filepath)
    if loader is None:
        raise ValueError(
            f"Unsupported file type: {filepath.suffix}. "
            f"Supported: {get_supported_extensions()}"
        )
    return loader.load(filepath)
