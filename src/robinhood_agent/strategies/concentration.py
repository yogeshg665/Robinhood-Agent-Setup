"""Concentration strategy: trim oversized single-name positions."""

from __future__ import annotations

from robinhood_agent.models.context import TradingContext
from robinhood_agent.models.proposal import Side, StrategySignal
from robinhood_agent.strategies.base import Strategy, StrategyOutput


class ConcentrationStrategy(Strategy):
    """Proposes trims when a single position exceeds the mandate's size cap.

    This is the proactive counterpart to the position-size risk check: rather than
    only blocking new buys, it actively reduces an existing overweight back toward
    the maximum position size.
    """

    name = "concentration"

    def generate(self, context: TradingContext) -> StrategyOutput:
        out = StrategyOutput()
        total = context.portfolio.total_value
        if total <= 0.0:
            return out

        cap = context.goals.max_position_pct
        for position in context.portfolio.positions:
            weight = context.portfolio.weight_of(position.symbol)
            if weight <= cap:
                continue
            quote = context.snapshot.quote(position.symbol)
            price = quote.price if quote else position.current_price
            if price <= 0.0:
                continue

            excess_notional = (weight - cap) * total
            quantity = float(int(min(excess_notional / price, position.quantity)))
            if quantity <= 0.0:
                continue

            rationale = (
                f"{position.symbol} is {weight:.1%} of the portfolio, above the "
                f"{cap:.1%} single-name cap; trim {quantity:.0f} share(s)."
            )
            out.signals.append(
                StrategySignal(
                    strategy=self.name,
                    symbol=position.symbol,
                    action="sell",
                    strength=min(1.0, (weight - cap) / max(cap, 1e-9)),
                    rationale=rationale,
                    evidence={"weight": round(weight, 4), "cap": cap},
                )
            )
            out.proposals.append(
                self._make_proposal(
                    symbol=position.symbol,
                    side=Side.SELL,
                    quantity=quantity,
                    price=price,
                    rationale=rationale,
                    confidence=0.75,
                )
            )
        return out
