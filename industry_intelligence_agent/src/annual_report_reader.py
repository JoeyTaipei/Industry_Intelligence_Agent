"""Annual report PDF reader for business analysis.

Annual reports are often messy: page headers repeat, line breaks are strange,
and section titles vary by company. This module focuses on a robust MVP:

1. Extract raw text from a local PDF.
2. Clean the text enough for analysis.
3. Identify likely annual report sections using keyword-based anchors.
4. Split text into overlapping chunks for future LLM or search workflows.
5. Return a structured dictionary that is easy to save or pass downstream.
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any


logger = logging.getLogger(__name__)


SECTION_PATTERNS: dict[str, list[str]] = {
    "business_overview": [
        r"\bbusiness overview\b",
        r"\boverview of business\b",
        r"\bour business\b",
        r"\bbusiness model\b",
        r"\bcompany overview\b",
    ],
    "risk_factors": [
        r"\brisk factors\b",
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
        r"\bmd&a\b",
        r"\bmanagement analysis\b",
    ],
    "industry_overview": [
        r"\bindustry overview\b",
        r"\bindustry outlook\b",
        r"\bmarket overview\b",
        r"\bindustry trends\b",
        r"\bmarket environment\b",
    ],
    "future_outlook": [
        r"\bfuture outlook\b",
        r"\boutlook\b",
        r"\bfuture plans\b",
        r"\bstrategy and outlook\b",
        r"\bgrowth strategy\b",
    ],
}


def generate_sample_annual_report_text(company_name: str, industry: str) -> str:
    """Generate sample annual-report-style text for an offline MVP demo."""
    company = company_name or "the company"
    sector = industry or "the industry"
    return f"""
Annual Report Demo Text 2026

Business Overview
{company} operates in the {sector} ecosystem. Demand for AI servers, advanced
semiconductors, and high performance computing creates growth opportunities.
The business depends on customer forecasts, supplier readiness, and production
capacity planning.

Risk Factors
Material supplier shortages may delay production and affect delivery schedules.
Customer concentration may increase revenue volatility if major cloud customers
change order plans. Geopolitical uncertainty, export controls, cybersecurity
threats, and energy requirements may create operating risk.

Financial Overview
Inventory levels may increase when production is prepared ahead of confirmed
delivery schedules. Accounts receivable and working capital should be monitored
because large enterprise customers may have different payment terms. Capital
expenditure and cash flow planning are important when demand requires capacity
expansion.

Management Discussion
Management continues to focus on operational resilience, supplier
diversification, production efficiency, data-driven planning, and cybersecurity
readiness.

Industry Outlook
AI infrastructure investment may support long-term demand, but the industry
faces pressure from export controls, component availability, and energy usage.

Future Outlook
Digital tools for demand forecasting, supplier monitoring, working capital
tracking, and KPI dashboards may improve visibility across the value chain.
""".strip()


def extract_text_from_pdf(pdf_path: str | Path) -> str:
    """Extract raw text from a local annual report PDF.

    The function uses `pdfplumber` first because it is beginner-friendly and
    good for text-heavy annual reports. If a PDF is scanned as images, this
    function may return limited text; OCR can be added later as a separate step.
    """
    path = Path(pdf_path)
    if not path.exists():
        logger.error("PDF file does not exist: %s", path)
        return ""

    try:
        import pdfplumber
    except ImportError:
        logger.error("pdfplumber is not installed. Run: pip install -r requirements.txt")
        return ""

    text_parts: list[str] = []

    try:
        with pdfplumber.open(str(path)) as pdf:
            for page_number, page in enumerate(pdf.pages, start=1):
                page_text = page.extract_text() or ""
                if page_text.strip():
                    text_parts.append(page_text)
                else:
                    logger.debug("No text found on page %s of %s", page_number, path.name)
    except Exception as exc:
        logger.exception("Failed to extract text from PDF %s: %s", path, exc)
        return ""

    raw_text = "\n\n".join(text_parts)
    logger.info("Extracted %s characters from %s", len(raw_text), path.name)
    return raw_text


def clean_annual_report_text(text: str) -> str:
    """Clean annual report text while preserving section readability."""
    if not text:
        return ""

    cleaned = text.replace("\x00", " ")

    # Join words split by PDF line hyphenation, such as "manu-\nfacturing".
    cleaned = re.sub(r"(\w)-\s*\n\s*(\w)", r"\1\2", cleaned)

    # Convert repeated newlines to paragraph breaks, then normalize spaces.
    cleaned = re.sub(r"\r\n|\r", "\n", cleaned)
    cleaned = re.sub(r"[ \t]+", " ", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)

    # Remove very common page-number-only lines.
    cleaned = re.sub(r"(?m)^\s*\d+\s*$", "", cleaned)

    # Clean spaces around newlines after removing page numbers.
    cleaned = re.sub(r" *\n *", "\n", cleaned)
    return cleaned.strip()


def chunk_text(text: str, chunk_size: int = 1200, overlap: int = 150) -> list[dict[str, Any]]:
    """Split text into overlapping word chunks.

    Overlap helps preserve context across chunk boundaries. For example, if a
    risk factor starts at the end of one chunk, the next chunk still includes
    enough previous words to remain understandable.
    """
    if not text:
        return []

    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than 0.")
    if overlap < 0:
        raise ValueError("overlap must be 0 or greater.")
    if overlap >= chunk_size:
        raise ValueError("overlap must be smaller than chunk_size.")

    words = text.split()
    chunks: list[dict[str, Any]] = []
    start = 0
    chunk_id = 1

    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunk_words = words[start:end]

        chunks.append(
            {
                "chunk_id": chunk_id,
                "start_word": start,
                "end_word": end,
                "text": " ".join(chunk_words),
            }
        )

        if end == len(words):
            break

        start = end - overlap
        chunk_id += 1

    return chunks


def extract_basic_metadata(text: str) -> dict[str, Any]:
    """Extract basic metadata clues from annual report text.

    This is intentionally heuristic. Annual reports have many formats, so the
    MVP looks for useful hints instead of trying to be perfect.
    """
    cleaned = clean_annual_report_text(text)
    first_page_text = cleaned[:5000]

    year_match = re.search(r"\b(20\d{2}|19\d{2})\b", first_page_text)
    annual_report_match = re.search(
        r"\b(annual report|form 10-k|integrated report|financial report)\b",
        first_page_text,
        flags=re.IGNORECASE,
    )

    company_name = _guess_company_name(first_page_text)
    word_count = len(cleaned.split())

    return {
        "company_name_guess": company_name,
        "report_year_guess": year_match.group(1) if year_match else "",
        "report_type_guess": annual_report_match.group(1) if annual_report_match else "",
        "character_count": len(cleaned),
        "word_count": word_count,
        "has_risk_section": _contains_any_pattern(cleaned, SECTION_PATTERNS["risk_factors"]),
        "has_management_discussion": _contains_any_pattern(
            cleaned, SECTION_PATTERNS["management_discussion"]
        ),
    }


def save_chunks_to_json(chunks: list[dict[str, Any]], output_path: str | Path) -> None:
    """Save section or text chunks to a JSON file."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8") as file:
        json.dump(chunks, file, ensure_ascii=False, indent=2)

    logger.info("Saved %s chunks to %s", len(chunks), path)


def read_annual_report_pdf(
    pdf_path: str | Path,
    chunk_size: int = 1200,
    overlap: int = 150,
) -> dict[str, Any]:
    """Read a PDF annual report and return structured analysis-ready output."""
    path = Path(pdf_path)
    raw_text = extract_text_from_pdf(path)
    cleaned_text = clean_annual_report_text(raw_text)
    sections = identify_annual_report_sections(cleaned_text)
    chunks = chunk_text(cleaned_text, chunk_size=chunk_size, overlap=overlap)
    metadata = extract_basic_metadata(cleaned_text)

    return {
        "pdf_path": str(path),
        "metadata": metadata,
        "raw_text": raw_text,
        "cleaned_text": cleaned_text,
        "sections": sections,
        "chunks": chunks,
    }


def identify_annual_report_sections(text: str) -> dict[str, str]:
    """Identify common annual report sections using keyword anchors.

    The method finds likely section headings, sorts them by position, and takes
    the text between one heading and the next. If a section is not found, its
    value is an empty string.
    """
    sections = {section_name: "" for section_name in SECTION_PATTERNS}
    if not text:
        return sections

    lower_text = text.lower()
    matches: list[tuple[int, str]] = []

    for section_name, patterns in SECTION_PATTERNS.items():
        position = _find_first_pattern_position(lower_text, patterns)
        if position is not None:
            matches.append((position, section_name))

    matches.sort(key=lambda item: item[0])

    for index, (start_position, section_name) in enumerate(matches):
        next_position = matches[index + 1][0] if index + 1 < len(matches) else len(text)
        section_text = text[start_position:next_position].strip()
        sections[section_name] = _limit_section_text(section_text)

    return sections


def read_pdf_text(pdf_path: str | Path, max_pages: int | None = None) -> str:
    """Backward-compatible wrapper that returns cleaned PDF text.

    `max_pages` is accepted for older code. The new MVP reads the full PDF.
    """
    _ = max_pages
    return clean_annual_report_text(extract_text_from_pdf(pdf_path))


def read_annual_report(pdf_path: str | Path, max_pages: int | None = None) -> dict[str, Any]:
    """Backward-compatible wrapper around `read_annual_report_pdf`."""
    _ = max_pages
    return read_annual_report_pdf(pdf_path)


def _contains_any_pattern(text: str, patterns: list[str]) -> bool:
    """Return True if any regex pattern appears in the text."""
    return any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in patterns)


def _find_first_pattern_position(text: str, patterns: list[str]) -> int | None:
    """Find the earliest position of any pattern in text."""
    positions: list[int] = []

    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            positions.append(match.start())

    return min(positions) if positions else None


def _guess_company_name(first_page_text: str) -> str:
    """Guess company name from the first few lines of the report."""
    lines = [line.strip() for line in first_page_text.splitlines() if line.strip()]

    for line in lines[:20]:
        lower_line = line.lower()
        if "annual report" in lower_line or "form 10-k" in lower_line:
            continue
        if 3 <= len(line.split()) <= 10 and len(line) <= 100:
            return line

    return ""


def _limit_section_text(section_text: str, max_words: int = 1800) -> str:
    """Keep extracted sections to a manageable length for MVP analysis."""
    words = section_text.split()
    return " ".join(words[:max_words])


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )

    example_pdf = Path("data/raw/example_annual_report.pdf")
    output_json = Path("data/processed/example_annual_report_chunks.json")

    result = read_annual_report_pdf(example_pdf)
    save_chunks_to_json(result["chunks"], output_json)

    print(f"PDF path: {result['pdf_path']}")
    print(f"Extracted words: {result['metadata'].get('word_count', 0)}")
    print(f"Chunks saved to: {output_json}")
