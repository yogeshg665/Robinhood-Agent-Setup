"""Momentum strategy: follow strong trends over a lookback window."""

from __future__ import annotations

from robinhood_agent.models.context import TradingContext
from robinhood_agent.models.proposal import Side, StrategySignal
from robinhood_agent.strategies.base import Strategy, StrategyOutput


class MomentumStrategy(Strategy):
    """Buys strong up-trends and exits strong down-trends.

    The trailing return over ``lookback_bars`` is compared to symmetric buy and sell
    thresholds. Buys are sized as a small tranche of the portfolio; sells exit an
    existing position that has rolled over.
    """

    name = "momentum"

    def generate(self, context: TradingContext) -> StrategyOutput:
        settings = self.config.strategy.momentum
        out = StrategyOutput()
        universe = context.goals.watchlist or list(context.snapshot.quotes.keys())

        for symbol in universe:
            bars = context.snapshot.bars_for(symbol)
            if len(bars) < settings.lookback_bars:
                continue
            window = bars[-settings.lookback_bars :]
            start_close = window[0].close
            end_close = window[-1].close
            if start_close <= 0.0:
                continue
            ret_pct = (end_close - start_close) / start_close * 100.0
            quote = context.snapshot.quote(symbol)
            if quote is None:
                continue

            held = context.portfolio.position_for(symbol)
            if ret_pct >= settings.buy_return_pct:
                quantity = self._tranche_quantity(context, quote.price, 0.05)
                if quantity <= 0.0:
                    continue
                rationale = (
                    f"{symbol} returned {ret_pct:+.1f}% over {settings.lookback_bars} "
                    f"bars, above the {settings.buy_return_pct:.0f}% momentum buy "
                    f"threshold."
                )
                strength = min(1.0, ret_pct / max(settings.buy_return_pct * 2, 1e-9))
                out.signals.append(
                    StrategySignal(strategy=self.name, symbol=symbol, action="buy",
                                   strength=strength, rationale=rationale,
                                   evidence={"return_pct": round(ret_pct, 2)})
                )
                out.proposals.append(
                    self._make_proposal(symbol, Side.BUY, quantity, quote.price,
                                        rationale, confidence=0.6)
                )
            elif ret_pct <= settings.sell_return_pct and held and held.quantity > 0:
                rationale = (
                    f"{symbol} returned {ret_pct:+.1f}% over {settings.lookback_bars} "
                    f"bars, below the {settings.sell_return_pct:.0f}% momentum exit "
                    f"threshold; exit position."
                )
                out.signals.append(
                    StrategySignal(strategy=self.name, symbol=symbol, action="sell",
                                   strength=0.6, rationale=rationale,
                                   evidence={"return_pct": round(ret_pct, 2)})
                )
                out.proposals.append(
                    self._make_proposal(symbol, Side.SELL, float(int(held.quantity)),
                                        quote.price, rationale, confidence=0.6)
                )
        return out
