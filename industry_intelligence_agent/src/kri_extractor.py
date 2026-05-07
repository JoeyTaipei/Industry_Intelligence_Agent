"""KRI evidence extraction for human review.

This module extracts risk evidence from news and annual report text. The
severity score is not a financial model; it is a prioritization hint that helps
human reviewers decide which evidence to validate first.
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
    from text_cleaner import clean_text


logger = logging.getLogger(__name__)

COUNTRIES = [
    "Taiwan",
    "China",
    "United States",
    "U.S.",
    "US",
    "Japan",
    "South Korea",
    "Korea",
    "India",
    "Vietnam",
    "EU",
    "European Union",
    "Germany",
    "Singapore",
    "Malaysia",
    "Thailand",
]

PERCENTAGE_RE = re.compile(r"\b\d+(?:\.\d+)?\s*(?:%|percent)\b", flags=re.IGNORECASE)

HIGH_SEVERITY_WORDS = [
    "material adverse effect",
    "materially adversely affect",
    "significant disruption",
    "significant",
    "critical",
    "severe",
    "sharp decline",
    "default",
    "liquidity pressure",
]

MEDIUM_SEVERITY_WORDS = [
    "uncertain",
    "uncertainty",
    "may",
    "could",
    "risk",
    "pressure",
    "delay",
    "shortage",
    "disruption",
    "volatile",
    "loss",
    "increase cost",
    "cost pressure",
]

KRI_COLUMNS = [
    "source_id",
    "company_name",
    "industry",
    "source_type",
    "published_date",
    "kri_category",
    "matched_keywords",
    "evidence_sentence",
    "detected_countries",
    "detected_percentages",
    "severity_hint",
    "risk_score_hint",
    "recommended_follow_up",
]


def load_kri_dictionary() -> dict[str, list[str]]:
    """Return the MVP keyword dictionary by KRI category."""
    return {
        "geopolitical risk": [
            "geopolitical",
            "war",
            "political tension",
            "cross-strait",
            "sanction",
            "trade restriction",
        ],
        "trade/tariff risk": [
            "tariff",
            "duty",
            "trade war",
            "import restriction",
            "export control",
            "customs",
        ],
        "supply chain risk": [
            "supply chain",
            "supplier",
            "shortage",
            "logistics",
            "procurement",
            "delivery delay",
        ],
        "supplier concentration risk": [
            "supplier concentration",
            "single supplier",
            "sole supplier",
            "key supplier",
            "limited suppliers",
            "depend on suppliers",
        ],
        "raw material risk": [
            "raw material",
            "rare earth",
            "lithium",
            "cobalt",
            "gallium",
            "germanium",
            "semiconductor components",
        ],
        "regulatory risk": [
            "regulatory",
            "regulation",
            "compliance",
            "lawsuit",
            "litigation",
            "fine",
            "license",
        ],
        "cybersecurity risk": [
            "cyber",
            "cybersecurity",
            "data breach",
            "ransomware",
            "information security",
            "system outage",
        ],
        "ESG risk": [
            "esg",
            "sustainability",
            "carbon",
            "emissions",
            "climate",
            "renewable energy",
            "labor rights",
        ],
        "cost pressure risk": [
            "cost pressure",
            "increase cost",
            "cost increase",
            "inflation",
            "gross margin",
            "pricing pressure",
        ],
        "demand risk": [
            "demand",
            "slowdown",
            "weak demand",
            "customer demand",
            "order cancellation",
            "volatile demand",
        ],
        "operational disruption risk": [
            "operational disruption",
            "production disruption",
            "factory shutdown",
            "delay",
            "business interruption",
            "outage",
        ],
        "liquidity risk": [
            "liquidity",
            "working capital",
            "cash reserves",
            "credit facility",
            "short-term funding",
        ],
        "leverage risk": [
            "leverage",
            "debt",
            "borrowings",
            "interest expense",
            "covenant",
            "financing cost",
        ],
        "profitability risk": [
            "profitability",
            "gross margin",
            "operating margin",
            "net income",
            "earnings decline",
            "margin pressure",
        ],
    }


def extract_kri_mentions(
    text: str | list[str] | list[dict[str, Any]] | pd.DataFrame,
    source_id: str,
    source_type: str,
    company_name: str | None = None,
    industry: str | None = None,
) -> pd.DataFrame:
    """Extract KRI evidence from text, annual-report chunks, or news rows."""
    records: list[dict[str, Any]] = []
    dictionary = load_kri_dictionary()

    for item in _iter_evidence_items(text, source_id, source_type, company_name, industry):
        for sentence in split_into_sentences(item["text"]):
            lower_sentence = sentence.lower()
            for category, keywords in dictionary.items():
                matched = [keyword for keyword in keywords if keyword.lower() in lower_sentence]
                if not matched:
                    continue
                severity = _severity_hint(sentence)
                records.append(
                    {
                        "source_id": item["source_id"],
                        "company_name": item["company_name"],
                        "industry": item["industry"],
                        "source_type": item["source_type"],
                        "published_date": item.get("published_date", ""),
                        "kri_category": category,
                        "matched_keywords": ", ".join(dict.fromkeys(matched)),
                        "evidence_sentence": sentence,
                        "detected_countries": ", ".join(_detect_countries(sentence)),
                        "detected_percentages": ", ".join(_detect_percentages(sentence)),
                        "severity_hint": severity,
                        "risk_score_hint": {"high": 3, "medium": 2, "low": 1}[severity],
                        "recommended_follow_up": _recommended_follow_up(category, severity),
                    }
                )

    if not records:
        return pd.DataFrame(columns=KRI_COLUMNS)

    df = pd.DataFrame(records)
    df = df.drop_duplicates(subset=["source_type", "kri_category", "evidence_sentence"]).reset_index(drop=True)
    return df[KRI_COLUMNS]


def score_kri_mentions(df: pd.DataFrame) -> pd.DataFrame:
    """Add severity and risk score hints for human prioritization.

    This is not a financial model. It does not estimate loss, probability, or
    enterprise value impact; it only helps human reviewers triage evidence.
    """
    if df is None or df.empty:
        return pd.DataFrame(columns=KRI_COLUMNS)

    result = df.copy()
    if "evidence_sentence" not in result.columns:
        result["evidence_sentence"] = ""
    result["severity_hint"] = result["evidence_sentence"].apply(_severity_hint)
    result["risk_score_hint"] = result["severity_hint"].map({"high": 3, "medium": 2, "low": 1}).fillna(1).astype(int)
    for column in KRI_COLUMNS:
        if column not in result.columns:
            result[column] = ""
    return result[KRI_COLUMNS].reset_index(drop=True)


def split_into_sentences(text: str) -> list[str]:
    """Split text into sentence-like evidence units."""
    cleaned = clean_text(text)
    if not cleaned:
        return []
    sentences = re.split(r"(?<=[.!?])\s+|\n+", cleaned)
    return [sentence.strip() for sentence in sentences if len(sentence.strip()) >= 25]


def save_kri_results(df: pd.DataFrame, output_path: str | Path) -> None:
    """Save KRI evidence to CSV or JSON."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.suffix.lower() == ".json":
        df.to_json(path, orient="records", force_ascii=False, indent=2)
    else:
        df.to_csv(path, index=False, encoding="utf-8-sig")


def extract_kri_signals(text: str) -> dict[str, list[str]]:
    """Backward-compatible summary helper."""
    df = extract_kri_mentions(text, source_id="unknown", source_type="text")
    risks = df["evidence_sentence"].drop_duplicates().head(10).tolist() if not df.empty else []
    return {"risks": risks, "opportunities": [], "kpi_kri_signals": risks}


def _iter_evidence_items(
    text: str | list[str] | list[dict[str, Any]] | pd.DataFrame,
    source_id: str,
    source_type: str,
    company_name: str | None,
    industry: str | None,
) -> list[dict[str, Any]]:
    if isinstance(text, pd.DataFrame):
        items = []
        for index, row in text.iterrows():
            items.append(
                {
                    "text": f"{row.get('title', '')}. {row.get('summary', '')}",
                    "source_id": row.get("url") or f"{source_id}_{index + 1}",
                    "source_type": row.get("source_type") or source_type,
                    "published_date": row.get("published_date", ""),
                    "company_name": row.get("company_name") or company_name or "",
                    "industry": row.get("industry") or industry or "",
                }
            )
        return items

    if isinstance(text, str):
        return [
            {
                "text": text,
                "source_id": source_id,
                "source_type": source_type,
                "published_date": "",
                "company_name": company_name or "",
                "industry": industry or "",
            }
        ]

    items = []
    for index, item in enumerate(text):
        if isinstance(item, str):
            item_text = item
            item_source_id = f"{source_id}_{index + 1}"
        else:
            item_text = str(item.get("text") or item.get("evidence_text") or "")
            item_source_id = str(item.get("source_id") or item.get("chunk_id") or f"{source_id}_{index + 1}")
        items.append(
            {
                "text": item_text,
                "source_id": item_source_id,
                "source_type": source_type,
                "published_date": "",
                "company_name": company_name or "",
                "industry": industry or "",
            }
        )
    return items


def _detect_countries(sentence: str) -> list[str]:
    found = []
    for country in COUNTRIES:
        if re.search(rf"(?<![A-Za-z]){re.escape(country)}(?![A-Za-z])", sentence, flags=re.IGNORECASE):
            found.append(country)
    return list(dict.fromkeys(found))


def _detect_percentages(sentence: str) -> list[str]:
    return [match.group(0).strip() for match in PERCENTAGE_RE.finditer(sentence)]


def _severity_hint(sentence: str) -> str:
    lower_sentence = sentence.lower()
    if any(word in lower_sentence for word in HIGH_SEVERITY_WORDS):
        return "high"
    if any(word in lower_sentence for word in MEDIUM_SEVERITY_WORDS):
        return "medium"
    return "low"


def _recommended_follow_up(category: str, severity: str) -> str:
    prefix = "優先覆核" if severity == "high" else "納入追蹤"
    return f"{prefix}：請確認 {category} 的來源可靠性、財務影響、管理層是否已揭露，以及是否需要客戶訪談追問。"
