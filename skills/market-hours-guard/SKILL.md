---
name: market-hours-guard
description: Veto orders placed while the US regular session (NYSE/Nasdaq, 9:30-16:00 ET) is closed, based on the deterministic snapshot timestamp, including weekends and exchange holidays. WHEN: "is the market open", "after hours", "pre-market order", "weekend trade", "exchange holiday", "trading session", "can we trade right now", "market closed".
---

# Market-Hours Guard

## Overview

A US session gate. It converts the run's `as_of` timestamp to Eastern time and
classifies the session as open, extended, or closed, accounting for weekends and a
hardcoded NYSE holiday calendar. Orders outside the regular session are vetoed by
default; extended-hours trading is treated as closed unless explicitly allowed. When
the snapshot has no parseable timestamp the check passes, so offline fixtures are
unaffected.

## When to Use

- During risk review, on every proposal.
- Do NOT rely on wall-clock time; the check uses the deterministic snapshot timestamp.

## Inputs

| Input | Required | Description |
| --- | --- | --- |
| `snapshot.as_of` | yes | ISO-8601 timestamp of the run. |
| `config.risk.market_hours` | yes | `block_when_closed` and `allow_extended_hours` flags. |

## Process

1. Parse `as_of`; pass when it is absent or unparseable.
2. Convert to Eastern time using the standard US daylight-saving rule.
3. Reject non-trading days (weekends, NYSE holidays) and outside-session times.
4. Emit a blocking finding when closed and `block_when_closed` is set.

## Outputs

At most one `RiskFinding` named `market_closed`, blocking by default.

## Rationalizations

| Excuse | Rebuttal |
| --- | --- |
| "Queue it for the open, send it now." | The agent does not hold orders; a closed session is a veto. |
| "Extended hours is basically the same." | Extended hours is treated as closed unless explicitly allowed. |

## Red Flags

- An order transmitted on a weekend or exchange holiday.
- Enabling extended hours without confirming venue support.

## Verification

- A weekday-open timestamp passes; a weekend or holiday timestamp blocks.
- Decisions are deterministic for a fixed `as_of`.
