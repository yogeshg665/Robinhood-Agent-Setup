"""Registry that assembles the enabled strategy swarm."""

from __future__ import annotations

from robinhood_agent.strategies.base import Strategy
from robinhood_agent.strategies.company_news import CompanyNewsStrategy
from robinhood_agent.strategies.concentration import ConcentrationStrategy
from robinhood_agent.strategies.dca import DollarCostAveragingStrategy
from robinhood_agent.strategies.mean_reversion import MeanReversionStrategy
from robinhood_agent.strategies.momentum import MomentumStrategy
from robinhood_agent.strategies.rebalancing import RebalancingStrategy
from robinhood_agent.strategies.relative_strength import RelativeStrengthStrategy
from robinhood_agent.strategies.thematic import ThematicStrategy
from robinhood_agent.utils.config import EngineConfig

# Strategy type keyed by the toggle attribute that enables it.
_STRATEGY_TYPES: list[tuple[str, type[Strategy]]] = [
    ("rebalancing", RebalancingStrategy),
    ("concentration", ConcentrationStrategy),
    ("momentum", MomentumStrategy),
    ("mean_reversion", MeanReversionStrategy),
    ("thematic", ThematicStrategy),
    ("dca", DollarCostAveragingStrategy),
    ("company_news", CompanyNewsStrategy),
    ("relative_strength", RelativeStrengthStrategy),
]


def default_strategies(config: EngineConfig) -> list[Strategy]:
    """Instantiate every strategy enabled by the configuration toggles."""
    toggles = config.strategy.toggles
    return [
        strategy_type(config)
        for toggle_name, strategy_type in _STRATEGY_TYPES
        if getattr(toggles, toggle_name, True)
    ]
