"""Text cleaning utilities.

Most source documents contain extra spaces, line breaks, menus, and repeated
text. These small helpers make the text easier to summarize and analyze.
"""

from __future__ import annotations

import re


def clean_text(text: str) -> str:
    """Normalize whitespace and remove empty text."""
    cleaned = re.sub(r"\s+", " ", text or "")
    return cleaned.strip()


def split_sentences(text: str) -> list[str]:
    """Split text into simple sentence-like chunks."""
    cleaned = clean_text(text)
    if not cleaned:
        return []
    return [sentence.strip() for sentence in re.split(r"(?<=[.!?])\s+", cleaned) if sentence.strip()]


def limit_words(text: str, max_words: int = 1200) -> str:
    """Keep long documents small enough for a first-pass MVP."""
    words = clean_text(text).split()
    return " ".join(words[:max_words])

