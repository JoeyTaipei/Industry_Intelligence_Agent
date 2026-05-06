"""SQLite storage for collected documents and generated briefs."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from industry_intelligence_agent.models import SourceDocument


def init_db(db_path: str | Path) -> None:
    """Create database tables if they do not exist."""
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_type TEXT NOT NULL,
                title TEXT NOT NULL,
                url TEXT,
                text TEXT,
                published_at TEXT,
                collected_at TEXT,
                metadata_json TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS briefs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                generated_at TEXT,
                company TEXT,
                ticker TEXT,
                industry TEXT,
                brief_json TEXT NOT NULL
            )
            """
        )


def save_documents(db_path: str | Path, documents: list[SourceDocument]) -> None:
    """Persist source documents to SQLite."""
    if not documents:
        return

    with sqlite3.connect(db_path) as conn:
        conn.executemany(
            """
            INSERT INTO documents (
                source_type, title, url, text, published_at, collected_at, metadata_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    doc.source_type,
                    doc.title,
                    doc.url,
                    doc.text,
                    doc.published_at,
                    doc.collected_at,
                    json.dumps(doc.metadata, ensure_ascii=False),
                )
                for doc in documents
            ],
        )


def save_brief(db_path: str | Path, brief: dict) -> None:
    """Persist generated brief to SQLite."""
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO briefs (generated_at, company, ticker, industry, brief_json)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                brief.get("generated_at", ""),
                brief.get("company", ""),
                brief.get("ticker", ""),
                brief.get("industry", ""),
                json.dumps(brief, ensure_ascii=False),
            ),
        )

