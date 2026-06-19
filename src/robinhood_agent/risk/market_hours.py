"""US market-hours gate.

Blocks orders when the US regular session (NYSE/Nasdaq, 9:30-16:00 ET) is closed,
based on the deterministic snapshot timestamp. Extended-hours trading is treated as
closed unless ``risk.market_hours.allow_extended_hours`` is set. When the snapshot
has no parseable timestamp the check passes, so offline unit fixtures are unaffected.
"""

from __future__ import annotations

from robinhood_agent.market.calendar import describe, parse_as_of, session_state
from robinhood_agent.models.context import TradingContext
from robinhood_agent.models.proposal import OrderProposal
from robinhood_agent.models.risk import RiskFinding
from robinhood_agent.risk.base import RiskCheck


class MarketHoursCheck(RiskCheck):
    """Vetoes orders placed while the US regular session is closed."""

    name = "market_hours"

    def evaluate(
        self, proposal: OrderProposal, context: TradingContext, order_index: int
    ) -> RiskFinding | None:
        settings = self.config.risk.market_hours
        when = parse_as_of(context.snapshot.as_of)
        if when is None:
            return None

        state = session_state(when, allow_extended_hours=settings.allow_extended_hours)
        if state == "open":
            return None
        if state == "extended" and settings.allow_extended_hours:
            return None

        blocking = settings.block_when_closed
        return self._finding(
            name="market_closed",
            severity=100.0 if blocking else 40.0,
            blocking=blocking,
            rationale=(
                f"US market is {state} at {describe(when)}; regular session is "
                f"9:30-16:00 ET. Order cannot be transmitted while closed."
            ),
            evidence={"session_state": state, "as_of": context.snapshot.as_of},
        )
