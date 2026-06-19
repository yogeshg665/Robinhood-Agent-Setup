---
name: risk-guardian
description: Evaluate every order proposal against deterministic risk limits and emit findings; the guardian can veto an order and has final say. WHEN: "check the risk", "is this order safe", "evaluate against limits", "risk review the trade", "will this breach a limit", "run the risk guardian", "position size check", "kill switch".
---

# Risk Guardian

## Overview

The independent control stage. It runs every risk check against each proposal and
emits findings with a severity, a blocking flag, and a rationale. The guardian has
final say: a blocking finding vetoes the order and cannot be overridden by a
strategy's conviction. Each check runs in isolation so one faulty check cannot
suppress the others.

## When to Use

- After the strategy swarm and before decisioning, on every proposal.
- Do NOT let any strategy bypass the guardian, including news-driven proposals.

## Inputs

| Input | Required | Description |
| --- | --- | --- |
| `proposals` | yes | The order proposals from the strategy swarm. |
| `config.risk` | yes | Market-hours, position-size, concentration, daily-loss, order-rate, price-deviation, buying-power, PDT, wash-sale, and liquidity limits. |

## Process

1. For each proposal, run every risk check with its order index.
2. Each check returns at most one finding (a severity 0-100, a blocking flag, and a
   rationale) or nothing.
3. Blocking checks include the US market-hours gate (see `market-hours-guard`), order
   notional and position size, sector concentration, the daily-loss kill switch (buys
   only), order rate, price deviation on limit orders, buying power, and the
   pattern-day-trader limit.
4. The wash-sale guard (see `wash-sale-guard`) and liquidity (volatility, spread, and
   average volume) are non-blocking by default but raise the risk score.
5. Collect findings keyed by proposal for the decision stage.

## Outputs

A mapping from each proposal to its list of `RiskFinding` objects.

## Rationalizations

| Excuse | Rebuttal |
| --- | --- |
| "The strategy is highly confident, skip the limit." | Conviction never overrides a limit; the guardian has final say. |
| "It is just over the cap, allow it." | A breach is a breach; the finding stands and may block the order. |

## Red Flags

- A proposal that reaches decisioning without being evaluated.
- A blocking finding being treated as advisory.

## Verification

- Every proposal has an evaluated findings list.
- Blocking findings are preserved intact for the decision stage.
