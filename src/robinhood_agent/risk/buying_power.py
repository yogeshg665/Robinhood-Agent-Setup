"""Buying-power sufficiency check."""

from __future__ import annotations

from robinhood_agent.models.context import TradingContext
from robinhood_agent.models.proposal import OrderProposal, Side
from robinhood_agent.models.risk import RiskFinding
from robinhood_agent.risk.base import RiskCheck


class BuyingPowerCheck(RiskCheck):
    """Blocks buys that would exceed available cash after a configured buffer."""

    name = "buying_power"

    def evaluate(
        self, proposal: OrderProposal, context: TradingContext, order_index: int
    ) -> RiskFinding | None:
        if proposal.side is not Side.BUY:
            return None
        settings = self.config.risk.buying_power
        account = context.portfolio.account
        buffer_amount = context.portfolio.total_value * settings.cash_buffer_pct
        available = account.cash - buffer_amount
        if proposal.notional > available:
            return self._finding(
                name="insufficient_buying_power",
                severity=88.0,
                blocking=True,
                rationale=(
                    f"Order needs {proposal.notional:,.0f} but only {available:,.0f} "
                    f"is available after a {settings.cash_buffer_pct:.0%} cash buffer."
                ),
                evidence={
                    "required": round(proposal.notional, 2),
                    "available": round(available, 2),
                },
            )
        return None
