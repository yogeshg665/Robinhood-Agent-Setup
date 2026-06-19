---
name: wash-sale-guard
description: Flag a buy that repurchases a security sold at a loss within the US IRS 30-day wash-sale window, so a disallowed loss is not triggered. Advisory by default; can be made blocking. WHEN: "wash sale", "30-day rule", "I just sold this at a loss", "tax-loss harvesting", "disallowed loss", "repurchase within 30 days", "IRS wash sale".
---

# Wash-Sale Guard

## Overview

A US tax-aware risk check. When a buy proposal targets a security that the account
sold at a loss within the wash-sale window, the check emits a finding so the agent
does not inadvertently trigger a disallowed loss under IRS rules. It is advisory by
default (non-blocking) because the rule affects tax treatment rather than trade
safety; it can be made blocking in configuration.

## When to Use

- During risk review, on every buy proposal.
- Do NOT apply it to sells; the rule concerns repurchases.

## Inputs

| Input | Required | Description |
| --- | --- | --- |
| `portfolio.recent_sales` | yes | Recently closed loss lots with `days_ago` and `realized_loss`. |
| `config.risk.wash_sale` | yes | Enabled flag, window days, severity, and blocking flag. |

## Process

1. Skip non-buy proposals and skip when the check is disabled.
2. Look for a recent loss sale of the same symbol within `window_days`.
3. If found, emit a finding citing the days since the sale and the realized loss.

## Outputs

At most one `RiskFinding` named `wash_sale_window`, advisory by default.

## Rationalizations

| Excuse | Rebuttal |
| --- | --- |
| "The loss is small, just rebuy now." | The rule applies regardless of size; flag it for review. |
| "Tax is not my problem." | A disallowed loss has a real after-tax cost; surface it. |

## Red Flags

- A repurchase within the window that reaches execution without review.
- Treating a tax flag as a trade-safety veto unless explicitly configured.

## Verification

- A buy within the window produces the finding; outside the window it does not.
- The decision routes to approval (or block, if configured) on a triggered finding.
