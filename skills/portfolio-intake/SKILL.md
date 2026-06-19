---
name: portfolio-intake
description: Validate and normalize a trading run's account, positions, goals, and market snapshot into a single trading context. WHEN: "load my portfolio", "start a trading run", "validate these positions", "normalize the account", "prepare the trading context", "ingest the market snapshot".
---

# Portfolio Intake

## Overview

The first stage of the lifecycle. It loads the account, positions, investor goals,
and the point-in-time market snapshot, fills in missing position metadata from the
snapshot, and produces the `TradingContext` every later stage consumes.

## When to Use

- At the start of every trading run, before enrichment or strategy generation.
- Do NOT use it to fetch live market data; inputs are a self-contained snapshot.

## Inputs

| Input | Required | Description |
| --- | --- | --- |
| `account` | yes | Pseudonymous account id, cash, buying power, start-of-day equity, day-trade count. |
| `positions` | yes | Held symbols with quantity, average cost, and (optional) sector and price. |
| `goals` | yes | Risk tolerance, target weights, themes, watchlist, news targets, and limits. |
| `market` | yes | Snapshot of instruments, quotes, price bars, and company news. |

## Process

1. Parse the account and positions into validated models.
2. Parse goals and the market snapshot (instruments, quotes, bars, news).
3. Hydrate each position's sector and current price from the snapshot when missing.
4. Assign a unique `run_id` and assemble the `TradingContext`.

## Outputs

A `TradingContext` with the portfolio, goals, snapshot, and an empty signal,
proposal, and enrichment workspace for later stages.

## Rationalizations

| Excuse | Rebuttal |
| --- | --- |
| "The position price is missing, just assume cost basis." | Hydrate from the snapshot quote so valuations and weights are correct. |

## Red Flags

- Negative cash, quantities, or prices.
- A position symbol with no instrument or quote in the snapshot.

## Verification

- The context reports the expected position and goal-weight counts.
- Every position has a non-zero current price or a documented reason it does not.
