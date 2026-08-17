"""
LUX Text Parser / Normalizer

Cleans and normalizes extracted text before chunking.
Does NOT alter the semantic meaning of the content.
"""

from __future__ import annotations

import re
import unicodedata


def normalize_text(text: str) -> str:
    """
    Normalize extracted text for consistent chunking.

    - Normalize Unicode characters (NFC form)
    - Replace non-breaking spaces and other whitespace variants
    - Collapse multiple blank lines into at most two
    - Strip trailing whitespace from each line
    - Preserve paragraph boundaries (single blank lines)

    Does not remove content or change semantic meaning.
    """
    if not text:
        return ""

    # Unicode normalization (composed form)
    text = unicodedata.normalize("NFC", text)

    # Replace non-breaking spaces, tabs, and other whitespace
    text = text.replace("\u00a0", " ")
    text = text.replace("\t", "    ")
    text = text.replace("\r\n", "\n")
    text = text.replace("\r", "\n")

    # Strip trailing whitespace from each line
    lines = [line.rstrip() for line in text.split("\n")]

    # Collapse runs of 2+ blank lines into 1 (preserving paragraph breaks)
    normalized_lines = []
    blank_count = 0
    for line in lines:
        if line == "":
            blank_count += 1
            if blank_count <= 1:
                normalized_lines.append(line)
        else:
            blank_count = 0
            normalized_lines.append(line)

    result = "\n".join(normalized_lines).strip()
    return result


def clean_for_embedding(text: str) -> str:
    """
    Additional cleaning specifically for embedding input.
    Removes excessive formatting while preserving meaning.
    """
    if not text:
        return ""

    # Remove markdown-style formatting markers (keep the text)
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)  # bold
    text = re.sub(r"\*(.+?)\*", r"\1", text)       # italic
    text = re.sub(r"`(.+?)`", r"\1", text)         # inline code

    # Collapse whitespace
    text = re.sub(r"[ ]{2,}", " ", text)

    return text.strip()
