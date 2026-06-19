---
name: trade-decisioning
description: Map a proposal's risk findings to a deterministic decision: allow, require human approval, or block. WHEN: "decide on the trade", "allow or block", "should this need approval", "apply the decision policy", "final trade decision", "approve or veto the order".
---

# Trade Decisioning

## Overview

The policy stage. It maps each proposal's risk findings to one deterministic
outcome: allow, require human approval, or block. The aggregate risk score is the
maximum finding severity, so the decision is conservative and reproducible.

## When to Use

- After the risk guardian, on every proposal.
- Do NOT let a language model alter the outcome; the mapping is deterministic.

## Inputs

| Input | Required | Description |
| --- | --- | --- |
| `findings_by_proposal` | yes | Risk findings per proposal from the guardian. |
| `config.decision_policy` | yes | Approval threshold, block-on-critical, and manual-approval switches. |

## Process

1. For each proposal, compute the risk score as the maximum finding severity.
2. If any finding is blocking and block-on-critical is enabled, decide BLOCK.
3. Otherwise, if manual approval is forced or the score meets the approval
   threshold, decide REQUIRE_APPROVAL.
4. Otherwise decide ALLOW.
5. Record the reasons (the finding rationales) and a deterministic narrative.

## Outputs

A `TradeDecision` per proposal with an outcome, the risk score, the findings, the
reasons, and a narrative.

## Rationalizations

| Excuse | Rebuttal |
| --- | --- |
| "Average the severities so a single breach does not dominate." | The maximum is used on purpose; the worst risk governs the decision. |
| "Auto-approve to keep things moving." | Scores at or above the threshold require a human; do not bypass it. |

## Red Flags

- A blocking finding that does not produce a BLOCK.
- A decision whose reasons do not match its findings.

## Verification

- Outcomes follow the policy exactly for every proposal.
- Each decision's narrative and reasons are consistent with its findings.
