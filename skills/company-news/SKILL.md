---
name: company-news
description: Turn aggregated daily company-news sentiment into a small, deterministic directional trade proposal. WHEN: "trade on this news", "act on the headline", "buy on positive news", "trim on negative news", "news-driven trade", "sentiment-based proposal".
---

# Company News

## Overview

A strategy that reads the deterministic news-sentiment summary produced by market
enrichment and turns strong sentiment into a small directional proposal. It
performs no network I/O, so it stays reproducible; news can only nudge proposals,
never risk decisions.

## When to Use

- During the strategy swarm, when `news_targets` have recent headlines.
- Do NOT use raw model interpretation of headlines; rely on the scored summary.

## Inputs

| Input | Required | Description |
| --- | --- | --- |
| `context.enrichment["news_sentiment"]` | yes | Per-symbol average sentiment, article count, latest headline. |
| `config.strategy.news` | yes | Positive and negative strength thresholds. |

## Process

1. For each summarized symbol, read the average sentiment and article count.
2. If the average is at or above the positive strength threshold, propose a small
   buy tranche.
3. If the average is at or below the negative strength threshold and the symbol is
   held, propose reducing the position.
4. Attach the sentiment evidence to every signal and proposal.

## Outputs

At most one buy or sell `OrderProposal` per symbol, each citing the average
sentiment and article count.

## Rationalizations

| Excuse | Rebuttal |
| --- | --- |
| "One mildly positive headline justifies a large buy." | Only strong aggregate sentiment qualifies, and sizing is a small fixed tranche. |

## Red Flags

- A proposal generated from zero articles.
- Sizing that ignores the small-tranche cap.

## Verification

- Every proposal cites its sentiment and article count.
- The risk guardian still evaluates each proposal; news never bypasses it.
