"""Simple financial market data collector."""

from __future__ import annotations

import logging
from io import StringIO

from industry_intelligence_agent.models import FinancialIndicator
from industry_intelligence_agent.utils.http import fetch_text

logger = logging.getLogger(__name__)


def collect_price_indicators(ticker: str, timeout: int = 15) -> list[FinancialIndicator]:
    """Fetch basic price indicators from Stooq daily CSV data.

    This is intentionally simple. For interview use, explain it as a placeholder
    that can later be replaced with a paid data provider or internal data mart.
    """
    if not ticker:
        return []

    import pandas as pd

    symbol = ticker.lower()
    if "." not in symbol:
        symbol = f"{symbol}.us"

    url = f"https://stooq.com/q/d/l/?s={symbol}&i=d"
    logger.info("Fetching price history: %s", url)

    try:
        csv_text = fetch_text(url, timeout=timeout)
        prices = pd.read_csv(StringIO(csv_text))
    except Exception as exc:
        logger.warning("Could not fetch financial data for %s: %s", ticker, exc)
        return []

    if prices.empty or "Close" not in prices.columns:
        return []

    latest = prices.iloc[-1]
    first = prices.iloc[0]
    latest_close = float(latest["Close"])
    first_close = float(first["Close"])
    period_return = ((latest_close / first_close) - 1) * 100 if first_close else 0

    return [
        FinancialIndicator("latest_close_price", round(latest_close, 2), str(latest["Date"]), url),
        FinancialIndicator("observed_period_return_pct", round(period_return, 2), f"{first['Date']} to {latest['Date']}", url),
        FinancialIndicator("observed_trading_days", int(len(prices)), f"{first['Date']} to {latest['Date']}", url),
    ]

