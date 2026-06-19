# US Market Conventions

The agent targets US equities and encodes several US-specific rules as deterministic
controls. These are guardrails, not tax or legal advice; confirm current rules with a
qualified professional and the relevant regulator (SEC, FINRA, IRS).

## Trading sessions (NYSE / Nasdaq)

- Regular session: 9:30-16:00 ET on trading days.
- Pre-market and after-hours are treated as closed unless extended hours are
  explicitly enabled (`risk.market_hours.allow_extended_hours`).
- Weekends and the NYSE holiday calendar are non-trading days. The market-hours guard
  derives the session from the snapshot timestamp in Eastern time, applying the
  standard US daylight-saving rule.

## Pattern Day Trader (PDT) rule

- FINRA's PDT rule limits accounts under the equity minimum to a bounded number of
  day trades in a rolling five-business-day window.
- The PDT check blocks a proposal that would exceed the configured day-trade budget
  (`risk.pdt.max_day_trades`), using the account's reported `day_trades_used`.

## Settlement (T+1)

- US equities settle on a T+1 basis. Buying power and the cash buffer should reflect
  unsettled proceeds; the buying-power check enforces a configurable cash buffer
  (`risk.buying_power.cash_buffer_pct`) so the account does not over-commit.

## Wash-sale rule (IRS 30 days)

- Selling a security at a loss and repurchasing the same or a substantially identical
  security within 30 days disallows the loss for tax purposes.
- The wash-sale guard flags a buy that repurchases a recent loss sale within the
  window (`risk.wash_sale.window_days`). It is advisory by default because it affects
  tax treatment rather than trade safety; it can be made blocking.

## Benchmark and alpha

- SPY (the S&P 500 ETF) is the default US benchmark for relative strength and a
  deterministic one-day alpha estimate in the report.
- Alpha here is the portfolio's value-weighted one-day change minus the benchmark's
  one-day change from the snapshot — a point-in-time estimate, not a backtested
  return.

## Order-handling guards

- A per-order notional cap and a single-name weight cap bound every order
  (fat-finger and concentration protection).
- A sector-concentration cap bounds aggregate exposure by sector.
- An order-rate throttle bounds the number of orders per run.
- A limit-price deviation guard rejects limit prices far from the last trade.

## Scope and disclaimers

- Equities only; the Robinhood Agentic Trading beta is equities only.
- All bundled data is synthetic. Paper mode is the default; live trading requires two
  explicit switches and still passes the risk guardian.
- Nothing here is investment, tax, or legal advice, and the project is not affiliated
  with or endorsed by Robinhood, any exchange, or any regulator.
