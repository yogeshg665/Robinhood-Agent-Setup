"""Live US market-data provider — disabled stub.

The engine is deterministic and offline by default: quotes and bars come from the
run snapshot. This module documents the integration seam for live US market data
without enabling any network access. Like the live news provider and the Robinhood
MCP broker, it refuses to run unless an operator explicitly configures a vendor and
supplies credentials through the environment.

Intended US vendors (operator choice):

- Yahoo Finance — delayed quotes and daily OHLCV history.
- Alpha Vantage — quotes, history, and technical indicators (``ALPHA_VANTAGE_API_KEY``).
- Polygon.io — consolidated US equities tape (``POLYGON_API_KEY``).
- Nasdaq Data Link / FRED — macro series for the regime layer (``FRED_API_KEY``).

Wire a real client into ``get_quote`` / ``get_bars`` behind your own credentials,
rate limits, and caching before enabling live data.
"""

from __future__ import annotations

import os

from robinhood_agent.market.base import MarketDataProvider
from robinhood_agent.market.offline import SnapshotMarketDataProvider
from robinhood_agent.models.context import MarketSnapshot
from robinhood_agent.models.market import PriceBar, Quote
from robinhood_agent.utils.logging import get_logger

logger = get_logger(__name__)


class LiveMarketDataProvider(MarketDataProvider):
    """Disabled stub for a live US market-data vendor.

    Reads its vendor and API key from the environment and otherwise refuses to run,
    so the engine never performs an unexpected network call.
    """

    def __init__(self, vendor: str | None = None, api_key: str | None = None) -> None:
        self.vendor = vendor or os.getenv("MARKET_DATA_VENDOR")
        self.api_key = api_key or os.getenv("MARKET_DATA_API_KEY")

    def _refuse(self) -> None:
        raise RuntimeError(
            "Live market-data provider is not configured. Set "
            "MARKET_DATA_PROVIDER=offline to use the deterministic snapshot, or "
            "implement LiveMarketDataProvider with a vendor (Yahoo Finance, Alpha "
            "Vantage, Polygon) and MARKET_DATA_API_KEY before enabling live data."
        )

    def get_quote(self, symbol: str) -> Quote | None:
        self._refuse()
        return None

    def get_bars(self, symbol: str) -> list[PriceBar]:
        self._refuse()
        return []


def build_market_data_provider(
    provider: str, snapshot: MarketSnapshot, api_key: str | None = None
) -> MarketDataProvider:
    """Construct the configured market-data provider; defaults to offline snapshot."""
    if provider == "live":
        logger.warning(
            "Live market-data provider requested; ensure MARKET_DATA_API_KEY is set."
        )
        return LiveMarketDataProvider(api_key=api_key)
    return SnapshotMarketDataProvider(snapshot)
