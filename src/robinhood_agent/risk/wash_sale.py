"""Wash-sale awareness check (US IRS 30-day rule).

Flags a buy of a security that was sold at a loss within the wash-sale window, so
the agent does not inadvertently trigger a disallowed loss. The check is advisory by
default (non-blocking) because the wash-sale rule affects tax treatment rather than
trade safety; set ``risk.wash_sale.blocking`` to make it veto such buys.
"""

from __future__ import annotations

from robinhood_agent.models.context import TradingContext
from robinhood_agent.models.proposal import OrderProposal, Side
from robinhood_agent.models.risk import RiskFinding
from robinhood_agent.risk.base import RiskCheck


class WashSaleCheck(RiskCheck):
    """Warns when a buy would repurchase a recent loss sale within the IRS window."""

    name = "wash_sale"

    def evaluate(
        self, proposal: OrderProposal, context: TradingContext, order_index: int
    ) -> RiskFinding | None:
        settings = self.config.risk.wash_sale
        if not settings.enabled or proposal.side is not Side.BUY:
            return None

        sale = context.portfolio.recent_loss_sale(proposal.symbol, settings.window_days)
        if sale is None:
            return None

        return self._finding(
            name="wash_sale_window",
            severity=settings.severity,
            blocking=settings.blocking,
            rationale=(
                f"Buying {proposal.symbol} repurchases a loss sale closed "
                f"{sale.days_ago} day(s) ago (realized loss {sale.realized_loss:,.0f}), "
                f"within the {settings.window_days}-day IRS wash-sale window; the loss "
                f"may be disallowed."
            ),
            evidence={
                "days_ago": sale.days_ago,
                "realized_loss": round(sale.realized_loss, 2),
                "window_days": settings.window_days,
            },
        )
