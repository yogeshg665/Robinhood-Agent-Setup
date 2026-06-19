"""Base class for risk checks.

Every check inspects a single :class:`OrderProposal` against the portfolio, the
market snapshot, and the configured limits, and returns at most one
:class:`RiskFinding`. A check is deterministic and must never place orders. A
``blocking`` finding is a hard limit breach that vetoes the order.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from robinhood_agent.models.context import TradingContext
from robinhood_agent.models.proposal import OrderProposal
from robinhood_agent.models.risk import RiskFinding
from robinhood_agent.utils.config import EngineConfig


class RiskCheck(ABC):
    """Abstract base for all pre-trade risk checks."""

    name: str = "risk"

    def __init__(self, config: EngineConfig) -> None:
        self.config = config

    @abstractmethod
    def evaluate(
        self, proposal: OrderProposal, context: TradingContext, order_index: int
    ) -> RiskFinding | None:
        """Return a finding for this proposal, or ``None`` when the check passes."""

    def _finding(
        self,
        name: str,
        severity: float,
        rationale: str,
        blocking: bool = False,
        evidence: dict | None = None,
    ) -> RiskFinding:
        return RiskFinding(
            check=self.name,
            name=name,
            severity=severity,
            blocking=blocking,
            rationale=rationale,
            evidence=evidence or {},
        )
