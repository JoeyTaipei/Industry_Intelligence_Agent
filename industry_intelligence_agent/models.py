"""Shared data models for the Industry Intelligence Agent."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


def utc_now_iso() -> str:
    """Return a consistent timestamp for saved records."""
    return datetime.now(timezone.utc).isoformat()


@dataclass
class SourceDocument:
    """A normalized source document from news, reports, PDFs, or web pages."""

    source_type: str
    title: str
    url: str = ""
    text: str = ""
    published_at: str = ""
    collected_at: str = field(default_factory=utc_now_iso)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CompanyProfile:
    """Basic company registry information."""

    company_name: str
    ticker: str = ""
    industry: str = ""
    country: str = ""
    website: str = ""
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class FinancialIndicator:
    """A simple financial or operating indicator."""

    name: str
    value: str | float | int
    period: str = ""
    source: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

