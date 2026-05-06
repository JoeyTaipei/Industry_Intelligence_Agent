"""Financial indicator formatting."""

from __future__ import annotations

from industry_intelligence_agent.models import FinancialIndicator


def indicators_to_dicts(indicators: list[FinancialIndicator]) -> list[dict]:
    """Convert indicators to JSON-friendly dictionaries."""
    return [indicator.to_dict() for indicator in indicators]


def indicator_summary(indicators: list[FinancialIndicator]) -> str:
    """Create a compact sentence for Markdown output."""
    if not indicators:
        return "No financial indicators were collected in this run."

    parts = [f"{item.name}: {item.value} ({item.period})" for item in indicators]
    return "; ".join(parts)

