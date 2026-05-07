"""Annual report PDF reader for the Streamlit MVP."""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any


logger = logging.getLogger(__name__)

SECTION_ANCHORS: dict[str, list[str]] = {
    "business_overview": [
        r"\bbusiness overview\b",
        r"\boverview of business\b",
        r"\bour business\b",
        r"\bbusiness\b",
        r"\bcompany overview\b",
    ],
    "risk_factors": [
        r"\brisk factors\b",
        r"\bitem 1a\.?\s+risk factors\b",
        r"\bprincipal risks\b",
        r"\brisk management\b",
        r"\bkey risks\b",
    ],
    "financial_overview": [
        r"\bfinancial overview\b",
        r"\bfinancial highlights\b",
        r"\bselected financial data\b",
        r"\bfinancial performance\b",
        r"\bresults of operations\b",
    ],
    "management_discussion": [
        r"\bmanagement discussion\b",
        r"\bmanagement's discussion\b",
        r"\bmanagements discussion\b",
        r"\bmd&a\b",
        r"\bmanagement analysis\b",
    ],
}

SECTION_PATTERNS = SECTION_ANCHORS


def extract_text_from_pdf(pdf_path: str | Path) -> str:
    """Extract text from a local or uploaded PDF path using pdfplumber, then PyMuPDF."""
    path = Path(pdf_path)
    if not path.exists():
        logger.warning("PDF file does not exist: %s", path)
        return ""

    text = _extract_with_pdfplumber(path)
    if text.strip():
        return text

    text = _extract_with_pymupdf(path)
    if text.strip():
        return text

    logger.warning("No readable text extracted from PDF: %s", path)
    return ""


def clean_annual_report_text(text: str) -> str:
    """Clean PDF text while preserving useful section breaks."""
    if not text:
        return ""
    cleaned = text.replace("\x00", " ")
    cleaned = re.sub(r"(\w)-\s*\n\s*(\w)", r"\1\2", cleaned)
    cleaned = re.sub(r"\r\n|\r", "\n", cleaned)
    cleaned = re.sub(r"[ \t]+", " ", cleaned)
    cleaned = re.sub(r"(?m)^\s*\d+\s*$", "", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    cleaned = re.sub(r" *\n *", "\n", cleaned)
    return cleaned.strip()


def extract_sections_by_anchors(text: str, max_words: int = 2500) -> dict[str, str]:
    """Find annual-report sections by simple heading anchors.

    Risk factors and MD&A are prioritized by callers because they contain the
    most useful risk language for KRI extraction.
    """
    cleaned = clean_annual_report_text(text)
    sections = {section: "" for section in SECTION_ANCHORS}
    if not cleaned:
        return sections

    lower_text = cleaned.lower()
    matches: list[tuple[int, str]] = []
    for section, anchors in SECTION_ANCHORS.items():
        positions = []
        for anchor in anchors:
            match = re.search(anchor, lower_text, flags=re.IGNORECASE)
            if match:
                positions.append(match.start())
        if positions:
            matches.append((min(positions), section))

    matches.sort(key=lambda item: item[0])
    for index, (start, section) in enumerate(matches):
        end = matches[index + 1][0] if index + 1 < len(matches) else len(cleaned)
        sections[section] = _limit_words(cleaned[start:end], max_words)

    return sections


def chunk_text(text: str, chunk_size: int = 900, overlap: int = 120) -> list[dict[str, Any]]:
    """Split text into overlapping chunks for extraction and review."""
    cleaned = clean_annual_report_text(text)
    if not cleaned:
        return []
    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than 0.")
    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("overlap must be non-negative and smaller than chunk_size.")

    words = cleaned.split()
    chunks: list[dict[str, Any]] = []
    start = 0
    chunk_id = 1
    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunks.append(
            {
                "chunk_id": chunk_id,
                "start_word": start,
                "end_word": end,
                "text": " ".join(words[start:end]),
            }
        )
        if end >= len(words):
            break
        start = end - overlap
        chunk_id += 1
    return chunks


def read_annual_report_pdf(
    pdf_path: str | Path,
    chunk_size: int = 900,
    overlap: int = 120,
) -> dict[str, Any]:
    """Read a PDF and return extraction-ready annual report data."""
    raw_text = extract_text_from_pdf(pdf_path)
    cleaned_text = clean_annual_report_text(raw_text)
    sections = extract_sections_by_anchors(cleaned_text)
    prioritized_text = "\n\n".join(
        part
        for part in [
            sections.get("risk_factors", ""),
            sections.get("management_discussion", ""),
            sections.get("business_overview", ""),
            sections.get("financial_overview", ""),
        ]
        if part
    ) or cleaned_text

    return {
        "pdf_path": str(pdf_path),
        "raw_text": raw_text,
        "cleaned_text": cleaned_text,
        "sections": sections,
        "prioritized_text": prioritized_text,
        "chunks": chunk_text(prioritized_text, chunk_size=chunk_size, overlap=overlap),
        "metadata": {
            "character_count": len(cleaned_text),
            "word_count": len(cleaned_text.split()),
            "has_risk_factors": bool(sections.get("risk_factors")),
            "has_management_discussion": bool(sections.get("management_discussion")),
        },
    }


def build_annual_report_evidence_rows(
    annual_report_data: dict[str, Any],
    company_name: str = "",
    industry: str = "",
) -> list[dict[str, Any]]:
    """Build section-level evidence rows for CSV/Excel export."""
    rows: list[dict[str, Any]] = []
    priority = {
        "risk_factors": 1,
        "management_discussion": 2,
        "business_overview": 3,
        "financial_overview": 4,
    }
    sections = annual_report_data.get("sections", {}) or {}
    for section, text in sorted(sections.items(), key=lambda item: priority.get(item[0], 99)):
        if not text:
            continue
        rows.append(
            {
                "company_name": company_name,
                "industry": industry,
                "section": section,
                "priority": priority.get(section, 99),
                "evidence_text": _limit_words(text, 220),
                "source_type": "annual_report",
                "source_id": section,
            }
        )
    return rows


def save_chunks_to_json(chunks: list[dict[str, Any]], output_path: str | Path) -> None:
    """Save chunks to JSON for debugging or downstream review."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(chunks, ensure_ascii=False, indent=2), encoding="utf-8")


def identify_annual_report_sections(text: str) -> dict[str, str]:
    """Backward-compatible alias for older modules."""
    return extract_sections_by_anchors(text)


def read_pdf_text(pdf_path: str | Path, max_pages: int | None = None) -> str:
    """Backward-compatible wrapper."""
    _ = max_pages
    return clean_annual_report_text(extract_text_from_pdf(pdf_path))


def read_annual_report(pdf_path: str | Path, max_pages: int | None = None) -> dict[str, Any]:
    """Backward-compatible wrapper."""
    _ = max_pages
    return read_annual_report_pdf(pdf_path)


def generate_sample_annual_report_text(company_name: str, industry: str) -> str:
    """Small sample used by old pipeline paths when no PDF is available."""
    company = company_name or "the company"
    sector = industry or "the industry"
    return f"""
Business Overview
{company} operates in {sector}. Demand may grow with new products and services.

Risk Factors
The company may face tariff risk, supplier concentration, supply chain disruption,
cybersecurity risk, cost pressure, regulatory uncertainty, and liquidity pressure.

Management Discussion
Management monitors operational disruption, raw material availability, demand
volatility, leverage risk, and profitability risk.
""".strip()


def _extract_with_pdfplumber(path: Path) -> str:
    try:
        import pdfplumber
    except ImportError:
        return ""
    try:
        with pdfplumber.open(str(path)) as pdf:
            return "\n\n".join(page.extract_text() or "" for page in pdf.pages)
    except Exception as exc:
        logger.warning("pdfplumber extraction failed for %s: %s", path, exc)
        return ""


def _extract_with_pymupdf(path: Path) -> str:
    try:
        import fitz
    except ImportError:
        return ""
    try:
        with fitz.open(str(path)) as doc:
            return "\n\n".join(page.get_text("text") for page in doc)
    except Exception as exc:
        logger.warning("PyMuPDF extraction failed for %s: %s", path, exc)
        return ""


def _limit_words(text: str, max_words: int) -> str:
    words = clean_annual_report_text(text).split()
    return " ".join(words[:max_words])
