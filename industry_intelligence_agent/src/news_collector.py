"""RSS news collection for business and industry research.

This module collects recent business news for a company, ticker, or industry
keyword. The MVP uses RSS feeds because they are free and easy to parse.

Later, this file can be extended with paid or API-based providers such as:
- NewsAPI
- SerpAPI
- Google Custom Search
- Tavily
"""

from __future__ import annotations

import logging
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from src.text_cleaner import clean_text


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
]


def load_sample_news(csv_path: str | Path) -> pd.DataFrame:
    """Load sample news CSV data and standardize expected columns."""
    path = Path(csv_path)
    if not path.exists():
        logger.warning("Sample news CSV does not exist, generating sample data: %s", path)
        return generate_sample_news(path)

    try:
        df = pd.read_csv(path, dtype=str).fillna("")
    except Exception as exc:
        logger.exception("Could not load sample news CSV %s: %s", path, exc)
        return pd.DataFrame(columns=ARTICLE_COLUMNS)

    for column in ARTICLE_COLUMNS:
        if column not in df.columns:
            df[column] = ""
    return df[ARTICLE_COLUMNS]


def generate_sample_news(output_path: str | Path) -> pd.DataFrame:
    """Generate interview-ready sample news so the MVP works offline."""
    rows = [
        {
            "source": "Demo Business RSS",
            "title": "Taiwan AI server supply chain expands capacity",
            "url": "https://example.com/demo/taiwan-ai-server-capacity",
            "published_date": "2026-04-20",
            "summary": "Quanta, Wistron, and Foxconn are increasing AI server production capacity as cloud customers request more advanced systems.",
            "keyword": "AI server",
            "company_name": "Quanta",
            "industry": "AI server",
        },
        {
            "source": "Demo Technology RSS",
            "title": "Advanced chip demand remains linked to AI accelerator growth",
            "url": "https://example.com/demo/advanced-chip-ai-demand",
            "published_date": "2026-04-18",
            "summary": "TSMC and related semiconductor suppliers see demand signals from AI accelerators, advanced packaging, and high performance computing.",
            "keyword": "TSMC semiconductor AI",
            "company_name": "TSMC",
            "industry": "semiconductor",
        },
        {
            "source": "Demo Finance RSS",
            "title": "Working capital pressure rises as AI hardware orders become more volatile",
            "url": "https://example.com/demo/working-capital-ai-hardware",
            "published_date": "2026-04-15",
            "summary": "AI server manufacturers face inventory planning challenges because demand is strong but order timing can shift quickly across customers.",
            "keyword": "working capital risk",
            "company_name": "Wistron",
            "industry": "manufacturing",
        },
        {
            "source": "Demo Market RSS",
            "title": "Export controls and geopolitical tension remain key semiconductor risks",
            "url": "https://example.com/demo/export-controls-semiconductor-risk",
            "published_date": "2026-04-12",
            "summary": "Taiwan semiconductor companies continue to monitor export controls and geopolitical uncertainty as part of operating risk management.",
            "keyword": "geopolitical risk semiconductor",
            "company_name": "TSMC",
            "industry": "semiconductor",
        },
        {
            "source": "Demo Cyber RSS",
            "title": "Manufacturing digitization increases cybersecurity and production continuity focus",
            "url": "https://example.com/demo/manufacturing-cyber-risk",
            "published_date": "2026-04-09",
            "summary": "As factories connect more equipment and production data, manufacturers are investing in cybersecurity monitoring and operational resilience.",
            "keyword": "cyber digital risk manufacturing",
            "company_name": "Foxconn",
            "industry": "manufacturing",
        },
        {
            "source": "Demo Financial Services RSS",
            "title": "Taiwan banks monitor credit exposure to cyclical technology supply chains",
            "url": "https://example.com/demo/bank-credit-tech-cycle",
            "published_date": "2026-04-05",
            "summary": "Financial institutions are watching credit exposure to technology suppliers because inventory cycles and customer concentration can affect working capital needs.",
            "keyword": "bank credit risk Taiwan",
            "company_name": "Cathay Financial",
            "industry": "financial services",
        },
    ]
    df = pd.DataFrame(rows, columns=ARTICLE_COLUMNS)
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, encoding="utf-8-sig")
    logger.info("Saved sample news data to %s", path)
    return df


@dataclass
class NewsArticle:
    """Structured article object used by the older starter pipeline wrapper."""

    title: str
    url: str
    summary: str
    published_at: str = ""
    source: str = "rss"

    def to_dict(self) -> dict:
        """Convert the article to a dictionary."""
        return asdict(self)


def load_rss_sources(config_path: str | Path) -> list[dict[str, str]]:
    """Load RSS source definitions from a YAML file.

    Expected YAML format:

    sources:
      - name: BBC Business
        category: global business news
        url: https://feeds.bbci.co.uk/news/business/rss.xml
    """
    path = Path(config_path)
    if not path.exists():
        logger.warning("RSS config file does not exist: %s", path)
        return []

    try:
        import yaml
    except ImportError:
        logger.error("PyYAML is not installed. Run: pip install -r requirements.txt")
        return []

    try:
        with path.open("r", encoding="utf-8") as file:
            config = yaml.safe_load(file) or {}
    except Exception as exc:
        logger.exception("Could not read RSS config file: %s", exc)
        return []

    sources = config.get("sources", [])
    if not isinstance(sources, list):
        logger.warning("RSS config should contain a list named 'sources'.")
        return []

    valid_sources: list[dict[str, str]] = []
    for source in sources:
        if not isinstance(source, dict):
            continue

        name = str(source.get("name", "")).strip()
        url = str(source.get("url", "")).strip()
        category = str(source.get("category", "")).strip()

        if not name or not url:
            logger.warning("Skipping RSS source with missing name or url: %s", source)
            continue

        valid_sources.append({"name": name, "url": url, "category": category})

    logger.info("Loaded %s RSS sources from %s", len(valid_sources), path)
    return valid_sources


def fetch_rss_articles(
    keyword: str,
    rss_sources: list[dict[str, str]] | list[str],
    max_articles: int = 20,
) -> pd.DataFrame:
    """Fetch RSS articles and return them as a pandas DataFrame.

    The function accepts either:
    - a list of source dictionaries from `load_rss_sources`
    - a simple list of RSS feed URL strings
    """
    empty_df = pd.DataFrame(columns=ARTICLE_COLUMNS)
    keyword = clean_text(keyword)

    if not keyword:
        logger.warning("No keyword provided. Returning an empty DataFrame.")
        return empty_df

    if not rss_sources:
        logger.warning("No RSS sources provided. Returning an empty DataFrame.")
        return empty_df

    try:
        import feedparser
    except ImportError:
        logger.error("feedparser is not installed. Run: pip install -r requirements.txt")
        return empty_df

    records: list[dict[str, Any]] = []
    normalized_sources = _normalize_sources(rss_sources)

    for source in normalized_sources:
        if len(records) >= max_articles:
            break

        source_name = source["name"]
        feed_url = source["url"]

        try:
            logger.info("Fetching RSS feed '%s': %s", source_name, feed_url)
            feed = feedparser.parse(feed_url)
        except Exception as exc:
            logger.exception("Failed to fetch RSS feed %s: %s", feed_url, exc)
            continue

        if getattr(feed, "bozo", False):
            logger.warning("RSS feed may be malformed: %s", feed_url)

        for entry in getattr(feed, "entries", []):
            title = clean_text(getattr(entry, "title", ""))
            summary = clean_text(getattr(entry, "summary", ""))
            url = clean_text(getattr(entry, "link", ""))
            published_date = clean_text(
                getattr(entry, "published", "") or getattr(entry, "updated", "")
            )

            records.append(
                {
                    "source": source_name,
                    "title": title,
                    "url": url,
                    "published_date": published_date,
                    "summary": summary,
                    "keyword": keyword,
                    "company_name": "",
                    "industry": "",
                }
            )

            if len(records) >= max_articles:
                break

    df = pd.DataFrame(records, columns=ARTICLE_COLUMNS)
    return filter_articles_by_keyword(df, keyword)


def filter_articles_by_keyword(df: pd.DataFrame, keyword: str) -> pd.DataFrame:
    """Filter articles whose title or summary contains any keyword term.

    Example:
    "TSMC AI server" will match articles containing "TSMC", "AI", or "server".
    This broader matching is useful for RSS feeds because exact phrase matches
    can be too strict for a small MVP.
    """
    if df.empty:
        return pd.DataFrame(columns=ARTICLE_COLUMNS)

    keyword = clean_text(keyword)
    terms = [term.lower() for term in keyword.split() if term.strip()]
    if not terms:
        return df

    searchable_text = (
        df["title"].fillna("").astype(str) + " " + df["summary"].fillna("").astype(str)
    ).str.lower()
    mask = searchable_text.apply(lambda text: any(term in text for term in terms))

    for column in ARTICLE_COLUMNS:
        if column not in df.columns:
            df[column] = ""
    filtered_df = df.loc[mask, ARTICLE_COLUMNS].drop_duplicates(subset=["url", "title"])
    return filtered_df.reset_index(drop=True)


def save_articles(df: pd.DataFrame, output_path: str | Path) -> None:
    """Save collected articles to CSV or JSON based on the file extension."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    if path.suffix.lower() == ".json":
        df.to_json(path, orient="records", force_ascii=False, indent=2)
        logger.info("Saved %s articles to JSON: %s", len(df), path)
        return

    df.to_csv(path, index=False, encoding="utf-8-sig")
    logger.info("Saved %s articles to CSV: %s", len(df), path)


def collect_news_from_rss(query: str, feeds: list[str], max_articles: int = 10) -> list[NewsArticle]:
    """Backward-compatible wrapper for the starter pipeline.

    New code should prefer `fetch_rss_articles`, which returns a DataFrame.
    """
    df = fetch_rss_articles(keyword=query, rss_sources=feeds, max_articles=max_articles)
    articles: list[NewsArticle] = []

    for row in df.to_dict(orient="records"):
        articles.append(
            NewsArticle(
                title=row.get("title", ""),
                url=row.get("url", ""),
                summary=row.get("summary", ""),
                published_at=row.get("published_date", ""),
                source=row.get("source", "rss"),
            )
        )

    return articles


def _normalize_sources(rss_sources: list[dict[str, str]] | list[str]) -> list[dict[str, str]]:
    """Convert source strings or dictionaries into one consistent shape."""
    normalized: list[dict[str, str]] = []

    for index, source in enumerate(rss_sources, start=1):
        if isinstance(source, str):
            normalized.append({"name": f"rss_source_{index}", "url": source, "category": ""})
            continue

        if isinstance(source, dict):
            name = str(source.get("name") or f"rss_source_{index}")
            url = str(source.get("url", ""))
            category = str(source.get("category", ""))

            if url:
                normalized.append({"name": name, "url": url, "category": category})

    return normalized


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )

    default_config = Path(__file__).resolve().parents[1] / "configs" / "rss_sources.yaml"
    default_output = Path(__file__).resolve().parents[1] / "data" / "exports" / "news_articles.csv"
    example_keyword = "Taiwan semiconductor industry"

    sources = load_rss_sources(default_config)
    articles_df = fetch_rss_articles(
        keyword=example_keyword,
        rss_sources=sources,
        max_articles=20,
    )
    save_articles(articles_df, default_output)

    print(f"Collected {len(articles_df)} articles for keyword: {example_keyword}")
    print(f"Saved output to: {default_output}")
