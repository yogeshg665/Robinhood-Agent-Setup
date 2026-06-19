"""Base class for lifecycle agents."""

from __future__ import annotations

from robinhood_agent.utils.config import EngineConfig
from robinhood_agent.utils.logging import get_logger


class Agent:
    """Common base providing config and a logger."""

    name: str = "agent"

    def __init__(self, config: EngineConfig) -> None:
        self.config = config
        self.logger = get_logger(f"robinhood_agent.agents.{self.name}")
