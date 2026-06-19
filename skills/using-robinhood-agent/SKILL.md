---
name: using-robinhood-agent
description: Meta-skill that routes an equities trading request to the correct workflow and defines the shared operating rules. Read this first. WHEN: "should I trade this", "rebalance my portfolio", "run the trading agent", "propose trades", "review my positions", "what would the agent do", "trade on this news", "which trading skill applies", "connect to Robinhood agentic trading".
---

# Using the Robinhood Agent

## Overview

This is the entry point for the pack. It explains the trading lifecycle, routes a
request to the right skill, and states the rules every skill must follow. The
agent proposes trades with a strategy swarm, but an independent risk guardian has
the final say. The default execution mode is paper (simulated) trading.

## When to Use

- At the start of any trading or portfolio request.
- When unsure which strategy or stage applies.

## Lifecycle

Run the stages in order. Each stage has a dedicated skill.

1. **Intake** — `portfolio-intake`: validate and normalize the account, positions,
   goals, and market snapshot.
2. **Enrichment** — `market-enrichment` and `company-news`: add derived metrics and
   a deterministic news-sentiment summary.
3. **Macro regime** — `macro-regime`: classify the US tape as risk-on, neutral, or
   risk-off (advisory; never changes a decision).
4. **Strategy swarm** — run every enabled strategy independently:
   - `rebalancing-strategy`
   - `concentration-analysis`
   - `momentum-strategy`
   - `mean-reversion-strategy`
   - `thematic-strategy`
   - `dca-strategy`
   - `company-news`
   - `relative-strength-strategy`
5. **Risk** — `risk-guardian` (plus `market-hours-guard` and `wash-sale-guard`):
   evaluate every proposal against the risk limits.
6. **Decisioning** — `trade-decisioning`: allow, require approval, or block.
7. **Execution** — `order-execution`: place allowed orders (paper by default).
8. **Reporting** — `trade-reporting`: produce the audit-ready report with the regime
   and a one-day alpha estimate versus SPY.

## Process

1. Identify the request type and locate the run input (account, positions, goals,
   market snapshot).
2. Run intake and enrichment to build the trading context.
3. Run every enabled strategy; each emits explainable signals and proposals.
4. Evaluate each proposal with the risk guardian, apply the decision policy, place
   allowed orders, and produce the report.

## Operating Rules

1. Every decision must be explainable and cite its risk findings.
2. Scoring and decisions are deterministic. A language model may enrich the
   narrative only; it must never change a score or a decision.
3. The risk guardian has final say. A blocking finding vetoes the order and cannot
   be overridden by a strategy's conviction.
4. Use pseudonymous account identifiers and synthetic market data. Never request or
   store real brokerage credentials in inputs.
5. Paper mode is the default. Live trading requires BOTH
   `EXECUTION_MODE=robinhood_mcp` AND `LIVE_TRADING_ENABLED=true`, and orders still
   pass the risk guardian and any human-approval gate.
6. Collective memory is optional and off by default. When enabled, recall and
   feedback remain deterministic, the memory signal is advisory, and threshold
   calibration is advisory only.
7. The macro-regime read is advisory. It frames strategy proposals (for example, it
   suppresses new relative-strength buys in a risk-off tape) but never changes a risk
   finding or a decision.

## Outputs

A routed workflow and a shared rule set that every downstream skill honors.

## Verification

- The correct lifecycle stage and skill are selected for the request.
- The operating rules above are applied throughout the run.
