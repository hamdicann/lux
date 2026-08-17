"""
LUX Response Validators

Basic quality gates for generated responses.
Checks for empty, trivially short, or error responses.
"""

from __future__ import annotations

import logging

logger = logging.getLogger("lux.core.validators")


def validate_response(content: str) -> tuple[bool, str]:
    """
    Validate a generated response.

    Returns:
        (is_valid, reason) tuple.
    """
    if not content or not content.strip():
        return False, "Empty response"

    content = content.strip()

    if len(content) < 5:
        return False, "Response too short"

    return True, "ok"


def sanitize_response(content: str) -> str:
    """Clean up a response before returning to the user."""
    if not content:
        return ""

    # Strip leading/trailing whitespace
    content = content.strip()

    return content
