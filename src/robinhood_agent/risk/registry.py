"""Registry that assembles the risk-guardian swarm."""

from __future__ import annotations

from robinhood_agent.risk.base import RiskCheck
from robinhood_agent.risk.buying_power import BuyingPowerCheck
from robinhood_agent.risk.concentration_limit import ConcentrationLimitCheck
from robinhood_agent.risk.daily_loss import DailyLossCheck
from robinhood_agent.risk.liquidity import LiquidityCheck
from robinhood_agent.risk.market_hours import MarketHoursCheck
from robinhood_agent.risk.order_rate import OrderRateCheck
from robinhood_agent.risk.pdt import PdtCheck
from robinhood_agent.risk.position_size import PositionSizeCheck
from robinhood_agent.risk.price_deviation import PriceDeviationCheck
from robinhood_agent.risk.wash_sale import WashSaleCheck
from robinhood_agent.utils.config import EngineConfig

_RISK_CHECK_TYPES: list[type[RiskCheck]] = [
    MarketHoursCheck,
    DailyLossCheck,
    OrderRateCheck,
    PositionSizeCheck,
    ConcentrationLimitCheck,
    BuyingPowerCheck,
    PdtCheck,
    PriceDeviationCheck,
    WashSaleCheck,
    LiquidityCheck,
]


def default_risk_checks(config: EngineConfig) -> list[RiskCheck]:
    """Instantiate the full risk-guardian swarm."""
    return [check_type(config) for check_type in _RISK_CHECK_TYPES]
