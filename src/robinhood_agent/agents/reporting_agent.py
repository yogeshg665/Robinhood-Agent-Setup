"""Reporting agent: produce an explainable, audit-ready trade report."""

from __future__ import annotations

from robinhood_agent.agents.base import Agent
from robinhood_agent.execution.base import ExecutionReport
from robinhood_agent.llm.client import LLMClient
from robinhood_agent.models.context import TradingContext
from robinhood_agent.models.decision import TradeDecision

_SYSTEM_PROMPT = (
    "You are a portfolio risk officer. Write a concise, factual summary of an "
    "automated trading run for an audit trail. Use neutral, professional language. "
    "Do not invent facts beyond the provided proposals, risk findings, and "
    "decisions."
)


class ReportingAgent(Agent):
    """Builds a structured report with a per-order reasoning trail."""

    name = "reporting"

    def __init__(self, config, llm_client: LLMClient | None = None) -> None:
        super().__init__(config)
        self.llm = llm_client or LLMClient()

    def run(
        self,
        context: TradingContext,
        decisions: list[TradeDecision],
        executions: list[ExecutionReport],
    ) -> dict:
        proposals = {p.proposal_id: p for p in context.proposals}
        decision_lines = []
        reasoning = []
        for decision in decisions:
            proposal = proposals.get(decision.proposal_id)
            decision_lines.append(
                {
                    "proposal_id": decision.proposal_id,
                    "symbol": decision.symbol,
                    "side": proposal.side.value if proposal else "",
                    "quantity": proposal.quantity if proposal else 0.0,
                    "strategy": proposal.strategy if proposal else "",
                    "estimated_notional": round(proposal.notional, 2) if proposal else 0.0,
                    "outcome": decision.outcome.value,
                    "risk_score": decision.risk_score,
                    "findings": [
                        {
                            "check": f.check,
                            "name": f.name,
                            "severity": f.severity,
                            "blocking": f.blocking,
                            "rationale": f.rationale,
                        }
                        for f in decision.findings
                    ],
                }
            )
            # Reasoning trail: one explicit line per decision.
            reasoning.append(f"{decision.symbol} [{decision.outcome.value}]: {decision.narrative}")

        deterministic = self._narrative(context, decisions, executions)
        narrative = self.llm.summarize(_SYSTEM_PROMPT, deterministic) or deterministic

        report = {
            "run_id": context.run_id,
            "as_of": context.enrichment.get("as_of"),
            "portfolio_value": round(context.portfolio.total_value, 2),
            "execution_venue": executions[0].venue if executions else "paper",
            "market_regime": context.enrichment.get("market_regime"),
            "benchmark": self._benchmark_block(context),
            "counts": self._counts(decisions, executions),
            "decisions": decision_lines,
            "executions": [
                {
                    "proposal_id": e.proposal_id,
                    "symbol": e.symbol,
                    "side": e.side,
                    "quantity": e.quantity,
                    "status": e.status,
                    "filled_price": e.filled_price,
                    "venue": e.venue,
                }
                for e in executions
            ],
            "reasoning": reasoning,
            "narrative": narrative,
        }
        self.logger.info("Generated report for %s", context.run_id)
        return report

    @staticmethod
    def _benchmark_block(context: TradingContext) -> dict:
        """Deterministic US benchmark comparison and one-day alpha estimate.

        The portfolio's one-day change is the value-weighted day change of its
        positions (from snapshot quotes). Alpha is that figure minus the benchmark's
        one-day change. All values are point-in-time estimates from the snapshot.
        """
        symbol = context.goals.benchmark or "SPY"
        bench_quote = context.snapshot.quote(symbol)
        bench_day = round(bench_quote.day_change_pct, 4) if bench_quote else None

        weighted_sum = 0.0
        weight_total = 0.0
        for position in context.portfolio.positions:
            quote = context.snapshot.quote(position.symbol)
            if quote is None or position.market_value <= 0.0:
                continue
            weighted_sum += position.market_value * quote.day_change_pct
            weight_total += position.market_value
        port_day = round(weighted_sum / weight_total, 4) if weight_total > 0.0 else None

        alpha = None
        if port_day is not None and bench_day is not None:
            alpha = round(port_day - bench_day, 4)

        return {
            "symbol": symbol,
            "benchmark_day_change_pct": bench_day,
            "portfolio_day_change_pct": port_day,
            "estimated_alpha_pct": alpha,
        }

    @staticmethod
    def _counts(decisions, executions) -> dict:
        outcomes: dict[str, int] = {}
        for decision in decisions:
            outcomes[decision.outcome.value] = outcomes.get(decision.outcome.value, 0) + 1
        filled = sum(1 for e in executions if e.status == "filled")
        return {
            "proposals": len(decisions),
            "by_outcome": outcomes,
            "filled": filled,
        }

    @staticmethod
    def _narrative(context, decisions, executions) -> str:
        counts: dict[str, int] = {}
        for decision in decisions:
            counts[decision.outcome.value] = counts.get(decision.outcome.value, 0) + 1
        filled = sum(1 for e in executions if e.status == "filled")
        lines = [
            f"Run {context.run_id} evaluated {len(decisions)} proposal(s) on a "
            f"portfolio valued at {context.portfolio.total_value:,.2f}.",
            "Decisions: "
            + ", ".join(f"{v} {k}" for k, v in sorted(counts.items()))
            + f". Filled {filled} order(s) at the {context.enrichment.get('as_of', 'run')} "
            f"snapshot.",
        ]
        for decision in decisions:
            lines.append(f"- {decision.narrative}")
        return "\n".join(lines)
