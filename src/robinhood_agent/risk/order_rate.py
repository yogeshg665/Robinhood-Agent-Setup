"""Per-run order-rate throttle."""

from __future__ import annotations

from robinhood_agent.models.context import TradingContext
from robinhood_agent.models.proposal import OrderProposal
from robinhood_agent.models.risk import RiskFinding
from robinhood_agent.risk.base import RiskCheck


class OrderRateCheck(RiskCheck):
    """Blocks proposals once the run exceeds the maximum order count.

    ``order_index`` is the zero-based position of the proposal within the run, so the
    first ``max_orders_per_run`` proposals pass and any beyond are throttled.
    """

    name = "order_rate"

    def evaluate(
        self, proposal: OrderProposal, context: TradingContext, order_index: int
    ) -> RiskFinding | None:
        settings = self.config.risk.order_rate
        if order_index >= settings.max_orders_per_run:
            return self._finding(
                name="order_rate_exceeded",
                severity=80.0,
                blocking=True,
                rationale=(
                    f"Order #{order_index + 1} exceeds the per-run limit of "
                    f"{settings.max_orders_per_run}; throttled to prevent runaway "
                    f"trading."
                ),
                evidence={"order_index": order_index, "limit": settings.max_orders_per_run},
            )
        return None
