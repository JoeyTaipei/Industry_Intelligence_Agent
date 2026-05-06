"""Consulting-style summarization helpers.

The default mode is rule-based and does not require an LLM. If `use_llm=True`
and `OPENAI_API_KEY` exists, the module can call an OpenAI model using only the
provided evidence.

Guardrails used throughout:
- Do not make unsupported claims.
- Cite source titles, URLs, or source IDs when available.
- Distinguish facts from interpretation.
- Say when evidence is insufficient.
"""

from __future__ import annotations

import json
import os
from typing import Any

import pandas as pd

try:
    from src.text_cleaner import clean_text, split_sentences
except ModuleNotFoundError:
    # Allows direct execution with: python src/summarizer.py
    from text_cleaner import clean_text, split_sentences


BRIEF_SECTIONS = [
    "Executive Summary",
    "Business Model",
    "Industry Trends",
    "Key Risk Indicators",
    "Recent News Signals",
    "Financial / Operating Signals",
    "Digital Transformation Opportunities",
    "Recommended Follow-up Questions",
]


def summarize_text(text: str, max_sentences: int = 5) -> str:
    """Return the first useful sentences from a body of text."""
    useful_sentences = [sentence for sentence in split_sentences(text) if len(sentence) > 40]
    if not useful_sentences:
        return "Evidence is insufficient for a supported summary."
    return " ".join(useful_sentences[:max_sentences])


def summarize_documents(documents: list[dict], max_sentences: int = 8) -> str:
    """Summarize multiple documents into one short paragraph.

    This function is kept for compatibility with the starter report generator.
    """
    combined_text = " ".join(str(document.get("text", "")) for document in documents)
    return summarize_text(combined_text, max_sentences=max_sentences)


def summarize_company_profile(company_profile: dict[str, Any] | None) -> str:
    """Summarize company registry/basic information with citations."""
    if not company_profile:
        return "- Fact: Company profile evidence is insufficient."

    name = company_profile.get("company_name") or "Unknown company"
    ticker = company_profile.get("ticker") or "N/A"
    industry = company_profile.get("industry") or "N/A"
    source = company_profile.get("source") or "company registry"
    address = company_profile.get("address") or "N/A"
    chairman = company_profile.get("chairman") or "N/A"
    general_manager = company_profile.get("general_manager") or "N/A"
    listing_date = company_profile.get("listing_date") or "N/A"

    return "\n".join(
        [
            f"- Fact: {name} operates in `{industry}` and is identified by ticker `{ticker}`. Source: {source}.",
            f"- Fact: Registered address: {address}. Source: {source}.",
            f"- Fact: Chairman: {chairman}; General manager: {general_manager}; Listing date: {listing_date}. Source: {source}.",
        ]
    )


def summarize_news_articles(news_df: pd.DataFrame | None) -> str:
    """Summarize recent news signals from a news DataFrame."""
    if news_df is None or news_df.empty:
        return "- Fact: Recent news evidence is insufficient."

    lines: list[str] = []
    for _, row in news_df.head(8).iterrows():
        title = clean_text(row.get("title", "Untitled article"))
        source = clean_text(row.get("source", "unknown source"))
        date = clean_text(row.get("published_date", ""))
        summary = clean_text(row.get("summary", ""))
        evidence = summarize_text(summary or title, max_sentences=1)
        citation = _citation(title=title, source=source, source_id=row.get("url", ""))
        date_text = f" Published: {date}." if date else ""
        lines.append(f"- Fact: {evidence}{date_text} Citation: {citation}.")

    return "\n".join(lines)


def summarize_kri_evidence(kri_df: pd.DataFrame | None) -> str:
    """Summarize extracted KRI evidence by category and severity."""
    if kri_df is None or kri_df.empty:
        return "- Fact: KRI evidence is insufficient."

    lines: list[str] = []
    grouped = kri_df.groupby("kri_category", dropna=False)

    for category, group in grouped:
        severity_order = {"high": 3, "medium": 2, "low": 1}
        group = group.copy()
        group["severity_rank"] = group["severity_hint"].map(severity_order).fillna(0)
        top_rows = group.sort_values("severity_rank", ascending=False).head(3)

        evidence_items = []
        for _, row in top_rows.iterrows():
            sentence = clean_text(row.get("evidence_sentence", ""))
            keyword = row.get("matched_keyword", "")
            source_id = row.get("source_id", "unknown")
            severity = row.get("severity_hint", "low")
            evidence_items.append(
                f"{severity} signal for `{keyword}`: {sentence} (source ID: {source_id})"
            )

        lines.append(f"- Fact: {category}: " + " | ".join(evidence_items))

    return "\n".join(lines)


def generate_industry_brief(input_data: dict[str, Any], use_llm: bool = False) -> str:
    """Generate a consulting-style industry brief.

    Expected `input_data` keys can include:
    - `industry`
    - `company_profile`
    - `news_df`
    - `kri_df`
    - `trend_notes`
    - `annual_report_chunks`
    - `financial_indicators`
    """
    if use_llm and _can_use_llm():
        return _generate_llm_brief(input_data, brief_type="industry")

    return _generate_rule_based_brief(input_data, brief_type="industry")


def generate_company_brief(input_data: dict[str, Any], use_llm: bool = False) -> str:
    """Generate a consulting-style company brief."""
    if use_llm and _can_use_llm():
        return _generate_llm_brief(input_data, brief_type="company")

    return _generate_rule_based_brief(input_data, brief_type="company")


def _generate_rule_based_brief(input_data: dict[str, Any], brief_type: str) -> str:
    """Build structured markdown using only provided evidence."""
    company_profile = input_data.get("company_profile") or {}
    news_df = _ensure_dataframe(input_data.get("news_df"))
    kri_df = _ensure_dataframe(input_data.get("kri_df"))
    trend_notes = input_data.get("trend_notes") or {}
    annual_report_chunks = input_data.get("annual_report_chunks") or []
    financial_indicators = input_data.get("financial_indicators") or []

    company_name = company_profile.get("company_name") or input_data.get("company_name") or "Target company"
    industry = input_data.get("industry") or trend_notes.get("industry") or company_profile.get("industry") or "Target industry"
    title = f"{company_name} Company Brief" if brief_type == "company" else f"{industry} Industry Brief"

    sections = {
        "Executive Summary": _executive_summary(input_data, brief_type),
        "Business Model": summarize_company_profile(company_profile),
        "Industry Trends": _summarize_trend_notes(trend_notes),
        "Key Risk Indicators": summarize_kri_evidence(kri_df),
        "Recent News Signals": summarize_news_articles(news_df),
        "Financial / Operating Signals": _summarize_financial_signals(financial_indicators, annual_report_chunks),
        "Digital Transformation Opportunities": _summarize_digital_opportunities(trend_notes),
        "Recommended Follow-up Questions": _recommended_questions(input_data),
    }

    markdown_lines = [f"# {title}", ""]
    for section in BRIEF_SECTIONS:
        markdown_lines.append(f"## {section}")
        markdown_lines.append(sections.get(section) or "- Evidence is insufficient.")
        markdown_lines.append("")

    markdown_lines.append("> Guardrail: This brief summarizes only provided evidence. Interpretations are marked as interpretation and should be validated before decision-making.")
    return "\n".join(markdown_lines).strip()


def _generate_llm_brief(input_data: dict[str, Any], brief_type: str) -> str:
    """Generate a markdown brief with an LLM using strict evidence guardrails."""
    evidence_json = _input_data_to_json(input_data)
    prompt = _build_llm_prompt(evidence_json, brief_type)

    try:
        from openai import OpenAI
    except ImportError:
        return _generate_rule_based_brief(input_data, brief_type)

    try:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a careful consulting analyst. Use only provided evidence.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
        )
        return response.choices[0].message.content or _generate_rule_based_brief(input_data, brief_type)
    except Exception:
        return _generate_rule_based_brief(input_data, brief_type)


def _build_llm_prompt(evidence_json: str, brief_type: str) -> str:
    """Create a simple, guarded prompt for LLM summarization."""
    return f"""
Create a consulting-style {brief_type} brief in structured markdown.

Use exactly these sections:
1. Executive Summary
2. Business Model
3. Industry Trends
4. Key Risk Indicators
5. Recent News Signals
6. Financial / Operating Signals
7. Digital Transformation Opportunities
8. Recommended Follow-up Questions

Rules:
- Only summarize the evidence provided below.
- Do not invent facts, numbers, companies, risks, or sources.
- If evidence is insufficient for a section, write: "Evidence is insufficient."
- Cite source titles, URLs, or source IDs wherever available.
- Clearly label facts as "Fact:" and judgment as "Interpretation:".
- Keep the writing concise and useful for a consulting interview brief.

Evidence JSON:
{evidence_json}
""".strip()


def _executive_summary(input_data: dict[str, Any], brief_type: str) -> str:
    """Create a short rule-based executive summary."""
    profile = input_data.get("company_profile") or {}
    trend_notes = input_data.get("trend_notes") or {}
    kri_df = _ensure_dataframe(input_data.get("kri_df"))
    news_df = _ensure_dataframe(input_data.get("news_df"))

    company = profile.get("company_name") or input_data.get("company_name") or "the target company"
    industry = input_data.get("industry") or trend_notes.get("industry") or profile.get("industry") or "the target industry"

    facts = [
        f"- Fact: This {brief_type} brief covers {company} in {industry}.",
        f"- Fact: Provided evidence includes {len(news_df)} news articles and {len(kri_df)} KRI evidence rows.",
    ]

    if trend_notes.get("main_trends"):
        facts.append(f"- Interpretation: The most visible trend signal is: {trend_notes['main_trends'][0]}")
    else:
        facts.append("- Fact: Industry trend evidence is insufficient.")

    return "\n".join(facts)


def _summarize_trend_notes(trend_notes: dict[str, Any]) -> str:
    """Summarize industry trend notes."""
    if not trend_notes:
        return "- Fact: Industry trend evidence is insufficient."

    lines: list[str] = []
    for label, key in [
        ("Main trend", "main_trends"),
        ("Growth driver", "growth_drivers"),
        ("Risk", "risks"),
        ("Key company", "key_companies"),
        ("Data indicator", "data_indicators"),
    ]:
        values = trend_notes.get(key) or []
        for value in values[:5]:
            lines.append(f"- Fact: {label}: {value}. Source: trend notes.")

    return "\n".join(lines) if lines else "- Fact: Industry trend evidence is insufficient."


def _summarize_financial_signals(
    financial_indicators: list[dict[str, Any]] | dict[str, Any],
    annual_report_chunks: list[dict[str, Any]],
) -> str:
    """Summarize financial and operating signals from provided evidence."""
    lines: list[str] = []

    if isinstance(financial_indicators, dict):
        financial_indicators = [financial_indicators]

    for indicator in financial_indicators[:8]:
        name = indicator.get("name") or indicator.get("metric") or "indicator"
        value = indicator.get("value", "N/A")
        period = indicator.get("period", "N/A")
        source = indicator.get("source", "provided financial indicators")
        lines.append(f"- Fact: {name}: {value} for {period}. Source: {source}.")

    for chunk in annual_report_chunks[:3]:
        text = clean_text(str(chunk.get("text", "")))
        if text:
            source_id = chunk.get("chunk_id") or chunk.get("source_id") or "annual report chunk"
            lines.append(f"- Fact: {summarize_text(text, max_sentences=1)} Source ID: {source_id}.")

    return "\n".join(lines) if lines else "- Fact: Financial and operating evidence is insufficient."


def _summarize_digital_opportunities(trend_notes: dict[str, Any]) -> str:
    """Summarize possible digital transformation opportunities."""
    opportunities = trend_notes.get("digital_transformation_opportunities", []) if trend_notes else []
    if not opportunities:
        return "- Fact: Digital transformation opportunity evidence is insufficient."

    return "\n".join(
        f"- Interpretation: Potential digital opportunity based on evidence: {item}. Source: trend notes."
        for item in opportunities[:6]
    )


def _recommended_questions(input_data: dict[str, Any]) -> str:
    """Generate follow-up questions based on missing or incomplete evidence."""
    questions = [
        "- What source confirms the latest revenue, margin, cash flow, and working capital trends?",
        "- Which risks are material according to management, and which are only external news signals?",
        "- Which indicators should be tracked monthly as KRI dashboard metrics?",
    ]

    if not input_data.get("trend_notes"):
        questions.append("- Which consulting, government, or industry reports can validate the industry trend view?")
    if _ensure_dataframe(input_data.get("news_df")).empty:
        questions.append("- What recent news sources should be added to improve market signal coverage?")
    if _ensure_dataframe(input_data.get("kri_df")).empty:
        questions.append("- Which annual report sections should be reviewed to extract KRI evidence?")

    return "\n".join(questions)


def _citation(title: str = "", source: str = "", source_id: str = "") -> str:
    """Build a readable citation string from available source fields."""
    parts = [part for part in [title, source, source_id] if part]
    return " | ".join(parts) if parts else "source not provided"


def _ensure_dataframe(value: Any) -> pd.DataFrame:
    """Convert supported table-like inputs to a DataFrame."""
    if isinstance(value, pd.DataFrame):
        return value
    if isinstance(value, list):
        return pd.DataFrame(value)
    return pd.DataFrame()


def _input_data_to_json(input_data: dict[str, Any]) -> str:
    """Convert mixed input data into JSON for the LLM prompt."""
    safe_data: dict[str, Any] = {}

    for key, value in input_data.items():
        if isinstance(value, pd.DataFrame):
            safe_data[key] = value.head(20).to_dict(orient="records")
        else:
            safe_data[key] = value

    return json.dumps(safe_data, ensure_ascii=False, indent=2, default=str)


def _can_use_llm() -> bool:
    """Return True only when the user asked for LLM mode and an API key exists."""
    return bool(os.getenv("OPENAI_API_KEY"))


if __name__ == "__main__":
    sample_input = {
        "company_profile": {
            "company_name": "Taiwan Semiconductor Manufacturing Company",
            "ticker": "2330.TW",
            "industry": "Semiconductors",
            "source": "sample company registry",
        },
        "trend_notes": {
            "industry": "Semiconductors",
            "main_trends": ["AI server demand is increasing semiconductor capacity needs"],
            "digital_transformation_opportunities": ["AI analytics for supply chain planning"],
        },
    }

    print(generate_company_brief(sample_input, use_llm=False))
