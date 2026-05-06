"""KRI evidence extraction for human review.

KRI means Key Risk Indicator. This module does not produce final risk scores.
It extracts evidence sentences from annual reports, company profiles, and news
so a human analyst can review them.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any

import pandas as pd

try:
    from src.text_cleaner import clean_text
except ModuleNotFoundError:
    # Allows direct execution with: python src/kri_extractor.py
    from text_cleaner import clean_text


logger = logging.getLogger(__name__)


KRI_COLUMNS = [
    "source_id",
    "company_name",
    "industry",
    "source_type",
    "kri_category",
    "matched_keyword",
    "evidence_sentence",
    "severity_hint",
    "risk_score_hint",
]


HIGH_SEVERITY_WORDS = [
    "significant",
    "material",
    "severe",
    "critical",
    "default",
    "sharp decline",
    "liquidity pressure",
    "high leverage",
    "insolvency",
    "bankruptcy",
]

MEDIUM_SEVERITY_WORDS = [
    "decline",
    "shortage",
    "delay",
    "loss",
    "uncertainty",
    "pressure",
    "disruption",
    "volatile",
    "weakness",
    "increase",
    "decrease",
    "risk",
    "challenge",
]


def load_kri_dictionary() -> dict[str, list[str]]:
    """Return the MVP keyword dictionary by KRI category."""
    return {
        "liquidity risk": [
            "liquidity",
            "working capital",
            "current ratio",
            "short-term funding",
            "cash reserves",
            "credit facility",
            "debt maturity",
        ],
        "leverage risk": [
            "leverage",
            "debt",
            "borrowings",
            "interest expense",
            "debt-to-equity",
            "covenant",
            "financing cost",
        ],
        "profitability risk": [
            "profitability",
            "gross margin",
            "operating margin",
            "net income",
            "earnings decline",
            "pricing pressure",
            "cost increase",
        ],
        "cash flow risk": [
            "cash flow",
            "operating cash",
            "free cash flow",
            "cash used in operations",
            "capital expenditure",
            "capex",
        ],
        "inventory risk": [
            "inventory",
            "obsolete inventory",
            "inventory write-down",
            "stock level",
            "excess inventory",
            "inventory turnover",
        ],
        "receivables risk": [
            "accounts receivable",
            "receivables",
            "bad debt",
            "allowance for doubtful accounts",
            "collection period",
            "credit loss",
        ],
        "supply chain risk": [
            "supply chain",
            "supplier",
            "shortage",
            "logistics",
            "procurement",
            "raw material",
            "delivery delay",
        ],
        "customer concentration risk": [
            "customer concentration",
            "major customer",
            "largest customer",
            "key customer",
            "customer dependency",
            "top five customers",
        ],
        "regulatory risk": [
            "regulation",
            "regulatory",
            "compliance",
            "lawsuit",
            "litigation",
            "sanction",
            "fine",
            "license",
        ],
        "geopolitical risk": [
            "geopolitical",
            "trade restriction",
            "export control",
            "tariff",
            "cross-strait",
            "war",
            "political tension",
        ],
        "cyber / digital risk": [
            "cyber",
            "cybersecurity",
            "data breach",
            "information security",
            "system outage",
            "ransomware",
            "digital risk",
        ],
        "ESG / sustainability risk": [
            "esg",
            "sustainability",
            "carbon",
            "emissions",
            "climate",
            "renewable energy",
            "water usage",
            "labor rights",
        ],
    }


def split_into_sentences(text: str) -> list[str]:
    """Split text into sentence-like evidence units."""
    cleaned = clean_text(text)
    if not cleaned:
        return []

    # Handles normal sentence punctuation and keeps common report text readable.
    sentences = re.split(r"(?<=[.!?])\s+|\n+", cleaned)
    return [sentence.strip() for sentence in sentences if len(sentence.strip()) >= 20]


def extract_kri_mentions(
    text: str | list[str] | list[dict[str, Any]],
    source_id: str,
    source_type: str,
    company_name: str | None = None,
    industry: str | None = None,
) -> pd.DataFrame:
    """Extract KRI evidence mentions from text or text chunks.

    `text` can be:
    - one long string
    - a list of strings
    - a list of dictionaries with a `text` field, such as annual report chunks
    """
    dictionary = load_kri_dictionary()
    sentences = _collect_sentences(text)
    records: list[dict[str, str]] = []

    for sentence in sentences:
        lower_sentence = sentence.lower()

        for category, keywords in dictionary.items():
            for keyword in keywords:
                if keyword.lower() in lower_sentence:
                    records.append(
                        {
                            "source_id": source_id,
                            "company_name": company_name or "",
                            "industry": industry or "",
                            "source_type": source_type,
                            "kri_category": category,
                            "matched_keyword": keyword,
                            "evidence_sentence": sentence,
                            "severity_hint": _severity_hint(sentence),
                            "risk_score_hint": 0,
                        }
                    )
                    # One matched keyword per category per sentence is enough
                    # for review and avoids noisy duplicate rows.
                    break

    df = pd.DataFrame(records, columns=KRI_COLUMNS)
    return score_kri_mentions(df)


def score_kri_mentions(df: pd.DataFrame) -> pd.DataFrame:
    """Add severity and numeric risk hints for analyst prioritization.

    This is evidence extraction, not a final credit decision. A human analyst
    should review source quality, materiality, and financial data before using
    the output in any recommendation.
    """
    if df.empty:
        return pd.DataFrame(columns=KRI_COLUMNS)

    result = df.copy()
    result["severity_hint"] = result["evidence_sentence"].apply(_severity_hint)
    result["risk_score_hint"] = result["severity_hint"].map({"high": 3, "medium": 2, "low": 1}).fillna(1).astype(int)
    for column in KRI_COLUMNS:
        if column not in result.columns:
            result[column] = ""
    return result[KRI_COLUMNS].reset_index(drop=True)


def save_kri_results(df: pd.DataFrame, output_path: str | Path) -> None:
    """Save KRI evidence results to CSV or JSON."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    if path.suffix.lower() == ".json":
        df.to_json(path, orient="records", force_ascii=False, indent=2)
        logger.info("Saved %s KRI rows to JSON: %s", len(df), path)
        return

    df.to_csv(path, index=False, encoding="utf-8-sig")
    logger.info("Saved %s KRI rows to CSV: %s", len(df), path)


def extract_kri_signals(text: str) -> dict[str, list[str]]:
    """Backward-compatible summary helper used by the starter report generator."""
    df = extract_kri_mentions(text, source_id="unknown", source_type="text")

    risks = df["evidence_sentence"].drop_duplicates().head(10).tolist() if not df.empty else []

    return {
        "risks": risks,
        "opportunities": [],
        "kpi_kri_signals": risks,
    }


def _collect_sentences(text: str | list[str] | list[dict[str, Any]]) -> list[str]:
    """Normalize supported input formats into a sentence list."""
    if isinstance(text, str):
        return split_into_sentences(text)

    sentences: list[str] = []
    for item in text:
        if isinstance(item, str):
            sentences.extend(split_into_sentences(item))
        elif isinstance(item, dict):
            sentences.extend(split_into_sentences(str(item.get("text", ""))))

    return sentences


def _severity_hint(sentence: str) -> str:
    """Assign a simple severity hint based on wording.

    This is not final risk scoring. It only helps analysts prioritize evidence.
    """
    lower_sentence = sentence.lower()

    if any(word in lower_sentence for word in HIGH_SEVERITY_WORDS):
        return "high"

    if any(word in lower_sentence for word in MEDIUM_SEVERITY_WORDS):
        return "medium"

    return "low"


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )

    sample_text = """
    The company faces material liquidity risk due to working capital pressure.
    Inventory levels increased because of weak customer demand.
    Cybersecurity threats and data breach incidents may disrupt operations.
    ESG requirements on carbon emissions may increase compliance costs.
    """

    results = extract_kri_mentions(sample_text, source_id="demo_report", source_type="annual_report")
    print(results)
