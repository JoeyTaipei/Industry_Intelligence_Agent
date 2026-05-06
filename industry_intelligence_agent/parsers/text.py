"""Text and HTML parsing helpers."""

from __future__ import annotations

import re


def clean_text(text: str) -> str:
    """Normalize whitespace so downstream summaries are easier to read."""
    text = re.sub(r"\s+", " ", text or "")
    return text.strip()


def extract_html_text(html: str) -> str:
    """Extract visible text from an HTML page."""
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    return clean_text(soup.get_text(" "))


def first_n_words(text: str, limit: int = 1200) -> str:
    """Keep large documents manageable for the MVP summarizer."""
    words = clean_text(text).split()
    return " ".join(words[:limit])

