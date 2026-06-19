"""Aggregate context and result models that flow through the pipeline."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from robinhood_agent.models.decision import TradeDecision
from robinhood_agent.models.market import (
    Instrument,
    MacroIndicators,
    NewsItem,
    PriceBar,
    Quote,
)
from robinhood_agent.models.portfolio import Portfolio, TradingGoals
from robinhood_agent.models.proposal import OrderProposal, StrategySignal


class MarketSnapshot(BaseModel):
    """A deterministic snapshot of market data for one run.

    Quotes, bars, and instruments are keyed by symbol. News is keyed by symbol and
    used by the company-news signal.
    """

    as_of: str | None = None
    instruments: dict[str, Instrument] = Field(default_factory=dict)
    quotes: dict[str, Quote] = Field(default_factory=dict)
    bars: dict[str, list[PriceBar]] = Field(default_factory=dict)
    news: dict[str, list[NewsItem]] = Field(default_factory=dict)
    macro: MacroIndicators | None = None

    def quote(self, symbol: str) -> Quote | None:
        return self.quotes.get(symbol)

    def instrument(self, symbol: str) -> Instrument | None:
        return self.instruments.get(symbol)

    def sector_of(self, symbol: str) -> str:
        instrument = self.instruments.get(symbol)
        return instrument.sector if instrument else "unknown"

    def symbols_in_sector(self, sector: str) -> list[str]:
        return sorted(
            symbol
            for symbol, instrument in self.instruments.items()
            if instrument.sector == sector
        )

    def bars_for(self, symbol: str) -> list[PriceBar]:
        return self.bars.get(symbol, [])

    def news_for(self, symbol: str) -> list[NewsItem]:
        return self.news.get(symbol, [])


class TradingContext(BaseModel):
    """Everything an agent needs to reason about one trading run."""

    run_id: str
    portfolio: Portfolio
    goals: TradingGoals
    snapshot: MarketSnapshot = Field(default_factory=MarketSnapshot)
    signals: list[StrategySignal] = Field(default_factory=list)
    proposals: list[OrderProposal] = Field(default_factory=list)
    enrichment: dict[str, Any] = Field(default_factory=dict)


class TradingResult(BaseModel):
    """The outcome of a trading run: decisions, executions, and the report."""

    run_id: str
    decisions: list[TradeDecision] = Field(default_factory=list)
    report: dict[str, Any] = Field(default_factory=dict)
