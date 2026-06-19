"""Strategy-swarm agent: run every enabled strategy with isolation."""

from __future__ import annotations

from robinhood_agent.agents.base import Agent
from robinhood_agent.models.context import TradingContext
from robinhood_agent.strategies.registry import default_strategies


class StrategySwarmAgent(Agent):
    """Runs each strategy independently and collects signals and proposals.

    A failure in one strategy is isolated and logged so the rest of the swarm still
    contributes. The agent records which strategies produced proposals for the audit
    trail.
    """

    name = "strategy_swarm"

    def __init__(self, config) -> None:
        super().__init__(config)
        self.strategies = default_strategies(config)

    def run(self, context: TradingContext) -> TradingContext:
        contributions: list[dict] = []
        for strategy in self.strategies:
            try:
                output = strategy.generate(context)
            except Exception as exc:  # noqa: BLE001 - isolate strategy failures
                self.logger.warning("Strategy %s failed: %s", strategy.name, exc)
                continue
            context.signals.extend(output.signals)
            context.proposals.extend(output.proposals)
            contributions.append(
                {"strategy": strategy.name, "proposals": len(output.proposals)}
            )
        context.enrichment["swarm_contributions"] = contributions
        self.logger.info(
            "Strategy swarm produced %d proposal(s)", len(context.proposals)
        )
        return context
