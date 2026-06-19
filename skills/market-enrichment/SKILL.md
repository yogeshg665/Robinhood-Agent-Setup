---
name: market-enrichment
description: Derive deterministic market context for a trading run, including portfolio weights and an aggregated daily company-news sentiment summary. WHEN: "enrich the market context", "compute portfolio weights", "summarize the news for my holdings", "add derived metrics", "prepare context for the strategies".
---

# Market Enrichment

## Overview

The enrichment stage attaches derived, deterministic context that strategies
consume: per-symbol portfolio weights, total portfolio value, and an aggregated
news-sentiment summary for each target symbol. News is fetched through the
configured provider (offline by default) and scored with a fixed keyword lexicon.

## When to Use

- After intake and before the strategy swarm.
- Do NOT use it to make trade decisions; it only prepares inputs.

## Inputs

| Input | Required | Description |
| --- | --- | --- |
| `context` | yes | The `TradingContext` from intake. |
| `goals.news_targets` | no | Symbols to summarize daily news for. |

## Process

1. Resolve the news provider from configuration (offline serves the snapshot).
2. For each `news_targets` symbol, fetch headlines within the lookback window and
   score each deterministically to an average sentiment in [-1, 1].
3. Compute portfolio weights and total value.
4. Merge the derived metrics into `context.enrichment`, preserving any
   caller-provided values.

## Outputs

`context.enrichment` populated with `portfolio_weights`, `total_value`, and
`news_sentiment` (average sentiment, article count, and latest headline per
symbol).

## Rationalizations

| Excuse | Rebuttal |
| --- | --- |
| "Let the model read the news and decide sentiment." | Sentiment must be deterministic; use the fixed lexicon so runs reproduce. |

## Red Flags

- A news-sentiment value outside [-1, 1].
- Enrichment that depends on a live network call in the default offline mode.

## Verification

- The summarized news-target count matches the available news.
- Re-running on the same snapshot yields identical sentiment values.
