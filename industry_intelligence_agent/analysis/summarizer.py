"""Rule-based summarization for the MVP."""

from __future__ import annotations

import re

from industry_intelligence_agent.parsers.text import clean_text


RISK_KEYWORDS = ["risk", "decline", "pressure", "competition", "regulation", "shortage", "uncertainty", "cost"]
OPPORTUNITY_KEYWORDS = ["growth", "opportunity", "demand", "expansion", "innovation", "ai", "cloud", "digital"]
TREND_KEYWORDS = ["trend", "market", "industry", "customers", "supply", "technology", "investment"]
KPI_KEYWORDS = ["revenue", "margin", "profit", "cash flow", "capex", "growth", "volume", "users"]


def summarize_text(text: str, max_sentences: int = 4) -> str:
    """Return the first useful sentences as a readable short summary."""
    sentences = _split_sentences(text)
    if not sentences:
        return ""
    return " ".join(sentences[:max_sentences])


def extract_sentences_by_keywords(
    text: str,
    keywords: list[str],
    max_items: int = 5,
) -> list[str]:
    """Find sentences that mention business-relevant keywords."""
    matches: list[str] = []
    for sentence in _split_sentences(text):
        lower = sentence.lower()
        if any(keyword in lower for keyword in keywords):
            matches.append(sentence)
        if len(matches) >= max_items:
            break
    return matches


def extract_risks(text: str) -> list[str]:
    return extract_sentences_by_keywords(text, RISK_KEYWORDS)


def extract_opportunities(text: str) -> list[str]:
    return extract_sentences_by_keywords(text, OPPORTUNITY_KEYWORDS)


def extract_trends(text: str) -> list[str]:
    return extract_sentences_by_keywords(text, TREND_KEYWORDS)


def extract_kpi_signals(text: str) -> list[str]:
    return extract_sentences_by_keywords(text, KPI_KEYWORDS)


def _split_sentences(text: str) -> list[str]:
    cleaned = clean_text(text)
    if not cleaned:
        return []

    raw_sentences = re.split(r"(?<=[.!?])\s+", cleaned)
    return [sentence.strip() for sentence in raw_sentences if len(sentence.strip()) > 30]

