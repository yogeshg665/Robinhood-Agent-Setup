"""Provider interfaces for market data and company news.

These abstractions let the engine stay deterministic and offline by default while
leaving a clean seam for live data sources. The default providers read from the
run's snapshot and from local fixtures; live providers are optional and disabled
unless explicitly configured.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from robinhood_agent.models.market import NewsItem, PriceBar, Quote


class MarketDataProvider(ABC):
    """Supplies quotes and price history for symbols."""

    @abstractmethod
    def get_quote(self, symbol: str) -> Quote | None:
        """Return the latest quote for ``symbol`` or ``None`` if unavailable."""

    @abstractmethod
    def get_bars(self, symbol: str) -> list[PriceBar]:
        """Return the available OHLCV history for ``symbol`` (oldest first)."""


class NewsProvider(ABC):
    """Supplies recent news headlines for a target company."""

    @abstractmethod
    def get_news(self, symbol: str, lookback_hours: int) -> list[NewsItem]:
        """Return news for ``symbol`` within the lookback window (newest first)."""
