"""Risk-finding model emitted by the risk-guardian swarm."""

from __future__ import annotations

from pydantic import BaseModel, Field


class RiskFinding(BaseModel):
    """A single risk observation about an order proposal.

    ``severity`` is 0-100. ``blocking`` marks a hard limit breach that must veto the
    order regardless of any strategy conviction or narrative.
    """

    check: str
    name: str
    severity: float = Field(default=0.0, ge=0.0, le=100.0)
    blocking: bool = False
    rationale: str = ""
    evidence: dict[str, object] = Field(default_factory=dict)

    @property
    def triggered(self) -> bool:
        return self.severity > 0.0 or self.blocking
