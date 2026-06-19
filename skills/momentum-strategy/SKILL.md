---
name: momentum-strategy
description: Follow strong price trends by buying names with high trailing returns and exiting positions that have rolled over. WHEN: "buy the trend", "momentum trade", "follow strong movers", "this stock is breaking out", "exit the downtrend", "trend-following proposal".
---

# Momentum Strategy

## Overview

A trend-following strategy. It compares the trailing return over a lookback window
to symmetric buy and sell thresholds: strong up-trends earn a small buy tranche,
and a held name in a strong down-trend is exited.

## When to Use

- During the strategy swarm, for symbols with enough price history.
- Do NOT use it without a sufficient bar history; skip such symbols.

## Inputs

| Input | Required | Description |
| --- | --- | --- |
| `snapshot.bars` | yes | Price bars covering at least the lookback window. |
| `config.strategy.momentum` | yes | Lookback length and buy/sell return thresholds. |

## Process

1. For each candidate symbol, take the last `lookback_bars` closing prices.
2. Compute the trailing return from the first to the last close.
3. If the return meets the buy threshold, propose a small buy tranche.
4. If the return meets the sell threshold and the name is held, propose an exit.

## Outputs

Buy or sell `OrderProposal` objects sized as a small tranche (buys) or a full exit
(sells), each citing the trailing return.

## Rationalizations

| Excuse | Rebuttal |
| --- | --- |
| "Buy more, the trend is obviously strong." | Sizing is a fixed small tranche; the risk guardian still caps exposure. |

## Red Flags

- A signal computed from fewer than the configured lookback bars.
- A buy that pushes a position over its cap (the guardian will block it).

## Verification

- Every proposal cites a trailing return beyond the relevant threshold.
- Proposals on tech-heavy names that breach limits are blocked downstream.
