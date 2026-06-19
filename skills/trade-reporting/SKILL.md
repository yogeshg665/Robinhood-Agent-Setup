---
name: trade-reporting
description: Produce an audit-ready report with a per-order reasoning trail, decision counts, execution outcomes, and a deterministic narrative. WHEN: "summarize the run", "explain the decisions", "produce the trade report", "audit trail", "what did the agent do and why", "report the executions".
---

# Trade Reporting

## Overview

The final stage. It assembles a structured, audit-ready report: per-order decisions
with their findings, decision counts, execution outcomes, and an explicit reasoning
trail. A deterministic narrative is always produced; an optional language model may
refine the wording without changing any fact.

## When to Use

- After execution, to close out the run.
- Do NOT let the optional model add facts not present in the decisions.

## Inputs

| Input | Required | Description |
| --- | --- | --- |
| `decisions` | yes | The `TradeDecision` list. |
| `executions` | yes | The `ExecutionReport` list. |
| `context` | yes | The run context for portfolio value and metadata. |

## Process

1. For each decision, record the symbol, side, quantity, strategy, notional,
   outcome, risk score, and findings.
2. Build a reasoning trail with one explicit line per decision.
3. Summarize decision counts by outcome and the number of filled orders.
4. Generate a deterministic narrative; optionally refine it with a model.

## Outputs

A report dictionary with `run_id`, counts, per-decision detail, executions, a
reasoning trail, and a narrative. Optionally written to an output directory.

## Rationalizations

| Excuse | Rebuttal |
| --- | --- |
| "Let the model summarize freely." | The narrative may be refined, but every fact must come from the decisions. |

## Red Flags

- A report whose counts disagree with the decisions.
- A narrative claiming a fill that did not occur.

## Verification

- The report's counts match the decisions and executions.
- The reasoning trail has one line per decision and cites the findings.
