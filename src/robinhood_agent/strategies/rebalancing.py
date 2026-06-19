"""Rebalancing strategy: drive holdings toward target weights."""

from __future__ import annotations

from robinhood_agent.models.context import TradingContext
from robinhood_agent.models.proposal import Side, StrategySignal
from robinhood_agent.strategies.base import Strategy, StrategyOutput


class RebalancingStrategy(Strategy):
    """Proposes buys and sells to close the gap to ``goals.target_weights``.

    A symbol is rebalanced only when its weight has drifted beyond the configured
    tolerance band and the corrective trade clears the minimum notional, which
    avoids churn on small deviations.
    """

    name = "rebalancing"

    def generate(self, context: TradingContext) -> StrategyOutput:
        settings = self.config.strategy.rebalancing
        out = StrategyOutput()
        total = context.portfolio.total_value
        if total <= 0.0:
            return out

        tolerance = settings.drift_tolerance_pct / 100.0
        for symbol, target_weight in context.goals.target_weights.items():
            quote = context.snapshot.quote(symbol)
            if quote is None:
                continue
            current_weight = context.portfolio.weight_of(symbol)
            drift = current_weight - target_weight
            if abs(drift) < tolerance:
                continue

            delta_notional = (target_weight - current_weight) * total
            if abs(delta_notional) < settings.min_trade_notional:
                continue

            side = Side.BUY if delta_notional > 0 else Side.SELL
            quantity = abs(delta_notional) / quote.price
            if side is Side.SELL:
                held = context.portfolio.position_for(symbol)
                quantity = min(quantity, held.quantity if held else 0.0)
            quantity = float(int(quantity))
            if quantity <= 0.0:
                continue

            rationale = (
                f"{symbol} weight {current_weight:.1%} drifted from target "
                f"{target_weight:.1%} (band {tolerance:.1%}); "
                f"{side.value} {quantity:.0f} share(s) to rebalance."
            )
            out.signals.append(
                StrategySignal(
                    strategy=self.name,
                    symbol=symbol,
                    action="rebalance",
                    strength=min(1.0, abs(drift) / max(tolerance, 1e-9)),
                    rationale=rationale,
                    evidence={
                        "current_weight": round(current_weight, 4),
                        "target_weight": round(target_weight, 4),
                    },
                )
            )
            out.proposals.append(
                self._make_proposal(
                    symbol=symbol,
                    side=side,
                    quantity=quantity,
                    price=quote.price,
                    rationale=rationale,
                    confidence=0.7,
                )
            )
        return out
