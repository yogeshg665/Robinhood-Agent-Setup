---
name: mean-reversion-strategy
description: Fade statistical extremes by buying oversold names and exiting overbought ones using a close-price z-score. WHEN: "buy the dip", "mean reversion trade", "this is oversold", "fade the spike", "revert to the mean", "z-score signal".
---

# Mean-Reversion Strategy

## Overview

A contrarian strategy. It computes a z-score of the current price against the mean
of a lookback window of closes. A deeply negative z-score (oversold) earns a small
buy tranche; a strongly positive z-score (overbought) exits a held position.

## When to Use

- During the strategy swarm, for symbols with enough price history.
- Do NOT use it when the price standard deviation is zero (no signal).

## Inputs

| Input | Required | Description |
| --- | --- | --- |
| `snapshot.bars` | yes | Price bars covering at least the lookback window. |
| `config.strategy.mean_reversion` | yes | Lookback length and buy/sell z-score thresholds. |

## Process

1. For each candidate symbol, compute the mean and standard deviation of the
   lookback closes.
2. Compute the z-score of the current price against that mean.
3. If the z-score is at or below the buy threshold, propose a small buy tranche.
4. If the z-score is at or above the sell threshold and the name is held, exit it.

## Outputs

Buy or sell `OrderProposal` objects sized as a small tranche (buys) or a full exit
(sells), each citing the z-score.

## Rationalizations

| Excuse | Rebuttal |
| --- | --- |
| "It is cheap, average down aggressively." | Sizing stays a small tranche; the guardian still enforces position limits. |

## Red Flags

- A z-score computed from an inconsistent price series (bars not matching the quote).
- A signal when standard deviation is zero.

## Verification

- Every proposal cites a z-score beyond the relevant threshold.
- Bars and quotes for a symbol are on the same price scale.
