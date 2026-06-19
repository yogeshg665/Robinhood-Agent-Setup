"""Tests for the deterministic macro-regime agent.

The regime is advisory: the agent writes a ``market_regime`` enrichment block but
never changes a risk finding or a decision.
"""

from __future__ import annotations

from robinhood_agent.agents.macro_regime_agent import MacroRegimeAgent
from robinhood_agent.models.market import MacroIndicators
from tests.conftest import build_config, make_bars, make_context


def _linear_closes(start: float, total_pct: float, count: int = 20) -> list[float]:
    return [start * (1.0 + (total_pct / 100.0) * i / (count - 1)) for i in range(count)]


def test_macro_regime_classifies_risk_on() -> None:
    context = make_context(
        macro=MacroIndicators(vix=14.0),  # <= 15 -> +1
        bars={"SPY": make_bars("SPY", _linear_closes(100.0, 3.0))},  # up -> +1
    )
    out = MacroRegimeAgent(build_config()).run(context)
    regime = out.enrichment["market_regime"]
    assert regime["regime"] == "risk_on"
    assert regime["score"] >= 2


def test_macro_regime_classifies_risk_off() -> None:
    context = make_context(
        macro=MacroIndicators(vix=30.0),  # >= 25 -> -2
        bars={"SPY": make_bars("SPY", _linear_closes(100.0, -3.0))},  # down -> -1
    )
    out = MacroRegimeAgent(build_config()).run(context)
    assert out.enrichment["market_regime"]["regime"] == "risk_off"


def test_macro_regime_neutral_without_signals() -> None:
    context = make_context()  # no macro, no benchmark bars -> score 0
    out = MacroRegimeAgent(build_config()).run(context)
    assert out.enrichment["market_regime"]["regime"] == "neutral"


def test_macro_regime_disabled_is_noop() -> None:
    config = build_config()
    config.macro.enabled = False
    context = make_context(macro=MacroIndicators(vix=14.0))
    out = MacroRegimeAgent(config).run(context)
    assert "market_regime" not in out.enrichment
