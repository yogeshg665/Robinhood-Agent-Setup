# AGENTS.md

Operating guide for AI agents working in this repository. This file defines how to
discover, invoke, and extend the AI Robinhood Agent skills.

## What This Repository Provides

A pack of Agent Skills that propose and govern equities trades, plus a deterministic
Python engine that implements the same logic and serves as the executable reference
for every skill. A swarm of strategies proposes orders; an independent risk guardian
has final say.

- `skills/` contains one folder per skill, each with a `SKILL.md`.
- `agents/` contains specialist personas.
- `references/` contains the strategy playbook, risk limits, US market conventions,
  US data sources, safety, MCP integration, and memory notes.
- `src/robinhood_agent/` is the executable engine the skills describe.

## How to Start

1. Read `skills/using-robinhood-agent/SKILL.md`. It is the meta-skill that routes a
   request to the correct workflow and defines the shared rules.
2. Run the lifecycle in order: intake, enrichment, macro regime, strategy swarm,
   risk, decision, execution, reporting.

## Operating Rules

1. Decisions must be explainable and cite their risk findings.
2. Scoring and decisions must be deterministic. A language model may enrich the
   narrative only; it must never change a score or a decision.
3. The risk guardian has final say. A blocking finding vetoes the order and cannot
   be overridden by a strategy's conviction.
4. Use pseudonymous account identifiers and synthetic market data. Never request or
   store real brokerage credentials in inputs.
5. Paper mode is the default. Live trading requires BOTH
   `EXECUTION_MODE=robinhood_mcp` AND `LIVE_TRADING_ENABLED=true`, and every order
   still passes the risk guardian and any human-approval gate.
6. Collective memory is optional and off by default. When enabled, recall and
   feedback remain deterministic, the memory signal is advisory, and threshold
   calibration is advisory only. See `references/memory-and-learning.md`.
7. The macro-regime read (risk-on / neutral / risk-off) is advisory. It frames
   strategy proposals but never changes a risk finding or a decision.

## Markets

US equities. SPY is the default benchmark for relative strength and the one-day
alpha estimate. US-specific controls (NYSE/Nasdaq session hours, the FINRA
pattern-day-trader limit, T+1 buying-power buffering, and the IRS 30-day wash-sale
rule) are encoded as deterministic checks. See `references/us-market-conventions.md`.

## Architecture

The engine runs as a small agent swarm coordinated by an orchestrator:

- Intake and enrichment agents build the trading context.
- A macro-regime agent classifies the US tape (advisory only).
- A strategy swarm runs every enabled strategy independently and isolates failures:
  rebalancing, concentration, momentum, mean reversion, thematic, dollar-cost
  averaging, company news, and relative strength versus SPY.
- A risk-guardian swarm evaluates every proposal with ten deterministic checks
  (market hours, daily loss, order rate, position size, concentration, buying power,
  pattern-day-trader, price deviation, wash sale, liquidity); it can veto an order.
- A decision agent applies the policy; an execution agent places only allowed orders;
  a reporting agent emits the audit trail, the regime, and a one-day alpha estimate.

## Running the Engine

```bash
python -m pip install -e ".[dev]"
python -m robinhood_agent.cli run data/samples/sample_run.json --output output
pytest -q
python scripts/validate_skills.py
```

## Adding a Skill

1. Copy `template/SKILL.md` into a new folder under `skills/`.
2. Set `name` to match the folder and write a complete `description` with trigger
   phrases.
3. Fill in Overview, When to Use, Process, and Verification at minimum.
4. If the skill is executable, add the implementation under
   `src/robinhood_agent/` and register it (a strategy in `strategies/registry.py`
   or a check in `risk/registry.py`).
5. Run `python scripts/validate_skills.py` and `pytest -q`.

## Conventions

- Skill folder names are lowercase with hyphens and match the `name` field.
- Each strategy emits explainable signals and proposals; each risk check emits at
  most one finding with a severity, a blocking flag, and a rationale.
- Configuration lives in `config/config.yaml`; do not hardcode thresholds.
