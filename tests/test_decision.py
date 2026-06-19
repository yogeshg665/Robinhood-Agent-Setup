"""Tests for the decision agent's deterministic outcome mapping."""

from __future__ import annotations

from robinhood_agent.agents.decision_agent import DecisionAgent
from robinhood_agent.models.decision import DecisionOutcome
from robinhood_agent.models.proposal import Side
from robinhood_agent.models.risk import RiskFinding
from tests.conftest import build_config, make_context, make_proposal


def _finding(severity: float, blocking: bool) -> RiskFinding:
    return RiskFinding(
        check="test",
        name="test_finding",
        severity=severity,
        blocking=blocking,
        rationale="synthetic finding",
        evidence={},
    )


def test_decision_mapping_allow_require_block() -> None:
    blocked = make_proposal("BLK", Side.BUY, 1, 100.0)
    review = make_proposal("REV", Side.BUY, 1, 100.0)
    allowed = make_proposal("OK", Side.BUY, 1, 100.0)
    context = make_context()
    context.proposals = [blocked, review, allowed]

    findings = {
        blocked.proposal_id: [_finding(90.0, blocking=True)],
        review.proposal_id: [_finding(65.0, blocking=False)],
        allowed.proposal_id: [],
    }

    decisions = {d.proposal_id: d for d in DecisionAgent(build_config()).run(context, findings)}
    assert decisions[blocked.proposal_id].outcome is DecisionOutcome.BLOCK
    assert decisions[review.proposal_id].outcome is DecisionOutcome.REQUIRE_APPROVAL
    assert decisions[allowed.proposal_id].outcome is DecisionOutcome.ALLOW


def test_risk_score_is_max_severity() -> None:
    proposal = make_proposal("AAA", Side.BUY, 1, 100.0)
    context = make_context()
    context.proposals = [proposal]
    findings = {proposal.proposal_id: [_finding(30.0, False), _finding(72.0, False)]}
    decision = DecisionAgent(build_config()).run(context, findings)[0]
    assert decision.risk_score == 72.0


def test_blocking_overrides_low_severity() -> None:
    # A blocking finding vetoes even when severity is below the approval threshold.
    proposal = make_proposal("AAA", Side.BUY, 1, 100.0)
    context = make_context()
    context.proposals = [proposal]
    findings = {proposal.proposal_id: [_finding(10.0, blocking=True)]}
    decision = DecisionAgent(build_config()).run(context, findings)[0]
    assert decision.outcome is DecisionOutcome.BLOCK
