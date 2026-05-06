"""RSS news collector."""

from __future__ import annotations

import logging

from industry_intelligence_agent.models import SourceDocument
from industry_intelligence_agent.parsers.text import clean_text

logger = logging.getLogger(__name__)


def collect_news(
    query: str,
    feeds: list[str],
    max_items: int = 8,
) -> list[SourceDocument]:
    """Collect RSS news items whose title or summary contains the query."""
    if not query or not feeds:
        return []

    import feedparser

    query_lower = query.lower()
    documents: list[SourceDocument] = []

    for feed_url in feeds:
        logger.info("Reading RSS feed: %s", feed_url)
        parsed = feedparser.parse(feed_url)
        for entry in parsed.entries:
            title = clean_text(getattr(entry, "title", ""))
            summary = clean_text(getattr(entry, "summary", ""))
            haystack = f"{title} {summary}".lower()

            if query_lower not in haystack:
                continue

            documents.append(
                SourceDocument(
                    source_type="news",
                    title=title or "Untitled news item",
                    url=getattr(entry, "link", ""),
                    text=summary,
                    published_at=getattr(entry, "published", ""),
                    metadata={"feed_url": feed_url},
                )
            )

            if len(documents) >= max_items:
                return documents

    return documents

