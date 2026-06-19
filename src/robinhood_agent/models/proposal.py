"""Strategy signals and order proposals."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class Side(str, Enum):
    """Order direction."""

    BUY = "buy"
    SELL = "sell"


class OrderType(str, Enum):
    """Supported order types."""

    MARKET = "market"
    LIMIT = "limit"


class StrategySignal(BaseModel):
    """A directional view emitted by a strategy for one symbol.

    Signals are advisory inputs that the strategy turns into proposals. ``strength``
    is a normalized conviction in [0, 1].
    """

    strategy: str
    symbol: str
    action: str  # buy | sell | hold | rebalance
    strength: float = Field(default=0.0, ge=0.0, le=1.0)
    rationale: str = ""
    evidence: dict[str, object] = Field(default_factory=dict)


class OrderProposal(BaseModel):
    """A concrete order a strategy wants to place, before risk review.

    A proposal is never executed directly: it must pass the risk guardian and the
    decision agent first.
    """

    proposal_id: str
    symbol: str
    side: Side
    quantity: float = Field(..., gt=0.0)
    order_type: OrderType = OrderType.MARKET
    limit_price: float | None = Field(default=None, gt=0.0)
    estimated_price: float = Field(..., gt=0.0)
    strategy: str = ""
    rationale: str = ""
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)

    @property
    def notional(self) -> float:
        """Estimated cash value of the order."""
        return self.quantity * self.estimated_price
