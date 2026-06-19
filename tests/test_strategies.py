"""Tests for the strategy swarm: each strategy fires on a crafted context."""

from __future__ import annotations

from robinhood_agent.models.market import Instrument
from robinhood_agent.models.portfolio import TradingGoals
from robinhood_agent.models.proposal import Side
from robinhood_agent.strategies.company_news import CompanyNewsStrategy
from robinhood_agent.strategies.concentration import ConcentrationStrategy
from robinhood_agent.strategies.dca import DollarCostAveragingStrategy
from robinhood_agent.strategies.mean_reversion import MeanReversionStrategy
from robinhood_agent.strategies.momentum import MomentumStrategy
from robinhood_agent.strategies.rebalancing import RebalancingStrategy
from robinhood_agent.strategies.registry import default_strategies
from robinhood_agent.strategies.relative_strength import RelativeStrengthStrategy
from robinhood_agent.strategies.thematic import ThematicStrategy
from tests.conftest import (
    build_config,
    make_account,
    make_bars,
    make_context,
    make_position,
    make_quote,
)


def test_rebalancing_sells_overweight() -> None:
    context = make_context(
        positions=[make_position("AAA", 100, 100.0, sector="technology")],
        goals=TradingGoals(target_weights={"AAA": 0.5}),
        quotes=[make_quote("AAA", 100.0)],
        account=make_account(cash=0.0),
    )
    out = RebalancingStrategy(build_config()).generate(context)
    assert any(p.symbol == "AAA" and p.side is Side.SELL for p in out.proposals)


def test_concentration_trims_oversized_position() -> None:
    context = make_context(
        positions=[make_position("AAA", 100, 100.0, sector="technology")],
        goals=TradingGoals(max_position_pct=0.20),
        quotes=[make_quote("AAA", 100.0)],
        account=make_account(cash=0.0),
    )
    out = ConcentrationStrategy(build_config()).generate(context)
    assert any(p.symbol == "AAA" and p.side is Side.SELL for p in out.proposals)


def test_momentum_buys_strong_uptrend() -> None:
    closes = [100.0 + i for i in range(20)]  # +19% over the window
    context = make_context(
        goals=TradingGoals(watchlist=["MOM"]),
        quotes=[make_quote("MOM", closes[-1])],
        bars={"MOM": make_bars("MOM", closes)},
    )
    out = MomentumStrategy(build_config()).generate(context)
    assert any(p.symbol == "MOM" and p.side is Side.BUY for p in out.proposals)


def test_mean_reversion_buys_oversold() -> None:
    closes = [100.0 + i for i in range(20)]  # mean well above the depressed quote
    context = make_context(
        goals=TradingGoals(watchlist=["MR"]),
        quotes=[make_quote("MR", 95.0)],
        bars={"MR": make_bars("MR", closes)},
    )
    out = MeanReversionStrategy(build_config()).generate(context)
    assert any(p.symbol == "MR" and p.side is Side.BUY for p in out.proposals)


def test_thematic_adds_new_name_in_theme() -> None:
    context = make_context(
        goals=TradingGoals(themes=["healthcare"]),
        instruments=[Instrument(symbol="HLT", name="Health Co", sector="healthcare")],
        quotes=[make_quote("HLT", 50.0)],
    )
    out = ThematicStrategy(build_config()).generate(context)
    assert any(p.symbol == "HLT" and p.side is Side.BUY for p in out.proposals)


def test_dca_buys_whole_shares() -> None:
    context = make_context(
        goals=TradingGoals(watchlist=["CHEAP"]),
        quotes=[make_quote("CHEAP", 10.0)],
    )
    out = DollarCostAveragingStrategy(build_config()).generate(context)
    assert any(p.symbol == "CHEAP" and p.side is Side.BUY for p in out.proposals)


def test_company_news_buys_on_positive_sentiment() -> None:
    context = make_context(
        quotes=[make_quote("NWS", 40.0)],
        enrichment={
            "news_sentiment": {
                "NWS": {
                    "average_sentiment": 0.8,
                    "article_count": 2,
                    "latest_headline": "record growth",
                }
            }
        },
    )
    out = CompanyNewsStrategy(build_config()).generate(context)
    assert any(p.symbol == "NWS" and p.side is Side.BUY for p in out.proposals)


def test_registry_respects_toggles() -> None:
    config = build_config()
    config.strategy.toggles.momentum = False
    names = {strategy.name for strategy in default_strategies(config)}
    assert "momentum" not in names
    assert "rebalancing" in names


def _linear_closes(start: float, total_pct: float, count: int = 20) -> list[float]:
    """Closes that move ``total_pct`` percent linearly across ``count`` bars."""
    return [start * (1.0 + (total_pct / 100.0) * i / (count - 1)) for i in range(count)]


def test_relative_strength_buys_outperformer() -> None:
    context = make_context(
        goals=TradingGoals(watchlist=["LEAD"]),  # benchmark defaults to SPY
        quotes=[make_quote("LEAD", 115.0)],
        bars={
            "SPY": make_bars("SPY", _linear_closes(100.0, 3.0)),  # +3%
            "LEAD": make_bars("LEAD", _linear_closes(100.0, 15.0)),  # +15% -> excess +12
        },
    )
    out = RelativeStrengthStrategy(build_config()).generate(context)
    assert any(p.symbol == "LEAD" and p.side is Side.BUY for p in out.proposals)


def test_relative_strength_exits_underperformer() -> None:
    context = make_context(
        positions=[make_position("LAG", 10, 90.0)],
        goals=TradingGoals(watchlist=["LAG"]),
        quotes=[make_quote("LAG", 90.0)],
        bars={
            "SPY": make_bars("SPY", _linear_closes(100.0, 3.0)),  # +3%
            "LAG": make_bars("LAG", _linear_closes(100.0, -10.0)),  # -10% -> excess -13
        },
    )
    out = RelativeStrengthStrategy(build_config()).generate(context)
    assert any(p.symbol == "LAG" and p.side is Side.SELL for p in out.proposals)


def test_relative_strength_suppressed_in_risk_off() -> None:
    context = make_context(
        goals=TradingGoals(watchlist=["LEAD"]),
        quotes=[make_quote("LEAD", 115.0)],
        bars={
            "SPY": make_bars("SPY", _linear_closes(100.0, 3.0)),
            "LEAD": make_bars("LEAD", _linear_closes(100.0, 15.0)),
        },
        enrichment={"market_regime": {"regime": "risk_off"}},
    )
    out = RelativeStrengthStrategy(build_config()).generate(context)
    assert not any(p.side is Side.BUY for p in out.proposals)


def test_relative_strength_registered_by_default() -> None:
    names = {strategy.name for strategy in default_strategies(build_config())}
    assert "relative_strength" in names
