# Execution and Safety

The agent defaults to paper (simulated) trading. Live trading is opt-in, gated, and
still passes through the risk guardian and any human-approval gate.

## Execution modes

- `paper` (default): a deterministic paper broker simulates fills at the limit price
  (for limit orders) or the estimated price, appends to a local JSON blotter, and
  involves no real funds.
- `robinhood_mcp`: routes allowed orders to Robinhood Agentic Trading through its MCP
  server. This adapter is a guarded stub in this repository and never trades by
  default.

## The two safety switches

Live trading requires BOTH of the following, and either one missing forces paper:

- `EXECUTION_MODE=robinhood_mcp`
- `LIVE_TRADING_ENABLED=true`

Even with both set, every order still passes the risk guardian, the decision policy,
and any approval gate. The risk guardian has final say.

## What is never placed

- `REQUIRE_APPROVAL` decisions are held for a human and recorded, never placed.
- `BLOCK` decisions are recorded and never placed.

## Defense in depth

- The guardian's order-notional, position-size, concentration, daily-loss, order-rate,
  price-deviation, buying-power, and PDT checks bound every order.
- A single fill failure is captured as a rejected report; it never crashes the run.
- Collective memory, when enabled, is advisory only and never changes a decision.

## Operational guidance

- Keep credentials out of run inputs and reports. Use environment variables for any
  endpoint or token.
- Treat the agentic account as isolated from the main portfolio, consistent with the
  platform's design.
- Start in paper mode, review the reasoning trail, and only consider live trading
  after the limits and outcomes are well understood.
