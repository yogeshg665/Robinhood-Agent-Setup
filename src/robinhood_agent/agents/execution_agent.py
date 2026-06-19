"""Execution agent: route approved orders to the broker adapter.

Only ``ALLOW`` decisions are sent to the broker. Orders held for human approval or
blocked by the guardian are recorded but never placed. With the default paper
broker, fills are simulated and no real funds are involved.
"""

from __future__ import annotations

from robinhood_agent.agents.base import Agent
from robinhood_agent.execution.base import BrokerAdapter, ExecutionReport
from robinhood_agent.models.context import TradingContext
from robinhood_agent.models.decision import DecisionOutcome, TradeDecision


class ExecutionAgent(Agent):
    """Places approved orders and records the disposition of the rest."""

    name = "execution"

    def run(
        self,
        context: TradingContext,
        decisions: list[TradeDecision],
        broker: BrokerAdapter,
    ) -> list[ExecutionReport]:
        proposals = {p.proposal_id: p for p in context.proposals}
        reports: list[ExecutionReport] = []

        for decision in decisions:
            proposal = proposals.get(decision.proposal_id)
            if proposal is None:
                continue
            if decision.outcome is DecisionOutcome.ALLOW:
                try:
                    reports.append(broker.place_order(proposal))
                except Exception as exc:  # noqa: BLE001 - never crash the run on a fill
                    self.logger.error("Order placement failed: %s", exc)
                    reports.append(
                        ExecutionReport(
                            proposal_id=proposal.proposal_id,
                            symbol=proposal.symbol,
                            side=proposal.side.value,
                            quantity=proposal.quantity,
                            status="rejected",
                            venue=broker.venue,
                            detail=str(exc),
                        )
                    )
            else:
                status = (
                    "held" if decision.outcome is DecisionOutcome.REQUIRE_APPROVAL
                    else "blocked"
                )
                reports.append(
                    ExecutionReport(
                        proposal_id=proposal.proposal_id,
                        symbol=proposal.symbol,
                        side=proposal.side.value,
                        quantity=proposal.quantity,
                        status=status,
                        venue=broker.venue,
                        detail=decision.narrative,
                    )
                )
        self.logger.info("Execution agent processed %d decision(s)", len(decisions))
        return reports
