# Robinhood MCP Integration

This document explains how the agent is designed to connect to Robinhood Agentic
Trading and why the integration is disabled by default in this repository.

## Background

Robinhood offers Agentic Trading, which exposes a Model Context Protocol (MCP) server
so an AI agent can place equities trades into a dedicated agentic account that is kept
isolated from the main portfolio. The platform provides built-in controls — push
notifications, an activity feed, instant disconnect, trade previews, and manual
approval — and discloses that Robinhood does not control, supervise, monitor,
recommend, or audit third-party AI agents. The current beta is equities only.

Always confirm the current capabilities and terms in the official documentation at
`robinhood.com/us/en/support/agentic-trading` before enabling anything.

## How this agent maps onto it

- The `robinhood_mcp` broker adapter is the integration point. In this repository it
  is a guarded stub: it raises rather than transmitting any order.
- The adapter reads its endpoint and credentials from environment variables only
  (for example, `ROBINHOOD_MCP_ENDPOINT`, `ROBINHOOD_MCP_API_KEY`,
  `ROBINHOOD_AGENTIC_ACCOUNT_ID`). Nothing is hardcoded and nothing is committed.
- The agent's own risk guardian is an additional layer on top of the platform's
  controls. An order must pass the guardian and the decision policy before the
  adapter is ever called.

## Enabling live trading (operator action)

Live trading requires deliberate operator action and is never the default:

1. Set `EXECUTION_MODE=robinhood_mcp`.
2. Set `LIVE_TRADING_ENABLED=true`.
3. Provide the endpoint and credentials via environment variables.
4. Implement the adapter's transport against the current MCP contract.

Even then, every order still passes the risk guardian, the decision policy, and any
human-approval gate. The agentic account should remain isolated from the main
portfolio.

## Safety posture

- Paper mode is the default and the recommended starting point.
- The risk guardian has final say and cannot be overridden by a strategy.
- Use the platform's manual-approval and trade-preview controls in addition to the
  agent's own approval gate.
- Keep the human in the loop. Treat agentic execution as assistive, not autonomous.
