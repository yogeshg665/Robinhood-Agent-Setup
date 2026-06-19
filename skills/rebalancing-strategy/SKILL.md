---
name: rebalancing-strategy
description: Propose trades that move the portfolio back toward its target weights when a holding drifts beyond the tolerance band. WHEN: "rebalance my portfolio", "drift back to target", "my weights are off", "bring positions to target allocation", "trim overweight and add underweight".
---

# Rebalancing Strategy

## Overview

A strategy that drives the portfolio toward the investor's `target_weights`. When a
holding's weight drifts beyond the tolerance band, it proposes a whole-share buy or
sell sized to close the gap, subject to a minimum trade notional.

## When to Use

- During the strategy swarm, whenever `target_weights` are defined.
- Do NOT use it to chase performance; it only restores target allocations.

## Inputs

| Input | Required | Description |
| --- | --- | --- |
| `goals.target_weights` | yes | Desired weight per symbol. |
| `config.strategy.rebalancing` | yes | Drift tolerance and minimum trade notional. |

## Process

1. For each target symbol, compute the current weight and its drift from target.
2. Skip symbols whose drift is within the tolerance band.
3. Size a buy (underweight) or sell (overweight) to close the gap in whole shares.
4. Skip trades below the minimum notional; cap sells at the held quantity.

## Outputs

Whole-share buy or sell `OrderProposal` objects that reduce target drift, each
citing the current and target weights.

## Rationalizations

| Excuse | Rebuttal |
| --- | --- |
| "It is only slightly overweight, rebalance anyway." | Inside the tolerance band, churn and costs outweigh the benefit; skip it. |

## Red Flags

- A sell larger than the held quantity.
- A proposal below the minimum trade notional.

## Verification

- Each proposal moves the holding toward its target weight.
- No proposal trades a symbol already within tolerance.
