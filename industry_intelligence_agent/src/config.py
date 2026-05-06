"""Configuration helpers for the Industry Intelligence Agent.

This module keeps file paths and project settings in one place. Later, you can
extend it to load API keys, database settings, or model settings from `.env`.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class ProjectConfig:
    """Simple configuration object used by the pipeline."""

    project_root: Path
    database_path: Path
    raw_data_dir: Path
    processed_data_dir: Path
    reports_dir: Path
    exports_dir: Path
    news_feeds: list[str]


def get_project_root() -> Path:
    """Return the root folder for this starter project."""
    return Path(__file__).resolve().parents[1]


def load_config(config_path: str | Path | None = None) -> ProjectConfig:
    """Load project settings from JSON and environment variables."""
    project_root = get_project_root()
    default_config_path = project_root / "configs" / "example_config.json"
    path = Path(config_path) if config_path else default_config_path

    settings: dict[str, Any] = {}
    if path.exists():
        with path.open("r", encoding="utf-8") as file:
            settings = json.load(file)

    data_dir = project_root / "data"
    database_path = Path(
        os.getenv("DATABASE_PATH", settings.get("database_path", "data/processed/intelligence.db"))
    )
    if not database_path.is_absolute():
        database_path = project_root / database_path

    return ProjectConfig(
        project_root=project_root,
        database_path=database_path,
        raw_data_dir=data_dir / "raw",
        processed_data_dir=data_dir / "processed",
        reports_dir=data_dir / "reports",
        exports_dir=data_dir / "exports",
        news_feeds=settings.get("news_feeds", []),
    )

