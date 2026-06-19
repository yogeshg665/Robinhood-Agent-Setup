"""Trade-decision model produced by the decision agent."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field

from robinhood_agent.models.risk import RiskFinding


class DecisionOutcome(str, Enum):
    """Terminal disposition for an order proposal."""

    ALLOW = "allow"
    REQUIRE_APPROVAL = "require_approval"
    BLOCK = "block"


class TradeDecision(BaseModel):
    """The risk-governed decision for a single order proposal.

    The decision is fully explainable: it references the aggregate risk score, the
    triggering findings, and a human-readable narrative. The outcome is deterministic
    given the proposal and findings.
    """

    proposal_id: str
    symbol: str
    outcome: DecisionOutcome
    risk_score: float = Field(default=0.0, ge=0.0, le=100.0)
    findings: list[RiskFinding] = Field(default_factory=list)
    reasons: list[str] = Field(default_factory=list)
    narrative: str = ""
    decided_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def is_executable(self) -> bool:
        """Whether the order may be sent to a broker without human sign-off."""
        return self.outcome is DecisionOutcome.ALLOW

    @property
    def needs_human(self) -> bool:
        return self.outcome is DecisionOutcome.REQUIRE_APPROVAL
