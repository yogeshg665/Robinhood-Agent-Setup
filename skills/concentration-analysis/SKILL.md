---
name: concentration-analysis
description: Detect single-name over-concentration and propose trims that bring an outsized position back under the per-position cap. WHEN: "am I too concentrated", "trim my biggest position", "reduce single-name risk", "this stock is too large a share", "cut overweight position".
---

# Concentration Analysis

## Overview

A strategy that protects against single-name over-concentration. When a position's
weight exceeds the per-position cap, it proposes a whole-share sell that trims the
holding back to the cap.

## When to Use

- During the strategy swarm, on every run with held positions.
- Do NOT use it for sector limits; that is enforced by the risk guardian.

## Inputs

| Input | Required | Description |
| --- | --- | --- |
| `goals.max_position_pct` | yes | The maximum single-name weight. |
| `portfolio` | yes | Held positions and their current valuations. |

## Process

1. Compute each position's weight in the portfolio.
2. Identify positions whose weight exceeds the per-position cap.
3. Size a whole-share sell that brings the position back to the cap.
4. Emit one sell proposal per over-concentrated name.

## Outputs

Whole-share sell `OrderProposal` objects for over-concentrated positions, each
citing the current weight and the cap.

## Rationalizations

| Excuse | Rebuttal |
| --- | --- |
| "The winner keeps winning, let it ride past the cap." | Concentration risk is independent of conviction; trim to the cap. |

## Red Flags

- A trim that leaves the position still above the cap.
- A sell on a position already within the cap.

## Verification

- Each proposal reduces an over-cap position toward the limit.
- No proposal sells a within-cap position.
