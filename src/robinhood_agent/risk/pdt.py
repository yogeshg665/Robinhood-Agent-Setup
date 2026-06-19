"""Pattern-day-trader (PDT) guard."""

from __future__ import annotations

from robinhood_agent.models.context import TradingContext
from robinhood_agent.models.proposal import OrderProposal
from robinhood_agent.models.risk import RiskFinding
from robinhood_agent.risk.base import RiskCheck


class PdtCheck(RiskCheck):
    """Blocks new orders that would breach the PDT day-trade limit.

    Accounts not flagged as pattern day traders are limited to a small number of
    day trades in a rolling five-day window. When the recorded day-trade count has
    reached the limit, further orders are blocked to avoid a restriction.
    """

    name = "pdt"

    def evaluate(
        self, proposal: OrderProposal, context: TradingContext, order_index: int
    ) -> RiskFinding | None:
        settings = self.config.risk.pdt
        account = context.portfolio.account
        if account.is_pattern_day_trader:
            return None
        if account.day_trades_used >= settings.max_day_trades:
            return self._finding(
                name="pdt_limit_reached",
                severity=85.0,
                blocking=True,
                rationale=(
                    f"Account has used {account.day_trades_used} of "
                    f"{settings.max_day_trades} permitted day trades and is not "
                    f"PDT-flagged; new orders are blocked to avoid a restriction."
                ),
                evidence={
                    "day_trades_used": account.day_trades_used,
                    "limit": settings.max_day_trades,
                },
            )
        return None
