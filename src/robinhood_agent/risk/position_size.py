"""Position-size and per-order notional limits."""

from __future__ import annotations

from robinhood_agent.models.context import TradingContext
from robinhood_agent.models.proposal import OrderProposal, Side
from robinhood_agent.models.risk import RiskFinding
from robinhood_agent.risk.base import RiskCheck


class PositionSizeCheck(RiskCheck):
    """Blocks buys that would breach the single-name weight or order-notional cap."""

    name = "position_size"

    def evaluate(
        self, proposal: OrderProposal, context: TradingContext, order_index: int
    ) -> RiskFinding | None:
        settings = self.config.risk.position_size

        if proposal.notional > settings.max_order_notional:
            return self._finding(
                name="order_notional_exceeded",
                severity=95.0,
                blocking=True,
                rationale=(
                    f"Order notional {proposal.notional:,.0f} exceeds the per-order "
                    f"maximum of {settings.max_order_notional:,.0f} (fat-finger guard)."
                ),
                evidence={"notional": round(proposal.notional, 2)},
            )

        if proposal.side is not Side.BUY:
            return None

        total = context.portfolio.total_value
        if total <= 0.0:
            return None
        held = context.portfolio.position_for(proposal.symbol)
        held_value = held.market_value if held else 0.0
        projected_weight = (held_value + proposal.notional) / total
        cap = min(settings.max_position_pct, context.goals.max_position_pct)
        if projected_weight > cap:
            return self._finding(
                name="position_size_exceeded",
                severity=90.0,
                blocking=True,
                rationale=(
                    f"Buying {proposal.symbol} would raise its weight to "
                    f"{projected_weight:.1%}, above the {cap:.1%} single-name cap."
                ),
                evidence={"projected_weight": round(projected_weight, 4), "cap": cap},
            )
        return None
