---
name: order-execution
description: Route allowed orders to the broker adapter; hold approval-required orders and never place blocked ones. Paper by default; live Robinhood MCP is gated. WHEN: "place the order", "execute the trade", "send to the broker", "submit allowed orders", "paper trade", "route to Robinhood agentic trading", "fill the order".
---

# Order Execution

## Overview

The execution stage. It sends only `ALLOW` decisions to the broker adapter; orders
held for human approval or blocked by the guardian are recorded but never placed.
The default adapter is a deterministic paper broker that simulates fills with no
real funds. Live Robinhood Agentic Trading (MCP) is a separate adapter gated behind
explicit safety switches.

## When to Use

- After decisioning, to act on the decisions.
- Do NOT place held or blocked orders; record their disposition only.

## Inputs

| Input | Required | Description |
| --- | --- | --- |
| `decisions` | yes | The `TradeDecision` list from the decision stage. |
| `config.execution` | yes | Mode (`paper` or `robinhood_mcp`) and the live-trading switch. |

## Process

1. Build the broker adapter from configuration; default to paper.
2. For each `ALLOW` decision, place the order and capture an execution report.
3. For `REQUIRE_APPROVAL`, record a held report; for `BLOCK`, record a blocked one.
4. Never raise on a single fill failure; record it and continue.

## Outputs

A list of `ExecutionReport` objects (filled, held, blocked, or rejected) with the
venue and any simulated fill price.

## Rationalizations

| Excuse | Rebuttal |
| --- | --- |
| "Just place the approval-required order to save a step." | Held orders need a human; placing them defeats the control. |
| "Enable live trading to test quickly." | Live requires both the MCP mode and the live switch, and is never the default. |

## Red Flags

- A held or blocked order that was placed.
- Live execution without both safety switches set.

## Verification

- Only `ALLOW` decisions produce placed orders.
- Held and blocked decisions appear in the reports with the correct status.
