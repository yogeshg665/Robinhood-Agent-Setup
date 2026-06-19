"""Intraday drawdown kill-switch."""

from __future__ import annotations

from robinhood_agent.models.context import TradingContext
from robinhood_agent.models.proposal import OrderProposal, Side
from robinhood_agent.models.risk import RiskFinding
from robinhood_agent.risk.base import RiskCheck


class DailyLossCheck(RiskCheck):
    """Halts new buying once intraday loss breaches the configured limit.

    The kill-switch blocks risk-increasing buys but allows sells, so the agent can
    still de-risk after a bad day. Loss is measured against the account's
    start-of-day equity.
    """

    name = "daily_loss"

    def evaluate(
        self, proposal: OrderProposal, context: TradingContext, order_index: int
    ) -> RiskFinding | None:
        if proposal.side is not Side.BUY:
            return None
        settings = self.config.risk.daily_loss
        account = context.portfolio.account
        start = account.start_of_day_equity
        if start <= 0.0:
            return None
        day_pnl = context.portfolio.total_value - start
        loss_pct = -day_pnl / start * 100.0
        if loss_pct >= settings.max_daily_loss_pct:
            return self._finding(
                name="daily_loss_kill_switch",
                severity=100.0,
                blocking=True,
                rationale=(
                    f"Intraday drawdown {loss_pct:.1f}% has reached the "
                    f"{settings.max_daily_loss_pct:.1f}% kill-switch; new buys are "
                    f"halted for the session."
                ),
                evidence={"intraday_loss_pct": round(loss_pct, 2)},
            )
        return None
