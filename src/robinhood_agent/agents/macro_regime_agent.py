"""Macro-regime agent: classify the US market environment deterministically.

This agent mirrors the "macro analyst" role of a trading desk, but it is fully
deterministic. It reads the run's macro indicators (VIX, the 10Y-2Y curve) and the
benchmark trend (SPY), then writes an advisory ``market_regime`` block into the
context enrichment. The regime can gate new buys in the relative-strength strategy,
but it never changes a risk finding or a trade decision.
"""

from __future__ import annotations

from robinhood_agent.agents.base import Agent
from robinhood_agent.models.context import TradingContext


def trailing_return_pct(closes: list[float], lookback: int) -> float | None:
    """Percent return over the last ``lookback`` closes, or ``None`` if too short."""
    if len(closes) < lookback or lookback < 1:
        return None
    window = closes[-lookback:]
    start = window[0]
    if start <= 0.0:
        return None
    return (window[-1] - start) / start * 100.0


class MacroRegimeAgent(Agent):
    """Derives an advisory US market regime: risk_on | neutral | risk_off."""

    name = "macro_regime"

    def run(self, context: TradingContext) -> TradingContext:
        if not self.config.macro.enabled:
            return context

        cfg = self.config.macro
        benchmark = context.goals.benchmark or self.config.benchmark.symbol
        lookback = self.config.benchmark.lookback_bars
        macro = context.snapshot.macro

        score = 0
        drivers: list[str] = []

        vix = macro.vix if macro else None
        if vix is not None:
            if vix >= cfg.vix_risk_off:
                score -= 2
                drivers.append(f"VIX {vix:.1f} >= {cfg.vix_risk_off:.0f} (risk-off)")
            elif vix <= cfg.vix_risk_on:
                score += 1
                drivers.append(f"VIX {vix:.1f} <= {cfg.vix_risk_on:.0f} (calm)")

        bench_bars = context.snapshot.bars_for(benchmark)
        bench_trend = trailing_return_pct(
            [bar.close for bar in bench_bars], lookback
        )
        if bench_trend is not None:
            if bench_trend > 0.0:
                score += 1
                drivers.append(f"{benchmark} trend {bench_trend:+.1f}% (up)")
            else:
                score -= 1
                drivers.append(f"{benchmark} trend {bench_trend:+.1f}% (down)")

        spread = macro.yield_curve_spread if macro else None
        if spread is not None and spread < 0.0 and cfg.inverted_curve_penalty:
            score -= 1
            drivers.append(f"10Y-2Y curve inverted ({spread:+.2f}pp)")

        if score >= 2:
            regime = "risk_on"
        elif score <= -2:
            regime = "risk_off"
        else:
            regime = "neutral"

        bench_quote = context.snapshot.quote(benchmark)
        context.enrichment["market_regime"] = {
            "regime": regime,
            "score": score,
            "benchmark": benchmark,
            "benchmark_trend_pct": round(bench_trend, 2) if bench_trend is not None else None,
            "benchmark_day_change_pct": (
                round(bench_quote.day_change_pct, 2) if bench_quote else None
            ),
            "vix": vix,
            "yield_curve_spread": spread,
            "drivers": drivers,
        }
        self.logger.info("Market regime classified as %s (score %d)", regime, score)
        return context
