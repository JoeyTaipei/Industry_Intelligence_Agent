"""Build a structured industry brief from collected evidence."""

from __future__ import annotations

from industry_intelligence_agent.analysis.financial_metrics import indicators_to_dicts, indicator_summary
from industry_intelligence_agent.analysis.summarizer import (
    extract_kpi_signals,
    extract_opportunities,
    extract_risks,
    extract_trends,
    summarize_text,
)
from industry_intelligence_agent.models import CompanyProfile, FinancialIndicator, SourceDocument, utc_now_iso


def generate_brief(
    company: str = "",
    ticker: str = "",
    industry: str = "",
    profile: CompanyProfile | None = None,
    documents: list[SourceDocument] | None = None,
    indicators: list[FinancialIndicator] | None = None,
) -> dict:
    """Generate a structured brief using simple transparent heuristics."""
    documents = documents or []
    indicators = indicators or []

    combined_text = " ".join(doc.text for doc in documents if doc.text)
    effective_company = company or (profile.company_name if profile else "")
    effective_ticker = ticker or (profile.ticker if profile else "")
    effective_industry = industry or (profile.industry if profile else "")

    business_model = profile.description if profile and profile.description else summarize_text(combined_text, 2)

    return {
        "generated_at": utc_now_iso(),
        "company": effective_company,
        "ticker": effective_ticker,
        "industry": effective_industry,
        "company_profile": profile.to_dict() if profile else {},
        "business_model_summary": business_model,
        "industry_trends": extract_trends(combined_text),
        "risks": extract_risks(combined_text),
        "opportunities": extract_opportunities(combined_text),
        "kpi_and_kri_signals": extract_kpi_signals(combined_text),
        "financial_indicators": indicators_to_dicts(indicators),
        "source_count": len(documents),
        "sources": [
            {
                "source_type": doc.source_type,
                "title": doc.title,
                "url": doc.url,
                "published_at": doc.published_at,
            }
            for doc in documents
        ],
    }


def brief_to_markdown(brief: dict) -> str:
    """Render the structured brief as interview-friendly Markdown."""
    title = brief.get("company") or brief.get("industry") or "Industry Brief"
    lines = [
        f"# {title} Industry Brief",
        "",
        f"Generated: {brief.get('generated_at', '')}",
        "",
        "## Snapshot",
        f"- Company: {brief.get('company') or 'N/A'}",
        f"- Ticker: {brief.get('ticker') or 'N/A'}",
        f"- Industry: {brief.get('industry') or 'N/A'}",
        f"- Sources reviewed: {brief.get('source_count', 0)}",
        "",
        "## Business Model",
        brief.get("business_model_summary") or "No business model summary available.",
        "",
        "## Industry Trends",
        *_bullet_lines(brief.get("industry_trends", [])),
        "",
        "## Risks",
        *_bullet_lines(brief.get("risks", [])),
        "",
        "## Opportunities",
        *_bullet_lines(brief.get("opportunities", [])),
        "",
        "## KPI / KRI Signals",
        *_bullet_lines(brief.get("kpi_and_kri_signals", [])),
        "",
        "## Financial Indicators",
        indicator_summary_from_brief(brief),
        "",
        "## Sources",
        *_source_lines(brief.get("sources", [])),
        "",
    ]
    return "\n".join(lines)


def indicator_summary_from_brief(brief: dict) -> str:
    indicators = [
        FinancialIndicator(
            name=item.get("name", ""),
            value=item.get("value", ""),
            period=item.get("period", ""),
            source=item.get("source", ""),
        )
        for item in brief.get("financial_indicators", [])
    ]
    return indicator_summary(indicators)


def _bullet_lines(items: list[str]) -> list[str]:
    return [f"- {item}" for item in items] or ["- Not enough evidence collected in this run."]


def _source_lines(sources: list[dict]) -> list[str]:
    if not sources:
        return ["- No sources collected."]
    return [f"- [{source.get('source_type')}] {source.get('title')} - {source.get('url')}" for source in sources]

