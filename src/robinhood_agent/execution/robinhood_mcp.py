"""Robinhood agentic-trading (MCP) adapter — disabled stub.

Robinhood's Agentic Trading lets a customer connect an AI agent to a dedicated
agentic account through an official Model Context Protocol (MCP) server. This
adapter is a deliberately disabled stub: it documents the integration seam but
refuses to place real orders unless the operator has explicitly enabled live
trading and supplied credentials.

To wire this up, implement ``place_order`` against the Robinhood Trading MCP
server using credentials read from the environment. Keep the live-trading safety
switch in place so the engine cannot place real orders by accident.

Reference: https://robinhood.com/us/en/support/agentic-trading/
"""

from __future__ import annotations

import os

from robinhood_agent.execution.base import BrokerAdapter, ExecutionReport
from robinhood_agent.models.proposal import OrderProposal
from robinhood_agent.utils.logging import get_logger

logger = get_logger(__name__)


class RobinhoodMcpBroker(BrokerAdapter):
    """Stub adapter for Robinhood agentic trading via MCP. Live trading disabled."""

    venue = "robinhood_mcp"

    def __init__(self, live_trading_enabled: bool = False) -> None:
        self.live_trading_enabled = live_trading_enabled
        self.endpoint = os.getenv("ROBINHOOD_MCP_ENDPOINT")
        self.api_key = os.getenv("ROBINHOOD_MCP_API_KEY")
        self.account_id = os.getenv("ROBINHOOD_AGENTIC_ACCOUNT_ID")

    def place_order(self, proposal: OrderProposal) -> ExecutionReport:
        if not self.live_trading_enabled:
            raise RuntimeError(
                "Live trading is disabled. Set LIVE_TRADING_ENABLED=true and "
                "EXECUTION_MODE=robinhood_mcp to enable real orders. The agent runs "
                "in paper mode by default."
            )
        if not (self.endpoint and self.api_key and self.account_id):
            raise RuntimeError(
                "Robinhood MCP credentials are not configured. Provide "
                "ROBINHOOD_MCP_ENDPOINT, ROBINHOOD_MCP_API_KEY, and "
                "ROBINHOOD_AGENTIC_ACCOUNT_ID via the environment."
            )
        # Intentionally not implemented: wiring a real broker connection is an
        # operator decision that must be made deliberately and reviewed.
        raise NotImplementedError(
            "RobinhoodMcpBroker.place_order is a stub. Implement the MCP order call "
            "here once you have reviewed Robinhood's agentic-trading integration "
            "docs and accepted the associated risks."
        )
