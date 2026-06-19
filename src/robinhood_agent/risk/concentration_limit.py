"""Sector-concentration limit."""

from __future__ import annotations

from robinhood_agent.models.context import TradingContext
from robinhood_agent.models.proposal import OrderProposal, Side
from robinhood_agent.models.risk import RiskFinding
from robinhood_agent.risk.base import RiskCheck


class ConcentrationLimitCheck(RiskCheck):
    """Blocks buys that would push a sector above its maximum weight."""

    name = "concentration_limit"

    def evaluate(
        self, proposal: OrderProposal, context: TradingContext, order_index: int
    ) -> RiskFinding | None:
        if proposal.side is not Side.BUY:
            return None
        settings = self.config.risk.concentration
        total = context.portfolio.total_value
        if total <= 0.0:
            return None

        sector = context.snapshot.sector_of(proposal.symbol)
        if sector == "unknown":
            return None
        current_sector_value = sum(
            p.market_value for p in context.portfolio.positions if p.sector == sector
        )
        projected = (current_sector_value + proposal.notional) / total
        if projected > settings.max_sector_pct:
            return self._finding(
                name="sector_concentration_exceeded",
                severity=85.0,
                blocking=True,
                rationale=(
                    f"Buying {proposal.symbol} would raise the '{sector}' sector "
                    f"weight to {projected:.1%}, above the "
                    f"{settings.max_sector_pct:.1%} limit."
                ),
                evidence={"sector": sector, "projected_weight": round(projected, 4)},
            )
        return None
