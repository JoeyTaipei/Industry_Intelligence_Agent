"""Local company registry lookup."""

from __future__ import annotations

from pathlib import Path

from industry_intelligence_agent.config import resolve_path
from industry_intelligence_agent.models import CompanyProfile


def lookup_company(
    company_name: str = "",
    ticker: str = "",
    registry_csv_path: str | Path = "data/company_registry_sample.csv",
) -> CompanyProfile | None:
    """Find a company in the local registry CSV by name or ticker."""
    import pandas as pd

    path = resolve_path(registry_csv_path)
    if not path.exists():
        return None

    registry = pd.read_csv(path).fillna("")
    if ticker:
        match = registry[registry["ticker"].str.lower() == ticker.lower()]
        if not match.empty:
            return _row_to_profile(match.iloc[0])

    if company_name:
        query = company_name.lower()
        match = registry[
            registry["company_name"].str.lower().str.contains(query, regex=False)
        ]
        if not match.empty:
            return _row_to_profile(match.iloc[0])

    return None


def _row_to_profile(row) -> CompanyProfile:
    return CompanyProfile(
        company_name=row.get("company_name", ""),
        ticker=row.get("ticker", ""),
        industry=row.get("industry", ""),
        country=row.get("country", ""),
        website=row.get("website", ""),
        description=row.get("description", ""),
    )

