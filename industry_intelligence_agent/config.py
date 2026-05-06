"""Configuration loading helpers."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config" / "example_config.json"


def load_env() -> None:
    """Load .env if python-dotenv is installed."""
    try:
        from dotenv import load_dotenv
    except ImportError:
        return

    load_dotenv(PROJECT_ROOT / ".env")


def resolve_path(path_value: str | Path) -> Path:
    """Resolve project-relative paths in config files."""
    path = Path(path_value)
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


def load_config(config_path: str | Path | None = None) -> dict[str, Any]:
    """Load JSON config and fill small defaults."""
    path = resolve_path(config_path) if config_path else DEFAULT_CONFIG_PATH
    with path.open("r", encoding="utf-8") as file:
        config = json.load(file)

    config.setdefault("request_timeout_seconds", 15)
    config.setdefault("max_news_items", 8)
    config.setdefault("news_feeds", [])
    config.setdefault("company_reports", {})
    config.setdefault("industry_reports", {})
    return config


def get_user_agent() -> str:
    """Return a polite user agent for web requests."""
    return os.getenv("USER_AGENT", "IndustryIntelligenceAgent/0.1")

