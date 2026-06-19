---
name: dca-strategy
description: Spread a fixed periodic contribution evenly across a watchlist as whole-share buys, independent of short-term signals. WHEN: "dollar cost average", "DCA into my watchlist", "invest my weekly contribution", "steady accumulation", "scheduled buys", "spread my deposit across names".
---

# Dollar-Cost-Averaging Strategy

## Overview

A disciplined accumulation strategy. It divides a fixed periodic contribution evenly
across the watchlist (or the target-weight names) and turns each slice into a
whole-share buy, independent of short-term signals.

## When to Use

- During the strategy swarm, when a contribution amount and a watchlist exist.
- Do NOT use it to time the market; sizing ignores momentum and valuation.

## Inputs

| Input | Required | Description |
| --- | --- | --- |
| `goals.watchlist` | no | Symbols to accumulate; falls back to target-weight names. |
| `config.strategy.dca` | yes | Cadence and contribution amount. |

## Process

1. Divide the contribution amount evenly across the target symbols.
2. For each symbol, convert its slice into a whole number of shares.
3. Skip a symbol whose slice cannot buy at least one whole share.
4. Emit a small buy proposal for each remaining symbol.

## Outputs

Small whole-share buy `OrderProposal` objects, each citing the cadence and the
slice amount.

## Rationalizations

| Excuse | Rebuttal |
| --- | --- |
| "Skip DCA this period, the market looks expensive." | DCA is signal-independent by design; the schedule is the point. |

## Red Flags

- A proposal whose notional far exceeds its contribution slice.
- A buy of a fractional share.

## Verification

- Each proposal's notional is at or below its contribution slice.
- Symbols too expensive for one whole share are skipped.
