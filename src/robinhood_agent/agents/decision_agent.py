"""Decision agent: map risk findings to a deterministic trade decision.

The mapping is reproducible and explainable. A blocking finding vetoes the order
when the policy enforces it. Otherwise the aggregate risk score (the maximum
finding severity) and the manual-approval policy determine whether an order may be
sent automatically or must be routed to a human.
"""

from __future__ import annotations

from robinhood_agent.agents.base import Agent
from robinhood_agent.models.context import TradingContext
from robinhood_agent.models.decision import DecisionOutcome, TradeDecision
from robinhood_agent.models.risk import RiskFinding


class DecisionAgent(Agent):
    """Applies the decision policy to each proposal's findings."""

    name = "decision"

    def run(
        self,
        context: TradingContext,
        findings_by_proposal: dict[str, list[RiskFinding]],
    ) -> list[TradeDecision]:
        policy = self.config.decision_policy
        decisions: list[TradeDecision] = []

        for proposal in context.proposals:
            findings = findings_by_proposal.get(proposal.proposal_id, [])
            risk_score = max((f.severity for f in findings), default=0.0)
            has_blocking = any(f.blocking for f in findings)
            reasons = [f"{f.name}: {f.rationale}" for f in findings]

            if has_blocking and policy.block_on_critical:
                outcome = DecisionOutcome.BLOCK
            elif policy.require_manual_approval or risk_score >= policy.approval_threshold:
                outcome = DecisionOutcome.REQUIRE_APPROVAL
            else:
                outcome = DecisionOutcome.ALLOW

            decision = TradeDecision(
                proposal_id=proposal.proposal_id,
                symbol=proposal.symbol,
                outcome=outcome,
                risk_score=round(risk_score, 1),
                findings=findings,
                reasons=reasons or [proposal.rationale],
                narrative=self._narrative(proposal, outcome, risk_score),
            )
            decisions.append(decision)

        self.logger.info("Decision agent produced %d decision(s)", len(decisions))
        return decisions

    @staticmethod
    def _narrative(proposal, outcome: DecisionOutcome, risk_score: float) -> str:
        verb = {
            DecisionOutcome.ALLOW: "approved for automatic execution",
            DecisionOutcome.REQUIRE_APPROVAL: "held for human approval",
            DecisionOutcome.BLOCK: "blocked by the risk guardian",
        }[outcome]
        return (
            f"{proposal.side.value.title()} {proposal.quantity:.0f} {proposal.symbol} "
            f"({proposal.strategy}) was {verb}. Aggregate risk {risk_score:.1f}/100."
        )
