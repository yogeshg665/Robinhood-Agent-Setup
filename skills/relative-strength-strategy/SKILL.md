---
name: relative-strength-strategy
description: Trade US equities by their strength relative to the benchmark (SPY). Buy names that outperform the index over the lookback window and exit held names that lag, suppressing new buys in a risk-off regime. WHEN: "relative strength", "outperforming the S&P", "beating SPY", "leaders vs laggards", "buy the market leaders", "exit the laggards", "alpha vs benchmark".
---

# Relative-Strength Strategy

## Overview

A US-market strategy that ranks each watchlist name by its trailing return relative
to the benchmark (SPY by default). Names that meaningfully outperform the index earn
a small buy tranche; held names that meaningfully lag are exited. New buys are
suppressed when the macro-regime agent has classified the tape as risk-off. The
regime read is advisory and deterministic and never overrides a risk finding.

## When to Use

- During the strategy swarm, for symbols that have both their own and benchmark bars.
- Do NOT use it when the benchmark has no price history; the strategy returns nothing.

## Inputs

| Input | Required | Description |
| --- | --- | --- |
| `snapshot.bars[symbol]` | yes | Price bars for the candidate covering the lookback. |
| `snapshot.bars[benchmark]` | yes | Price bars for the benchmark (SPY). |
| `goals.benchmark` | no | Benchmark symbol; defaults to `config.benchmark.symbol`. |
| `enrichment.market_regime` | no | Advisory regime used to gate new buys. |
| `config.strategy.relative_strength` | yes | Lookback and outperform/underperform thresholds. |

## Process

1. Compute the benchmark trailing return over the lookback window.
2. For each candidate, compute its trailing return and the excess versus the benchmark.
3. If the excess meets the outperform threshold and the regime is not risk-off,
   propose a small buy tranche.
4. If the excess meets the underperform threshold and the name is held, propose an exit.

## Outputs

Buy or sell `OrderProposal` objects, each citing the candidate return, the benchmark
return, and the excess.

## Rationalizations

| Excuse | Rebuttal |
| --- | --- |
| "It is up a lot, buy it regardless of the index." | Strength is measured relative to SPY; absolute moves do not qualify. |
| "Override the risk-off regime, the name looks great." | Regime gating is deterministic; the guardian still has final say either way. |

## Red Flags

- A signal computed without benchmark bars.
- A buy proposed during a risk-off regime.

## Verification

- Every proposal cites the excess return versus the benchmark.
- New buys do not appear when `enrichment.market_regime.regime` is `risk_off`.
