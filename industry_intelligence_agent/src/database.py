"""Lightweight SQLite database layer for industry intelligence data.

SQLite is a good MVP choice because it is built into Python and stores data in
one local file. This module keeps the schema simple and uses pandas DataFrames
for easy loading, exporting, and dashboard work.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


DEFAULT_DB_PATH = Path(__file__).resolve().parents[1] / "data" / "processed" / "intelligence.db"
_DB_PATH = DEFAULT_DB_PATH


def init_db(db_path: str | Path = DEFAULT_DB_PATH) -> None:
    """Initialize the SQLite database and create all MVP tables."""
    global _DB_PATH

    _DB_PATH = Path(db_path)
    _DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    with _connect() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS companies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_id TEXT,
                ticker TEXT,
                company_name TEXT,
                industry TEXT,
                address TEXT,
                unified_business_number TEXT,
                chairman TEXT,
                general_manager TEXT,
                listing_date TEXT,
                source TEXT,
                source_url TEXT,
                source_file TEXT,
                created_at TEXT
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS news_articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT,
                title TEXT,
                url TEXT,
                published_date TEXT,
                summary TEXT,
                keyword TEXT,
                company_or_industry TEXT,
                source_url TEXT,
                created_at TEXT
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS annual_report_chunks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_id TEXT,
                company_or_industry TEXT,
                chunk_id TEXT,
                text TEXT,
                source_file TEXT,
                source_url TEXT,
                metadata_json TEXT,
                created_at TEXT
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS industry_trends (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                industry TEXT,
                category TEXT,
                item TEXT,
                source_url TEXT,
                source_file TEXT,
                created_at TEXT
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS kri_mentions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_id TEXT,
                company_or_industry TEXT,
                kri_category TEXT,
                matched_keyword TEXT,
                evidence_sentence TEXT,
                severity_hint TEXT,
                source_type TEXT,
                source_url TEXT,
                source_file TEXT,
                created_at TEXT
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS generated_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                report_type TEXT,
                company_name TEXT,
                ticker TEXT,
                industry TEXT,
                report_markdown TEXT,
                report_json TEXT,
                source_file TEXT,
                created_at TEXT
            )
            """
        )


def insert_companies(df: pd.DataFrame) -> None:
    """Insert company registry rows into the `companies` table."""
    if df is None or df.empty:
        return

    rows = _prepare_dataframe(
        df,
        [
            "company_id",
            "ticker",
            "company_name",
            "industry",
            "address",
            "unified_business_number",
            "chairman",
            "general_manager",
            "listing_date",
            "source",
            "source_url",
            "source_file",
        ],
    )
    _insert_dataframe("companies", rows)


def insert_news_articles(df: pd.DataFrame) -> None:
    """Insert collected news articles into the `news_articles` table."""
    if df is None or df.empty:
        return

    rows = _prepare_dataframe(
        df,
        [
            "source",
            "title",
            "url",
            "published_date",
            "summary",
            "keyword",
            "company_or_industry",
            "source_url",
        ],
    )
    rows["source_url"] = rows["source_url"].where(rows["source_url"] != "", rows["url"])
    _insert_dataframe("news_articles", rows)


def insert_annual_report_chunks(chunks: list[dict[str, Any]]) -> None:
    """Insert annual report chunks into the `annual_report_chunks` table."""
    if not chunks:
        return

    records: list[dict[str, Any]] = []
    for chunk in chunks:
        metadata = {
            key: value
            for key, value in chunk.items()
            if key
            not in {
                "source_id",
                "company_or_industry",
                "chunk_id",
                "text",
                "source_file",
                "source_url",
            }
        }
        records.append(
            {
                "source_id": chunk.get("source_id", ""),
                "company_or_industry": chunk.get("company_or_industry", ""),
                "chunk_id": str(chunk.get("chunk_id", "")),
                "text": chunk.get("text", ""),
                "source_file": chunk.get("source_file", ""),
                "source_url": chunk.get("source_url", ""),
                "metadata_json": json.dumps(metadata, ensure_ascii=False),
            }
        )

    rows = pd.DataFrame(records)
    _insert_dataframe("annual_report_chunks", rows)


def insert_industry_trends(trend_json: dict[str, Any]) -> None:
    """Insert industry trend notes into the `industry_trends` table."""
    if not trend_json:
        return

    industry = trend_json.get("industry", "")
    source_url = trend_json.get("source_url", "")
    source_file = trend_json.get("source_file", "")
    records: list[dict[str, Any]] = []

    for category, value in trend_json.items():
        if category in {"industry", "source_url", "source_file"}:
            continue

        values = value if isinstance(value, list) else [value]
        for item in values:
            if item:
                records.append(
                    {
                        "industry": industry,
                        "category": category,
                        "item": str(item),
                        "source_url": source_url,
                        "source_file": source_file,
                    }
                )

    if records:
        _insert_dataframe("industry_trends", pd.DataFrame(records))


def insert_kri_mentions(df: pd.DataFrame) -> None:
    """Insert extracted KRI evidence rows into the `kri_mentions` table."""
    if df is None or df.empty:
        return

    rows = _prepare_dataframe(
        df,
        [
            "source_id",
            "company_or_industry",
            "kri_category",
            "matched_keyword",
            "evidence_sentence",
            "severity_hint",
            "source_type",
            "source_url",
            "source_file",
        ],
    )
    _insert_dataframe("kri_mentions", rows)


def insert_generated_report(
    report_json: dict[str, Any],
    report_markdown: str = "",
    report_type: str = "company_industry_brief",
    source_file: str = "",
) -> None:
    """Insert a generated Markdown/JSON report into the database."""
    report_json = report_json or {}
    company_profile = report_json.get("company_profile", {}) or {}

    rows = pd.DataFrame(
        [
            {
                "report_type": report_type,
                "company_name": company_profile.get("company_name", report_json.get("company_name", "")),
                "ticker": company_profile.get("ticker", report_json.get("ticker", "")),
                "industry": report_json.get("industry", company_profile.get("industry", "")),
                "report_markdown": report_markdown,
                "report_json": json.dumps(report_json, ensure_ascii=False, default=str),
                "source_file": source_file,
            }
        ]
    )
    _insert_dataframe("generated_reports", rows)


def get_company_by_name(name: str) -> pd.DataFrame:
    """Return company rows whose name contains the supplied text."""
    query = f"%{name or ''}%"
    return _read_sql(
        """
        SELECT *
        FROM companies
        WHERE LOWER(company_name) LIKE LOWER(?)
           OR LOWER(ticker) = LOWER(?)
           OR LOWER(company_id) = LOWER(?)
        ORDER BY created_at DESC
        """,
        [query, name or "", name or ""],
    )


def get_recent_news(company_or_industry: str) -> pd.DataFrame:
    """Return recent news rows related to a company or industry keyword."""
    query = f"%{company_or_industry or ''}%"
    return _read_sql(
        """
        SELECT *
        FROM news_articles
        WHERE LOWER(company_or_industry) LIKE LOWER(?)
           OR LOWER(keyword) LIKE LOWER(?)
           OR LOWER(title) LIKE LOWER(?)
           OR LOWER(summary) LIKE LOWER(?)
        ORDER BY COALESCE(published_date, created_at) DESC
        """,
        [query, query, query, query],
    )


def get_kri_mentions(company_or_industry: str) -> pd.DataFrame:
    """Return KRI evidence rows related to a company or industry keyword."""
    query = f"%{company_or_industry or ''}%"
    return _read_sql(
        """
        SELECT *
        FROM kri_mentions
        WHERE LOWER(company_or_industry) LIKE LOWER(?)
           OR LOWER(source_id) LIKE LOWER(?)
           OR LOWER(evidence_sentence) LIKE LOWER(?)
        ORDER BY created_at DESC
        """,
        [query, query, query],
    )


def initialize_database(database_path: str | Path) -> None:
    """Backward-compatible alias for `init_db`."""
    init_db(database_path)


def save_report_to_database(database_path: str | Path, report: dict) -> None:
    """Backward-compatible helper used by the starter pipeline."""
    init_db(database_path)
    insert_generated_report(report_json=report)


def _connect() -> sqlite3.Connection:
    """Open a SQLite connection to the configured database path."""
    _DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(_DB_PATH)


def _created_at() -> str:
    """Return a UTC timestamp for inserted rows."""
    return datetime.now(timezone.utc).isoformat()


def _prepare_dataframe(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    """Ensure a DataFrame has exactly the expected columns plus created_at."""
    rows = df.copy()
    for column in columns:
        if column not in rows.columns:
            rows[column] = ""

    rows = rows[columns].fillna("")
    rows["created_at"] = _created_at()
    return rows


def _insert_dataframe(table_name: str, df: pd.DataFrame) -> None:
    """Append a DataFrame to a SQLite table."""
    if df.empty:
        return

    rows = df.copy()
    if "created_at" not in rows.columns:
        rows["created_at"] = _created_at()

    with _connect() as connection:
        rows.to_sql(table_name, connection, if_exists="append", index=False)


def _read_sql(sql: str, params: list[Any]) -> pd.DataFrame:
    """Read a SQL query into a DataFrame."""
    with _connect() as connection:
        return pd.read_sql_query(sql, connection, params=params)


if __name__ == "__main__":
    db_path = Path("data/processed/example_intelligence.db")
    init_db(db_path)

    sample_companies = pd.DataFrame(
        [
            {
                "company_id": "2330",
                "ticker": "2330.TW",
                "company_name": "Taiwan Semiconductor Manufacturing Company",
                "industry": "Semiconductors",
                "source": "sample",
            }
        ]
    )
    sample_news = pd.DataFrame(
        [
            {
                "source": "sample RSS",
                "title": "AI server demand supports semiconductor growth",
                "url": "https://example.com/news",
                "published_date": "2026-05-06",
                "summary": "AI demand is increasing advanced chip demand.",
                "keyword": "semiconductor",
                "company_or_industry": "Semiconductors",
            }
        ]
    )
    sample_kri = pd.DataFrame(
        [
            {
                "source_id": "annual_report_chunk_1",
                "company_or_industry": "Semiconductors",
                "kri_category": "supply chain risk",
                "matched_keyword": "shortage",
                "evidence_sentence": "Material shortages may delay production.",
                "severity_hint": "medium",
                "source_type": "annual_report",
            }
        ]
    )

    insert_companies(sample_companies)
    insert_news_articles(sample_news)
    insert_kri_mentions(sample_kri)

    print(get_company_by_name("TSMC"))
    print(get_recent_news("semiconductor"))
    print(get_kri_mentions("semiconductor"))
