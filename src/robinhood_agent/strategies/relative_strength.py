"""Relative-strength strategy: trade US names against the benchmark (SPY).

For each watchlist name the strategy compares its trailing return to the benchmark's
trailing return over the same window. Names that meaningfully outperform are bought
in a small tranche; held names that meaningfully lag are exited. New buys are
suppressed when the macro-regime agent has flagged a risk-off environment. The
regime read is advisory and deterministic; it never overrides a risk finding.
"""

from __future__ import annotations

from robinhood_agent.models.context import TradingContext
from robinhood_agent.models.proposal import Side, StrategySignal
from robinhood_agent.strategies.base import Strategy, StrategyOutput


def _trailing_return_pct(closes: list[float], lookback: int) -> float | None:
    if len(closes) < lookback or lookback < 1:
        return None
    window = closes[-lookback:]
    start = window[0]
    if start <= 0.0:
        return None
    return (window[-1] - start) / start * 100.0


class RelativeStrengthStrategy(Strategy):
    """Buys benchmark-relative leaders and exits benchmark-relative laggards."""

    name = "relative_strength"

    def generate(self, context: TradingContext) -> StrategyOutput:
        settings = self.config.strategy.relative_strength
        out = StrategyOutput()

        benchmark = context.goals.benchmark or self.config.benchmark.symbol
        bench_bars = context.snapshot.bars_for(benchmark)
        bench_ret = _trailing_return_pct(
            [bar.close for bar in bench_bars], settings.lookback_bars
        )
        if bench_ret is None:
            return out  # no benchmark history: cannot measure relative strength

        regime = context.enrichment.get("market_regime", {}).get("regime")
        universe = context.goals.watchlist or list(context.snapshot.quotes.keys())

        for symbol in universe:
            if symbol == benchmark:
                continue
            bars = context.snapshot.bars_for(symbol)
            sym_ret = _trailing_return_pct(
                [bar.close for bar in bars], settings.lookback_bars
            )
            if sym_ret is None:
                continue
            quote = context.snapshot.quote(symbol)
            if quote is None:
                continue
            excess = sym_ret - bench_ret
            held = context.portfolio.position_for(symbol)

            if excess >= settings.outperform_pct and regime != "risk_off":
                quantity = self._tranche_quantity(
                    context, quote.price, settings.per_name_target_pct
                )
                if quantity <= 0.0:
                    continue
                rationale = (
                    f"{symbol} outperformed {benchmark} by {excess:+.1f}% over "
                    f"{settings.lookback_bars} bars ({sym_ret:+.1f}% vs "
                    f"{bench_ret:+.1f}%); relative-strength buy."
                )
                out.signals.append(
                    StrategySignal(
                        strategy=self.name, symbol=symbol, action="buy",
                        strength=min(1.0, excess / max(settings.outperform_pct * 2, 1e-9)),
                        rationale=rationale,
                        evidence={"excess_return_pct": round(excess, 2), "benchmark": benchmark},
                    )
                )
                out.proposals.append(
                    self._make_proposal(symbol, Side.BUY, quantity, quote.price,
                                        rationale, confidence=0.55)
                )
            elif excess <= settings.underperform_pct and held and held.quantity > 0:
                rationale = (
                    f"{symbol} lagged {benchmark} by {excess:+.1f}% over "
                    f"{settings.lookback_bars} bars ({sym_ret:+.1f}% vs "
                    f"{bench_ret:+.1f}%); relative-strength exit."
                )
                out.signals.append(
                    StrategySignal(
                        strategy=self.name, symbol=symbol, action="sell",
                        strength=0.55, rationale=rationale,
                        evidence={"excess_return_pct": round(excess, 2), "benchmark": benchmark},
                    )
                )
                out.proposals.append(
                    self._make_proposal(symbol, Side.SELL, float(int(held.quantity)),
                                        quote.price, rationale, confidence=0.55)
                )
        return out
