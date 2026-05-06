"""Configured annual report and industry report collection."""

from __future__ import annotations

import logging

from industry_intelligence_agent.models import SourceDocument
from industry_intelligence_agent.parsers.pdf import extract_pdf_text_from_url
from industry_intelligence_agent.parsers.text import extract_html_text, first_n_words
from industry_intelligence_agent.utils.http import fetch_text

logger = logging.getLogger(__name__)


def collect_configured_reports(
    company: str = "",
    industry: str = "",
    config: dict | None = None,
    timeout: int = 15,
) -> list[SourceDocument]:
    """Read report URLs from config and extract basic text."""
    config = config or {}
    documents: list[SourceDocument] = []

    for url in _matching_urls(company, config.get("company_reports", {})):
        documents.append(_read_report(url, "annual_report", timeout))

    for url in _matching_urls(industry, config.get("industry_reports", {})):
        documents.append(_read_report(url, "industry_report", timeout))

    return documents


def _matching_urls(query: str, mapping: dict[str, list[str]]) -> list[str]:
    if not query:
        return []

    query_lower = query.lower()
    for key, urls in mapping.items():
        if key.lower() == query_lower or key.lower() in query_lower or query_lower in key.lower():
            return urls
    return []


def _read_report(url: str, source_type: str, timeout: int) -> SourceDocument:
    logger.info("Reading %s: %s", source_type, url)
    title = url.split("/")[-1] or source_type

    try:
        if url.lower().split("?")[0].endswith(".pdf"):
            text = extract_pdf_text_from_url(url, timeout=timeout)
        else:
            text = extract_html_text(fetch_text(url, timeout=timeout))
    except Exception as exc:
        logger.warning("Could not read report %s: %s", url, exc)
        text = ""

    return SourceDocument(
        source_type=source_type,
        title=title,
        url=url,
        text=first_n_words(text, limit=2500),
        metadata={"read_status": "ok" if text else "failed_or_empty"},
    )

