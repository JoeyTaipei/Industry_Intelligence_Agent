"""PDF extraction helpers."""

from __future__ import annotations

import tempfile
from pathlib import Path

from industry_intelligence_agent.parsers.text import clean_text
from industry_intelligence_agent.utils.http import fetch_url


def extract_pdf_text_from_path(path: str | Path, max_pages: int = 12) -> str:
    """Extract text from the first pages of a PDF."""
    import pdfplumber

    chunks: list[str] = []
    with pdfplumber.open(str(path)) as pdf:
        for page in pdf.pages[:max_pages]:
            chunks.append(page.extract_text() or "")
    return clean_text(" ".join(chunks))


def extract_pdf_text_from_url(url: str, timeout: int = 15, max_pages: int = 12) -> str:
    """Download a PDF to a temp file, then extract text."""
    content = fetch_url(url, timeout=timeout)
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=True) as tmp:
        tmp.write(content)
        tmp.flush()
        return extract_pdf_text_from_path(tmp.name, max_pages=max_pages)

