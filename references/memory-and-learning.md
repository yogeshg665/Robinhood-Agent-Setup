# Memory and Learning

Collective memory is optional and off by default. When enabled, it lets the agent
remember prior decisions, accept analyst feedback, and suggest a calibrated approval
threshold. It never changes a score or a decision at run time.

## What is stored

A local SQLite store records one row per decided proposal: the proposal id, run id,
symbol, strategy, side, outcome, risk score, narrative, an analyst label, and
timestamps. No real customer or brokerage data is stored; identifiers are
pseudonymous and market data is synthetic.

## Recall (advisory only)

At the start of a run, the agent can recall prior history for the symbols in scope
and attach a summary (counts of prior good and bad trades, blocked count, and the most
recent outcome) to `context.enrichment["memory_recall"]`. This is informational. It
does not feed the risk score and does not alter any decision.

## Feedback

An analyst can label a recorded decision as a good trade or a bad trade. Labels are
stored against the proposal id and preserved across subsequent runs. Feedback is
deterministic: the same label always produces the same stored state.

## Calibration (advisory only)

From the labeled history, the agent can suggest an approval threshold:

- If the good and bad trades are separable by risk score, suggest the midpoint
  between the highest-scoring good trade and the lowest-scoring bad trade.
- If they overlap, suggest the highest-scoring good trade.
- At least one good and one bad label are required to make a suggestion.

The suggestion is advisory. An operator must review it and edit
`config/config.yaml` (or set `RISK_APPROVAL_THRESHOLD`) to adopt it. The agent never
self-adjusts its limits.

## Determinism guarantees

- Recall and feedback are deterministic.
- The memory signal is never blocking and never critical.
- Calibration is advisory; thresholds change only by explicit operator action.
