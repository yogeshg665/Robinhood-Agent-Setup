"""Broker adapter interface and the execution-report model."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime, timezone

from pydantic import BaseModel, Field

from robinhood_agent.models.proposal import OrderProposal


class ExecutionReport(BaseModel):
    """The result of attempting to place a single order."""

    proposal_id: str
    symbol: str
    side: str
    quantity: float
    status: str  # filled | submitted | rejected | skipped
    venue: str
    filled_price: float = 0.0
    detail: str = ""
    submitted_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class BrokerAdapter(ABC):
    """Abstract broker. Implementations place orders for approved proposals."""

    venue: str = "broker"

    @abstractmethod
    def place_order(self, proposal: OrderProposal) -> ExecutionReport:
        """Place a single order and return an execution report."""
