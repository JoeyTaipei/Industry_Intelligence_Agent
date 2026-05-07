"""News collection helpers for the Streamlit MVP.

The app uses Google News RSS because it is free, simple, and good enough for a
first-pass industry intelligence workflow. If RSS fetching fails, callers can
fall back to `generate_sample_news` so the demo continues gracefully.
"""

from __future__ import annotations

import logging
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
from urllib.parse import quote_plus

import pandas as pd

try:
    from src.text_cleaner import clean_text
except ModuleNotFoundError:
    from text_cleaner import clean_text


logger = logging.getLogger(__name__)

ARTICLE_COLUMNS = [
    "source",
    "title",
    "url",
    "published_date",
    "summary",
    "keyword",
    "company_name",
    "industry",
    "source_type",
]


def build_google_news_rss_url(query: str, language: str = "en-US", region: str = "US") -> str:
    """Build a Google News RSS URL for a search query."""
    encoded_query = quote_plus(clean_text(query))
    return (
        "https://news.google.com/rss/search"
        f"?q={encoded_query}&hl={language}&gl={region}&ceid={region}:{language.split('-')[0]}"
    )


def fetch_google_news_rss(
    query: str,
    max_articles: int = 10,
    language: str = "en-US",
    region: str = "US",
    company_name: str = "",
    industry: str = "",
) -> pd.DataFrame:
    """Fetch recent Google News RSS articles and return a normalized DataFrame."""
    query = clean_text(query)
    if not query:
        return pd.DataFrame(columns=ARTICLE_COLUMNS)

    try:
        import feedparser
    except ImportError:
        logger.warning("feedparser is not installed.")
        return pd.DataFrame(columns=ARTICLE_COLUMNS)

    url = build_google_news_rss_url(query, language=language, region=region)
    try:
        feed = feedparser.parse(url)
    except Exception as exc:
        logger.warning("Google News RSS fetch failed: %s", exc)
        return pd.DataFrame(columns=ARTICLE_COLUMNS)

    if getattr(feed, "bozo", False):
        logger.warning("Google News RSS returned a malformed feed for query: %s", query)

    records: list[dict[str, Any]] = []
    for entry in getattr(feed, "entries", [])[:max_articles]:
        records.append(
            {
                "source": clean_text(getattr(entry, "source", {}).get("title", "") if isinstance(getattr(entry, "source", {}), dict) else "Google News"),
                "title": clean_text(getattr(entry, "title", "")),
                "url": clean_text(getattr(entry, "link", "")),
                "published_date": clean_text(getattr(entry, "published", "") or getattr(entry, "updated", "")),
                "summary": clean_text(getattr(entry, "summary", "")),
                "keyword": query,
                "company_name": company_name,
                "industry": industry,
                "source_type": "google_news_rss",
            }
        )

    return clean_news_dataframe(pd.DataFrame(records))


def clean_news_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize news rows to the app's expected schema."""
    if df is None or df.empty:
        return pd.DataFrame(columns=ARTICLE_COLUMNS)

    result = df.copy()
    for column in ARTICLE_COLUMNS:
        if column not in result.columns:
            result[column] = ""

    for column in ARTICLE_COLUMNS:
        result[column] = result[column].fillna("").astype(str).map(clean_text)

    result["source"] = result["source"].replace("", "Google News")
    result["source_type"] = result["source_type"].replace("", "google_news_rss")
    result = result.drop_duplicates(subset=["url", "title"]).reset_index(drop=True)
    return result[ARTICLE_COLUMNS]


def generate_sample_news(
    output_path: str | Path | None = None,
    company_name: str = "Apple",
    industry: str = "consumer electronics semiconductor supply chain",
    keyword: str = "Apple tariff supply chain China Taiwan semiconductor",
) -> pd.DataFrame:
    """Generate sample rows so the app still works when RSS/network fails."""
    rows = [
        {
            "source": "Sample News",
            "title": f"{company_name} supply chain faces tariff and China exposure questions",
            "url": "https://example.com/sample/apple-tariff-supply-chain",
            "published_date": "2026-05-01",
            "summary": "Consumer electronics companies may face tariff uncertainty, cost pressure, and supply chain disruption linked to China, Taiwan, and semiconductor component sourcing.",
            "keyword": keyword,
            "company_name": company_name,
            "industry": industry,
            "source_type": "sample_news",
        },
        {
            "source": "Sample News",
            "title": "Semiconductor shortages could delay product launches",
            "url": "https://example.com/sample/semiconductor-shortage",
            "published_date": "2026-04-26",
            "summary": "A shortage of advanced chips and raw materials could delay production schedules and increase costs for global electronics brands.",
            "keyword": keyword,
            "company_name": company_name,
            "industry": industry,
            "source_type": "sample_news",
        },
        {
            "source": "Sample News",
            "title": "Cybersecurity and supplier concentration remain board-level risks",
            "url": "https://example.com/sample/cyber-supplier-risk",
            "published_date": "2026-04-20",
            "summary": "Companies with concentrated suppliers in Asia may face operational disruption, cybersecurity risk, and regulatory pressure across the United States, EU, China, and Taiwan.",
            "keyword": keyword,
            "company_name": company_name,
            "industry": industry,
            "source_type": "sample_news",
        },
    ]
    df = clean_news_dataframe(pd.DataFrame(rows))
    if output_path:
        save_articles(df, output_path)
    return df


def load_sample_news(csv_path: str | Path) -> pd.DataFrame:
    """Load sample news CSV data and standardize expected columns."""
    path = Path(csv_path)
    if not path.exists():
        logger.warning("Sample news CSV does not exist, generating sample data: %s", path)
        return generate_sample_news(path)

    try:
        df = pd.read_csv(path, dtype=str).fillna("")
    except Exception as exc:
        logger.warning("Could not load sample news CSV %s: %s", path, exc)
        return pd.DataFrame(columns=ARTICLE_COLUMNS)
    return clean_news_dataframe(df)


def fetch_rss_articles(
    keyword: str,
    rss_sources: list[dict[str, str]] | list[str] | None = None,
    max_articles: int = 20,
) -> pd.DataFrame:
    """Backward-compatible wrapper that now prefers Google News RSS."""
    _ = rss_sources
    return fetch_google_news_rss(keyword, max_articles=max_articles)


def load_rss_sources(config_path: str | Path) -> list[dict[str, str]]:
    """Backward-compatible config loader for older scripts."""
    path = Path(config_path)
    if not path.exists():
        return []
    try:
        import yaml

        config = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception:
        return []
    sources = config.get("sources", [])
    return sources if isinstance(sources, list) else []


def filter_articles_by_keyword(df: pd.DataFrame, keyword: str) -> pd.DataFrame:
    """Filter articles whose title or summary contains any keyword term."""
    df = clean_news_dataframe(df)
    terms = [term.lower() for term in clean_text(keyword).split() if term.strip()]
    if df.empty or not terms:
        return df
    searchable = (df["title"] + " " + df["summary"]).str.lower()
    return df[searchable.apply(lambda text: any(term in text for term in terms))].reset_index(drop=True)


def save_articles(df: pd.DataFrame, output_path: str | Path) -> None:
    """Save news rows to CSV or JSON."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    clean_df = clean_news_dataframe(df)
    if path.suffix.lower() == ".json":
        clean_df.to_json(path, orient="records", force_ascii=False, indent=2)
    else:
        clean_df.to_csv(path, index=False, encoding="utf-8-sig")


@dataclass
class NewsArticle:
    """Structured article object used by older wrappers."""

    title: str
    url: str
    summary: str
    published_at: str = ""
    source: str = "rss"

    def to_dict(self) -> dict:
        return asdict(self)


def collect_news_from_rss(query: str, feeds: list[str], max_articles: int = 10) -> list[NewsArticle]:
    """Backward-compatible list-returning wrapper."""
    _ = feeds
    df = fetch_google_news_rss(query, max_articles=max_articles)
    return [
        NewsArticle(
            title=row.get("title", ""),
            url=row.get("url", ""),
            summary=row.get("summary", ""),
            published_at=row.get("published_date", ""),
            source=row.get("source", "Google News"),
        )
        for row in df.to_dict(orient="records")
    ]
