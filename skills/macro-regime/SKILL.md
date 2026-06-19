---
name: macro-regime
description: Classify the US market environment as risk-on, neutral, or risk-off from VIX, the 10Y-2Y Treasury curve, and the benchmark (SPY) trend. The regime is deterministic and advisory; it gates new relative-strength buys but never changes a risk finding or a decision. WHEN: "what is the market regime", "risk-on or risk-off", "is the tape healthy", "VIX is elevated", "yield curve inverted", "macro backdrop", "should we be defensive".
---

# Macro-Regime

## Overview

A deterministic "macro analyst" stage. It reads the run's macro indicators (VIX, the
10Y-2Y Treasury spread) and the benchmark (SPY) trend, then classifies the US tape as
`risk_on`, `neutral`, or `risk_off` with an explainable driver list. The result is
written to `enrichment.market_regime`. It is advisory: it can suppress new
relative-strength buys but never changes a risk finding or a trade decision.

## When to Use

- After enrichment and before the strategy swarm, once per run.
- Do NOT treat the regime as a hard control; the risk guardian remains the only veto.

## Inputs

| Input | Required | Description |
| --- | --- | --- |
| `snapshot.macro` | no | VIX, 10Y/2Y yields, fed funds, dollar index. |
| `snapshot.bars[benchmark]` | no | Benchmark bars for the trend signal. |
| `config.macro` | yes | VIX risk-on/off thresholds and the curve penalty toggle. |

## Process

1. Start a score at zero and collect drivers.
2. VIX at/above `vix_risk_off` subtracts; at/below `vix_risk_on` adds.
3. A rising benchmark adds; a falling benchmark subtracts.
4. An inverted 10Y-2Y curve subtracts when the penalty is enabled.
5. Score >= 2 is `risk_on`; score <= -2 is `risk_off`; otherwise `neutral`.

## Outputs

`enrichment.market_regime` with the regime, score, benchmark trend and day change,
VIX, the yield-curve spread, and the human-readable drivers.

## Rationalizations

| Excuse | Rebuttal |
| --- | --- |
| "Let the regime block this risky order." | The regime never blocks; only the risk guardian vetoes. |
| "Ignore the indicators, it feels risk-on." | Classification is deterministic from the inputs, not sentiment. |

## Red Flags

- Using the regime to override a blocking risk finding.
- A regime computed from indicators that are not part of the run snapshot.

## Verification

- The regime and its drivers are reproducible for identical inputs.
- Decisions are unchanged when the regime block is removed from the report.
