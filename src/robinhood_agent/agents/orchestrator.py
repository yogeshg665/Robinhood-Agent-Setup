"""Orchestrator: coordinate the full trading lifecycle as an agent swarm."""

from __future__ import annotations

from typing import Any

from robinhood_agent.agents.base import Agent
from robinhood_agent.agents.decision_agent import DecisionAgent
from robinhood_agent.agents.execution_agent import ExecutionAgent
from robinhood_agent.agents.intake_agent import IntakeAgent
from robinhood_agent.agents.macro_regime_agent import MacroRegimeAgent
from robinhood_agent.agents.market_enrichment_agent import MarketEnrichmentAgent
from robinhood_agent.agents.reporting_agent import ReportingAgent
from robinhood_agent.agents.risk_guardian import RiskGuardianAgent
from robinhood_agent.agents.strategy_swarm import StrategySwarmAgent
from robinhood_agent.execution.factory import build_broker
from robinhood_agent.llm.client import LLMClient
from robinhood_agent.market.base import NewsProvider
from robinhood_agent.memory.store import MemoryStore
from robinhood_agent.models.context import MarketSnapshot, TradingContext, TradingResult
from robinhood_agent.models.portfolio import Portfolio, TradingGoals


class OrchestratorAgent(Agent):
    """Runs intake, enrichment, strategy swarm, risk guardian, decision, execution,
    and reporting in order, with an optional collective-memory side effect."""

    name = "orchestrator"

    def __init__(
        self,
        config,
        llm_client: LLMClient | None = None,
        memory_store: MemoryStore | None = None,
        news_provider: NewsProvider | None = None,
    ) -> None:
        super().__init__(config)
        self.memory_store = memory_store
        self.intake = IntakeAgent(config)
        self.enrichment = MarketEnrichmentAgent(config, news_provider=news_provider)
        self.macro = MacroRegimeAgent(config)
        self.swarm = StrategySwarmAgent(config)
        self.guardian = RiskGuardianAgent(config)
        self.decision = DecisionAgent(config)
        self.execution = ExecutionAgent(config)
        self.reporting = ReportingAgent(config, llm_client=llm_client)
        self.broker = build_broker(config)

    def run(
        self,
        portfolio: Portfolio,
        goals: TradingGoals,
        snapshot: MarketSnapshot,
        enrichment: dict[str, Any] | None = None,
    ) -> TradingResult:
        context = self.intake.run(portfolio, goals, snapshot, enrichment)
        context = self.enrichment.run(context)
        context = self.macro.run(context)
        self._recall_history(context)
        context = self.swarm.run(context)

        findings = self.guardian.run(context)
        decisions = self.decision.run(context, findings)
        executions = self.execution.run(context, decisions, self.broker)
        report = self.reporting.run(context, decisions, executions)

        self._remember(context, decisions)
        return TradingResult(run_id=context.run_id, decisions=decisions, report=report)

    def _recall_history(self, context: TradingContext) -> None:
        """Attach advisory prior-trade history. Never alters decisions."""
        if self.memory_store is None:
            return
        symbols = set(context.goals.watchlist) | set(context.goals.target_weights)
        symbols |= {p.symbol for p in context.portfolio.positions}
        symbols |= set(context.goals.news_targets)
        recall: dict[str, dict] = {}
        for symbol in sorted(symbols):
            summary = self.memory_store.recall_for_symbol(symbol)
            if summary.has_history:
                recall[symbol] = summary.as_enrichment()
        if recall:
            context.enrichment["memory_recall"] = recall

    def _remember(self, context: TradingContext, decisions) -> None:
        if self.memory_store is None:
            return
        proposals = {p.proposal_id: p for p in context.proposals}
        for decision in decisions:
            proposal = proposals.get(decision.proposal_id)
            if proposal is not None:
                self.memory_store.record_decision(context.run_id, proposal, decision)
