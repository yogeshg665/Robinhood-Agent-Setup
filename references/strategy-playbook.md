# Strategy Playbook

A reference for the strategy swarm. Each strategy is independent, deterministic, and
emits explainable signals and proposals. The risk guardian evaluates every proposal
afterward; nothing here bypasses it.

## Macro Regime (context, not a strategy)

Before the swarm runs, a deterministic macro-regime read classifies the US tape as
risk-on, neutral, or risk-off from VIX, the 10Y-2Y Treasury spread, and the SPY
trend. The regime is advisory: it frames strategy proposals (for example, it
suppresses new relative-strength buys when risk-off) but never changes a risk finding
or a decision.

## Rebalancing

- Goal: keep holdings near their `target_weights`.
- Trigger: a holding's weight drifts beyond the tolerance band.
- Action: a whole-share buy (underweight) or sell (overweight) sized to close the
  gap, subject to a minimum trade notional. Sells are capped at the held quantity.

## Concentration

- Goal: limit single-name risk.
- Trigger: a position's weight exceeds the per-position cap.
- Action: a whole-share sell that trims the position back to the cap.

## Momentum

- Goal: follow strong trends.
- Trigger: the trailing return over the lookback window meets a buy or sell threshold.
- Action: a small buy tranche for strong up-trends; a full exit for a held name in a
  strong down-trend.

## Mean Reversion

- Goal: fade statistical extremes.
- Trigger: the close-price z-score crosses the buy (oversold) or sell (overbought)
  threshold.
- Action: a small buy tranche when oversold; a full exit of a held name when
  overbought.

## Thematic

- Goal: build exposure to conviction themes.
- Trigger: a theme (sector) has instruments not yet held.
- Action: initiate whole-share positions sized to the per-name target, up to a cap on
  new names per run.

## Dollar-Cost Averaging

- Goal: disciplined, signal-independent accumulation.
- Trigger: a periodic contribution and a watchlist.
- Action: divide the contribution evenly and place small whole-share buys.

## Company News

- Goal: react to strong, deterministic daily-news sentiment.
- Trigger: aggregated sentiment for a target symbol crosses the positive or negative
  strength threshold.
- Action: a small buy on strongly positive sentiment; a reduction of a held name on
  strongly negative sentiment.

## Relative Strength (vs SPY)

- Goal: favor US names outperforming the benchmark and exit clear laggards.
- Trigger: a name's trailing return minus the benchmark's trailing return over the
  lookback window crosses the outperform or underperform threshold.
- Action: a small buy tranche for a strong outperformer (suppressed when the regime is
  risk-off); a full exit of a held name that materially underperforms.
- Benchmark: `goals.benchmark` or `config.benchmark.symbol` (default SPY); the
  benchmark symbol is never traded by this strategy.

## Sizing Discipline

All buy tranches are small, fixed fractions of portfolio value. No strategy upsizes
on conviction. Position and order limits are enforced separately by the guardian.
