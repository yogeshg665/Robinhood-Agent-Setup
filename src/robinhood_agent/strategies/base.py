"""Base class and shared helpers for trading strategies.

Each strategy is independent and side-effect free: it reads the
:class:`TradingContext` and returns a :class:`StrategyOutput` of signals and order
proposals. Strategies never execute orders and never override risk findings.
"""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from robinhood_agent.models.context import TradingContext
from robinhood_agent.models.proposal import OrderProposal, OrderType, Side, StrategySignal
from robinhood_agent.utils.config import EngineConfig


@dataclass
class StrategyOutput:
    """What a strategy returns: advisory signals and concrete proposals."""

    signals: list[StrategySignal] = field(default_factory=list)
    proposals: list[OrderProposal] = field(default_factory=list)


class Strategy(ABC):
    """Abstract base for all strategies."""

    name: str = "strategy"

    def __init__(self, config: EngineConfig) -> None:
        self.config = config

    @abstractmethod
    def generate(self, context: TradingContext) -> StrategyOutput:
        """Produce signals and proposals for the current context."""

    # -- helpers -----------------------------------------------------------

    @staticmethod
    def _proposal_id() -> str:
        return f"prop_{uuid.uuid4().hex[:10]}"

    def _make_proposal(
        self,
        symbol: str,
        side: Side,
        quantity: float,
        price: float,
        rationale: str,
        confidence: float = 0.5,
        order_type: OrderType = OrderType.MARKET,
        limit_price: float | None = None,
    ) -> OrderProposal:
        return OrderProposal(
            proposal_id=self._proposal_id(),
            symbol=symbol,
            side=side,
            quantity=round(quantity, 6),
            order_type=order_type,
            limit_price=limit_price,
            estimated_price=price,
            strategy=self.name,
            rationale=rationale,
            confidence=confidence,
        )

    @staticmethod
    def _tranche_quantity(
        context: TradingContext, price: float, fraction: float
    ) -> float:
        """Whole-share quantity for a target fraction of total portfolio value."""
        if price <= 0.0:
            return 0.0
        target_notional = context.portfolio.total_value * fraction
        affordable = min(target_notional, context.portfolio.account.cash)
        return float(int(max(affordable, 0.0) // price))
