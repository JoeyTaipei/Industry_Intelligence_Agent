"""Industry trend document reader and rule-based extractor.

This module reads industry trend sources such as consulting reports,
government reports, PDF reports, and web articles. The MVP uses transparent
keyword rules first, so it works without an LLM. Later, the extraction function
can be replaced or enhanced with an OpenAI summarizer.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any

try:
    from src.text_cleaner import clean_text, limit_words, split_sentences
except ModuleNotFoundError:
    # Allows this file to run directly with: python src/industry_trend_reader.py
    from text_cleaner import clean_text, limit_words, split_sentences


logger = logging.getLogger(__name__)


TREND_KEYWORDS = [
    "trend",
    "shift",
    "adoption",
    "automation",
    "ai",
    "cloud",
    "digital",
    "sustainability",
    "supply chain",
    "reshoring",
]

GROWTH_DRIVER_KEYWORDS = [
    "growth",
    "demand",
    "driver",
    "investment",
    "government policy",
    "subsidy",
    "export",
    "capacity",
    "innovation",
]

RISK_KEYWORDS = [
    "risk",
    "uncertainty",
    "competition",
    "regulation",
    "geopolitical",
    "inflation",
    "shortage",
    "cybersecurity",
    "margin pressure",
]

DATA_INDICATOR_KEYWORDS = [
    "revenue",
    "cagr",
    "market size",
    "gross margin",
    "operating margin",
    "capex",
    "market share",
    "growth rate",
    "inventory",
    "working capital",
    "%",
    "billion",
    "million",
]

DIGITAL_TRANSFORMATION_KEYWORDS = [
    "digital transformation",
    "ai",
    "machine learning",
    "automation",
    "analytics",
    "data platform",
    "cloud",
    "erp",
    "crm",
    "rpa",
    "iot",
]

COMMON_COMPANY_NAMES = [
    "TSMC",
    "MediaTek",
    "Quanta",
    "Wistron",
    "Foxconn",
    "Hon Hai",
    "Cathay Financial",
    "Fubon Financial",
    "E.SUN Bank",
    "NVIDIA",
    "AMD",
    "Intel",
    "Apple",
    "Microsoft",
    "Amazon",
    "Google",
    "Samsung",
]


def read_local_text(path: str | Path) -> str:
    """Read a local TXT or Markdown file and return cleaned text."""
    file_path = Path(path)
    if not file_path.exists():
        logger.warning("Local text file does not exist: %s", file_path)
        return ""

    try:
        text = file_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        text = file_path.read_text(encoding="utf-8-sig", errors="ignore")
    except Exception as exc:
        logger.exception("Could not read local text file %s: %s", file_path, exc)
        return ""

    return clean_text(text)


def read_pdf_report(path: str | Path) -> str:
    """Read a local PDF report and return cleaned text."""
    pdf_path = Path(path)
    if not pdf_path.exists():
        logger.warning("PDF report does not exist: %s", pdf_path)
        return ""

    try:
        import pdfplumber
    except ImportError:
        logger.error("pdfplumber is not installed. Run: pip install -r requirements.txt")
        return ""

    text_parts: list[str] = []

    try:
        with pdfplumber.open(str(pdf_path)) as pdf:
            for page in pdf.pages:
                text_parts.append(page.extract_text() or "")
    except Exception as exc:
        logger.exception("Could not read PDF report %s: %s", pdf_path, exc)
        return ""

    return clean_text(" ".join(text_parts))


def fetch_article_text(url: str, timeout: int = 15) -> str:
    """Fetch a web article URL and return visible cleaned text."""
    try:
        import requests
        from bs4 import BeautifulSoup
    except ImportError:
        logger.error("requests and beautifulsoup4 are required. Run: pip install -r requirements.txt")
        return ""

    try:
        response = requests.get(url, timeout=timeout, headers={"User-Agent": "IndustryIntelligenceAgent/0.1"})
        response.raise_for_status()
    except Exception as exc:
        logger.exception("Could not fetch article URL %s: %s", url, exc)
        return ""

    soup = BeautifulSoup(response.text, "html.parser")
    for tag in soup(["script", "style", "noscript", "nav", "footer"]):
        tag.decompose()

    return clean_text(soup.get_text(" "))


def extract_industry_trend_sections(text: str) -> dict[str, list[str]]:
    """Extract trend notes using simple keyword rules.

    The return keys match the JSON structure needed by the industry brief. Each
    value is a list of short evidence sentences.
    """
    cleaned = clean_text(text)

    return {
        "main_trends": _extract_keyword_sentences(cleaned, TREND_KEYWORDS),
        "growth_drivers": _extract_keyword_sentences(cleaned, GROWTH_DRIVER_KEYWORDS),
        "risks": _extract_keyword_sentences(cleaned, RISK_KEYWORDS),
        "key_companies": _extract_key_companies(cleaned),
        "data_indicators": _extract_data_indicators(cleaned),
        "digital_transformation_opportunities": _extract_keyword_sentences(
            cleaned,
            DIGITAL_TRANSFORMATION_KEYWORDS,
        ),
    }


def convert_to_trend_notes(text: str, industry: str) -> dict[str, Any]:
    """Convert raw report/article text into JSON-ready industry trend notes."""
    sections = extract_industry_trend_sections(text)

    return {
        "industry": industry,
        "main_trends": sections["main_trends"],
        "growth_drivers": sections["growth_drivers"],
        "risks": sections["risks"],
        "key_companies": sections["key_companies"],
        "data_indicators": sections["data_indicators"],
        "digital_transformation_opportunities": sections[
            "digital_transformation_opportunities"
        ],
    }


def read_source_to_trend_notes(source: str | Path, industry: str) -> dict[str, Any]:
    """Read a PDF, TXT/MD file, or URL and return structured trend notes."""
    source_text = str(source)

    if source_text.startswith(("http://", "https://")):
        text = fetch_article_text(source_text)
    else:
        path = Path(source)
        if path.suffix.lower() == ".pdf":
            text = read_pdf_report(path)
        else:
            text = read_local_text(path)

    return convert_to_trend_notes(text, industry=industry)


def read_local_trend_file(file_path: str | Path) -> dict[str, Any]:
    """Backward-compatible wrapper for local TXT/MD trend files."""
    path = Path(file_path)
    text = read_local_text(path)

    return {
        "source_type": "industry_trend",
        "file_name": path.name,
        "file_path": str(path),
        "text": limit_words(text, max_words=2000),
    }


def read_web_trend_page(url: str, timeout: int = 15) -> dict[str, Any]:
    """Backward-compatible wrapper for web trend pages."""
    text = fetch_article_text(url, timeout=timeout)

    return {
        "source_type": "industry_trend",
        "url": url,
        "text": limit_words(text, max_words=2000),
    }


def _extract_keyword_sentences(
    text: str,
    keywords: list[str],
    max_items: int = 7,
) -> list[str]:
    """Return sentences containing any keyword."""
    results: list[str] = []

    for sentence in split_sentences(text):
        lower_sentence = sentence.lower()
        if any(keyword.lower() in lower_sentence for keyword in keywords):
            results.append(sentence)

        if len(results) >= max_items:
            break

    return results


def _extract_key_companies(text: str, max_items: int = 10) -> list[str]:
    """Find company names mentioned in the text.

    The MVP checks common names first, then adds simple capitalized-name
    patterns. This is not perfect, but it is useful for early portfolio demos.
    """
    found: list[str] = []

    for company in COMMON_COMPANY_NAMES:
        if re.search(rf"\b{re.escape(company)}\b", text, flags=re.IGNORECASE):
            found.append(company)

    capitalized_candidates = re.findall(
        r"\b[A-Z][A-Za-z&\.]+(?:\s+[A-Z][A-Za-z&\.]+){0,3}\b",
        text,
    )

    for candidate in capitalized_candidates:
        if candidate in found:
            continue
        if _looks_like_company_name(candidate):
            found.append(candidate)
        if len(found) >= max_items:
            break

    return found[:max_items]


def _extract_data_indicators(text: str, max_items: int = 10) -> list[str]:
    """Extract sentences that mention quantitative or financial indicators."""
    indicator_sentences = _extract_keyword_sentences(text, DATA_INDICATOR_KEYWORDS, max_items=max_items)

    # Also capture compact numeric phrases such as "CAGR of 8%" or "$10 billion".
    numeric_phrases = re.findall(
        r"\b(?:CAGR|revenue|market size|growth|margin|capex|market share)?[^.]{0,40}"
        r"(?:\d+(?:\.\d+)?%|\$?\d+(?:\.\d+)?\s*(?:million|billion|trillion))",
        text,
        flags=re.IGNORECASE,
    )

    for phrase in numeric_phrases:
        cleaned_phrase = clean_text(phrase)
        if cleaned_phrase and cleaned_phrase not in indicator_sentences:
            indicator_sentences.append(cleaned_phrase)
        if len(indicator_sentences) >= max_items:
            break

    return indicator_sentences[:max_items]


def _looks_like_company_name(candidate: str) -> bool:
    """Heuristic check for likely company names."""
    company_terms = ["Inc", "Corp", "Company", "Co", "Ltd", "Bank", "Financial", "Semiconductor"]
    if any(term.lower() in candidate.lower() for term in company_terms):
        return True
    return candidate in COMMON_COMPANY_NAMES


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )

    sample_text = """
    The Taiwan semiconductor industry is seeing strong AI demand and cloud investment.
    TSMC and MediaTek are key companies in the ecosystem. Market size is expected to
    grow at a CAGR of 8%. However, geopolitical risk and capacity shortage remain
    important concerns. Digital transformation opportunities include AI analytics,
    supply chain automation, and cloud-based data platforms.
    """

    notes = convert_to_trend_notes(sample_text, industry="Taiwan semiconductor industry")
    print(notes)
