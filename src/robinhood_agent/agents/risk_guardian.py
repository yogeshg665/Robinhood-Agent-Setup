"""Risk-guardian agent: run the risk swarm against every proposal."""

from __future__ import annotations

from robinhood_agent.agents.base import Agent
from robinhood_agent.models.context import TradingContext
from robinhood_agent.models.risk import RiskFinding
from robinhood_agent.risk.registry import default_risk_checks


class RiskGuardianAgent(Agent):
    """Evaluates each order proposal against every risk check.

    The guardian is the authority that can veto an order. Each check runs in
    isolation so a single faulty check cannot suppress the others. Findings are
    returned keyed by proposal id for the decision agent.
    """

    name = "risk_guardian"

    def __init__(self, config) -> None:
        super().__init__(config)
        self.checks = default_risk_checks(config)

    def run(self, context: TradingContext) -> dict[str, list[RiskFinding]]:
        findings_by_proposal: dict[str, list[RiskFinding]] = {}
        for order_index, proposal in enumerate(context.proposals):
            findings: list[RiskFinding] = []
            for check in self.checks:
                try:
                    finding = check.evaluate(proposal, context, order_index)
                except Exception as exc:  # noqa: BLE001 - isolate check failures
                    self.logger.warning("Risk check %s failed: %s", check.name, exc)
                    continue
                if finding is not None:
                    findings.append(finding)
            findings_by_proposal[proposal.proposal_id] = findings
        self.logger.info(
            "Risk guardian evaluated %d proposal(s)", len(context.proposals)
        )
        return findings_by_proposal
