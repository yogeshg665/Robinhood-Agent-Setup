"""Limit-price deviation (fat-finger) guard."""

from __future__ import annotations

from robinhood_agent.models.context import TradingContext
from robinhood_agent.models.proposal import OrderProposal, OrderType
from robinhood_agent.models.risk import RiskFinding
from robinhood_agent.risk.base import RiskCheck


class PriceDeviationCheck(RiskCheck):
    """Blocks limit orders whose price is implausibly far from the last quote."""

    name = "price_deviation"

    def evaluate(
        self, proposal: OrderProposal, context: TradingContext, order_index: int
    ) -> RiskFinding | None:
        if proposal.order_type is not OrderType.LIMIT or proposal.limit_price is None:
            return None
        settings = self.config.risk.price_deviation
        quote = context.snapshot.quote(proposal.symbol)
        reference = quote.price if quote else proposal.estimated_price
        if reference <= 0.0:
            return None
        deviation = abs(proposal.limit_price - reference) / reference * 100.0
        if deviation > settings.max_limit_deviation_pct:
            return self._finding(
                name="limit_price_deviation",
                severity=90.0,
                blocking=True,
                rationale=(
                    f"Limit price {proposal.limit_price:,.2f} deviates {deviation:.1f}% "
                    f"from the last price {reference:,.2f}, above the "
                    f"{settings.max_limit_deviation_pct:.1f}% fat-finger guard."
                ),
                evidence={"deviation_pct": round(deviation, 2)},
            )
        return None
