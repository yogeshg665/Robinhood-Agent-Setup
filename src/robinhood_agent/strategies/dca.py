"""Dollar-cost-averaging strategy: scheduled contributions across a watchlist."""

from __future__ import annotations

from robinhood_agent.models.context import TradingContext
from robinhood_agent.models.proposal import Side, StrategySignal
from robinhood_agent.strategies.base import Strategy, StrategyOutput


class DollarCostAveragingStrategy(Strategy):
    """Spreads a fixed periodic contribution evenly across the watchlist.

    The contribution is divided across the named symbols, and each slice is turned
    into a whole-share buy. This provides a steady, low-volatility accumulation path
    independent of short-term signals.
    """

    name = "dca"

    def generate(self, context: TradingContext) -> StrategyOutput:
        settings = self.config.strategy.dca
        out = StrategyOutput()
        targets = context.goals.watchlist or list(context.goals.target_weights.keys())
        if not targets or settings.contribution_amount <= 0.0:
            return out

        slice_amount = settings.contribution_amount / len(targets)
        for symbol in targets:
            quote = context.snapshot.quote(symbol)
            if quote is None or quote.price <= 0.0:
                continue
            quantity = float(int(slice_amount // quote.price))
            if quantity <= 0.0:
                continue
            rationale = (
                f"{settings.cadence.title()} DCA: invest ~{slice_amount:,.0f} into "
                f"{symbol} ({quantity:.0f} share(s))."
            )
            out.signals.append(
                StrategySignal(strategy=self.name, symbol=symbol, action="buy",
                               strength=0.4, rationale=rationale,
                               evidence={"cadence": settings.cadence})
            )
            out.proposals.append(
                self._make_proposal(symbol, Side.BUY, quantity, quote.price,
                                    rationale, confidence=0.5)
            )
        return out
