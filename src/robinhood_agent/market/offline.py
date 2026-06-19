"""Deterministic market-data provider backed by the run snapshot."""

from __future__ import annotations

from robinhood_agent.market.base import MarketDataProvider
from robinhood_agent.models.context import MarketSnapshot
from robinhood_agent.models.market import PriceBar, Quote


class SnapshotMarketDataProvider(MarketDataProvider):
    """Serves quotes and bars directly from a provided :class:`MarketSnapshot`.

    This keeps the engine fully deterministic and offline: all market data is part
    of the run input. A live provider can later implement the same interface.
    """

    def __init__(self, snapshot: MarketSnapshot) -> None:
        self.snapshot = snapshot

    def get_quote(self, symbol: str) -> Quote | None:
        return self.snapshot.quote(symbol)

    def get_bars(self, symbol: str) -> list[PriceBar]:
        return self.snapshot.bars_for(symbol)
