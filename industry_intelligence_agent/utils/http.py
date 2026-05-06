"""Small HTTP helper shared by collectors and parsers."""

from __future__ import annotations

from industry_intelligence_agent.config import get_user_agent


def fetch_url(url: str, timeout: int = 15) -> bytes:
    """Fetch URL content as bytes and raise clear HTTP errors."""
    import requests

    response = requests.get(
        url,
        timeout=timeout,
        headers={"User-Agent": get_user_agent()},
    )
    response.raise_for_status()
    return response.content


def fetch_text(url: str, timeout: int = 15) -> str:
    """Fetch URL content as decoded text."""
    import requests

    response = requests.get(
        url,
        timeout=timeout,
        headers={"User-Agent": get_user_agent()},
    )
    response.raise_for_status()
    response.encoding = response.encoding or "utf-8"
    return response.text

