"""Shared test fixtures and builders.

Everything here is synthetic. Builders assemble a deterministic ``TradingContext``,
proposals, and configuration so individual strategies and risk checks can be tested
in isolation.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from robinhood_agent.models.context import MarketSnapshot, TradingContext
from robinhood_agent.models.market import (
    Instrument,
    MacroIndicators,
    NewsItem,
    PriceBar,
    Quote,
)
from robinhood_agent.models.portfolio import (
    Account,
    Portfolio,
    Position,
    RecentSale,
    TradingGoals,
)
from robinhood_agent.models.proposal import OrderProposal, OrderType, Side
from robinhood_agent.utils.config import EngineConfig


def build_config(**overrides) -> EngineConfig:
    """Return a default engine config; overrides patch top-level sections by dict."""
    config = EngineConfig()
    for key, value in overrides.items():
        setattr(config, key, value)
    return config


def make_quote(
    symbol: str,
    price: float,
    previous_close: float | None = None,
    volatility: float = 0.02,
    average_volume: float = 5_000_000.0,
    bid: float | None = None,
    ask: float | None = None,
) -> Quote:
    return Quote(
        symbol=symbol,
        price=price,
        previous_close=previous_close if previous_close is not None else price,
        average_volume=average_volume,
        volatility=volatility,
        bid=bid,
        ask=ask,
    )


def make_bars(symbol: str, closes: list[float]) -> list[PriceBar]:
    start = datetime(2026, 5, 1, tzinfo=timezone.utc)
    bars: list[PriceBar] = []
    for index, close in enumerate(closes):
        bars.append(
            PriceBar(
                symbol=symbol,
                date=start + timedelta(days=index),
                open=close,
                high=close + 0.5,
                low=close - 0.5,
                close=close,
                volume=1_000_000.0,
            )
        )
    return bars


def make_position(
    symbol: str,
    quantity: float,
    price: float,
    average_cost: float | None = None,
    sector: str = "unknown",
) -> Position:
    return Position(
        symbol=symbol,
        quantity=quantity,
        average_cost=average_cost if average_cost is not None else price,
        current_price=price,
        sector=sector,
    )


def make_account(
    cash: float = 50_000.0,
    buying_power: float | None = None,
    start_of_day_equity: float = 0.0,
    day_trades_used: int = 0,
    is_pattern_day_trader: bool = False,
) -> Account:
    return Account(
        account_id="test-account",
        cash=cash,
        buying_power=buying_power if buying_power is not None else cash,
        start_of_day_equity=start_of_day_equity,
        day_trades_used=day_trades_used,
        is_pattern_day_trader=is_pattern_day_trader,
    )


def make_context(
    positions: list[Position] | None = None,
    goals: TradingGoals | None = None,
    instruments: list[Instrument] | None = None,
    quotes: list[Quote] | None = None,
    bars: dict[str, list[PriceBar]] | None = None,
    news: dict[str, list[NewsItem]] | None = None,
    account: Account | None = None,
    enrichment: dict | None = None,
    macro: MacroIndicators | None = None,
    recent_sales: list[RecentSale] | None = None,
    as_of: str = "2026-05-11T13:30:00+00:00",
) -> TradingContext:
    positions = positions or []
    portfolio = Portfolio(
        account=account or make_account(),
        positions=positions,
        recent_sales=recent_sales or [],
    )
    snapshot = MarketSnapshot(
        as_of=as_of,
        instruments={i.symbol: i for i in (instruments or [])},
        quotes={q.symbol: q for q in (quotes or [])},
        bars=bars or {},
        news=news or {},
        macro=macro,
    )
    return TradingContext(
        run_id="run_test",
        portfolio=portfolio,
        goals=goals or TradingGoals(),
        snapshot=snapshot,
        signals=[],
        proposals=[],
        enrichment=enrichment or {},
    )


def make_proposal(
    symbol: str,
    side: Side,
    quantity: float,
    price: float,
    strategy: str = "test",
    order_type: OrderType = OrderType.MARKET,
    limit_price: float | None = None,
) -> OrderProposal:
    return OrderProposal(
        proposal_id=f"prop_{symbol}_{side.value}",
        symbol=symbol,
        side=side,
        quantity=quantity,
        order_type=order_type,
        limit_price=limit_price,
        estimated_price=price,
        strategy=strategy,
        rationale="test proposal",
        confidence=0.5,
    )
