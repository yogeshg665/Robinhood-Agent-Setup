"""Factory that selects the broker adapter from configuration."""

from __future__ import annotations

from robinhood_agent.execution.base import BrokerAdapter
from robinhood_agent.execution.paper import PaperBroker
from robinhood_agent.execution.robinhood_mcp import RobinhoodMcpBroker
from robinhood_agent.utils.config import EngineConfig
from robinhood_agent.utils.logging import get_logger

logger = get_logger(__name__)


def build_broker(config: EngineConfig) -> BrokerAdapter:
    """Return the configured broker, defaulting to the safe paper broker.

    The live Robinhood path is only selected when execution mode is
    ``robinhood_mcp`` AND live trading is explicitly enabled. Any other combination
    falls back to paper mode.
    """
    execution = config.execution
    if execution.mode == "robinhood_mcp" and execution.live_trading_enabled:
        logger.warning("LIVE trading selected via Robinhood MCP adapter.")
        return RobinhoodMcpBroker(live_trading_enabled=True)
    if execution.mode == "robinhood_mcp":
        logger.warning(
            "Execution mode is robinhood_mcp but live trading is disabled; "
            "using paper broker."
        )
    return PaperBroker(state_path=execution.paper_state_path)
