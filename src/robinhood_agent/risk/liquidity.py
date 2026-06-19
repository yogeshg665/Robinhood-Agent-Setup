"""Liquidity and volatility screen."""

from __future__ import annotations

from robinhood_agent.models.context import TradingContext
from robinhood_agent.models.proposal import OrderProposal
from robinhood_agent.models.risk import RiskFinding
from robinhood_agent.risk.base import RiskCheck


class LiquidityCheck(RiskCheck):
    """Flags thin or highly volatile names for human approval.

    Unlike the hard limits, this check is non-blocking: it raises severity so the
    decision agent routes the order to manual approval rather than vetoing it
    outright. High volatility, wide spreads, and low average volume each contribute.
    """

    name = "liquidity"

    def evaluate(
        self, proposal: OrderProposal, context: TradingContext, order_index: int
    ) -> RiskFinding | None:
        settings = self.config.risk.liquidity
        quote = context.snapshot.quote(proposal.symbol)
        if quote is None:
            return None

        reasons: list[str] = []
        severity = 0.0
        evidence: dict[str, object] = {}

        if quote.volatility > settings.max_volatility:
            severity = max(severity, 65.0)
            reasons.append(
                f"daily volatility {quote.volatility:.1%} exceeds "
                f"{settings.max_volatility:.1%}"
            )
            evidence["volatility"] = round(quote.volatility, 4)

        if quote.spread_pct > settings.max_spread_pct:
            severity = max(severity, 55.0)
            reasons.append(
                f"bid/ask spread {quote.spread_pct:.2f}% exceeds "
                f"{settings.max_spread_pct:.2f}%"
            )
            evidence["spread_pct"] = round(quote.spread_pct, 3)

        if 0.0 < quote.average_volume < settings.min_average_volume:
            severity = max(severity, 50.0)
            reasons.append(
                f"average volume {quote.average_volume:,.0f} is below "
                f"{settings.min_average_volume:,.0f}"
            )
            evidence["average_volume"] = quote.average_volume

        if severity == 0.0:
            return None

        return self._finding(
            name="thin_liquidity",
            severity=severity,
            blocking=False,
            rationale=(
                f"{proposal.symbol} shows liquidity risk: " + "; ".join(reasons) + "."
            ),
            evidence=evidence,
        )
