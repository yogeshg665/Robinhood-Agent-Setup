"""Intake agent: validate and normalize the run input into a context."""

from __future__ import annotations

import uuid
from typing import Any

from robinhood_agent.agents.base import Agent
from robinhood_agent.models.context import MarketSnapshot, TradingContext
from robinhood_agent.models.portfolio import Portfolio, TradingGoals


class IntakeAgent(Agent):
    """Builds a :class:`TradingContext` from raw portfolio, goals, and market data."""

    name = "intake"

    def run(
        self,
        portfolio: Portfolio,
        goals: TradingGoals,
        snapshot: MarketSnapshot,
        enrichment: dict[str, Any] | None = None,
    ) -> TradingContext:
        run_id = f"run_{uuid.uuid4().hex[:12]}"
        context = TradingContext(
            run_id=run_id,
            portfolio=portfolio,
            goals=goals,
            snapshot=snapshot,
            enrichment=dict(enrichment or {}),
        )
        self.logger.info(
            "Intake built %s: %d position(s), %d goal weight(s)",
            run_id,
            len(portfolio.positions),
            len(goals.target_weights),
        )
        return context
