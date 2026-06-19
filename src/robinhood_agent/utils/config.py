"""Engine configuration models and loader.

Configuration is loaded from ``config/config.yaml`` and may be overridden by a
small set of environment variables. Thresholds are never hardcoded in logic; they
live here so behavior is auditable and reproducible.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field


class DecisionPolicy(BaseModel):
    """How risk findings map to a trade decision."""

    approval_threshold: float = 40.0  # aggregate risk score requiring human approval
    block_on_critical: bool = True  # a blocking finding always vetoes the order
    require_manual_approval: bool = False  # force approval for every order


class ExecutionConfig(BaseModel):
    """Execution mode and the live-trading safety switch."""

    mode: str = "paper"  # paper | robinhood_mcp
    live_trading_enabled: bool = False
    paper_state_path: str = ".paper_state/blotter.json"


class StrategyToggles(BaseModel):
    """Enable/disable individual strategies."""

    rebalancing: bool = True
    concentration: bool = True
    momentum: bool = True
    mean_reversion: bool = True
    thematic: bool = True
    dca: bool = True
    company_news: bool = True
    relative_strength: bool = True


class RebalancingConfig(BaseModel):
    drift_tolerance_pct: float = 5.0  # rebalance when weight drifts beyond this band
    min_trade_notional: float = 100.0


class MomentumConfig(BaseModel):
    lookback_bars: int = 20
    buy_return_pct: float = 8.0
    sell_return_pct: float = -8.0


class MeanReversionConfig(BaseModel):
    lookback_bars: int = 20
    zscore_buy: float = -2.0
    zscore_sell: float = 2.0


class ThematicConfig(BaseModel):
    per_name_target_pct: float = 0.05
    max_new_names: int = 3


class DcaConfig(BaseModel):
    cadence: str = "weekly"
    contribution_amount: float = 250.0


class RelativeStrengthConfig(BaseModel):
    """Relative strength versus the US benchmark (default SPY)."""

    lookback_bars: int = 20
    outperform_pct: float = 5.0  # excess trailing return vs benchmark to buy
    underperform_pct: float = -5.0  # excess trailing return vs benchmark to exit
    per_name_target_pct: float = 0.05


class NewsConfig(BaseModel):
    provider: str = "offline"  # offline | live
    lookback_hours: int = 24
    positive_strength: float = 0.6
    negative_strength: float = 0.6


class PositionSizeConfig(BaseModel):
    max_position_pct: float = 0.20
    max_order_notional: float = 25000.0


class ConcentrationLimitConfig(BaseModel):
    max_sector_pct: float = 0.40


class DailyLossConfig(BaseModel):
    max_daily_loss_pct: float = 5.0  # kill-switch on intraday drawdown


class OrderRateConfig(BaseModel):
    max_orders_per_run: int = 10


class PriceDeviationConfig(BaseModel):
    max_limit_deviation_pct: float = 10.0  # fat-finger guard vs. last price


class BuyingPowerConfig(BaseModel):
    cash_buffer_pct: float = 0.02


class PdtConfig(BaseModel):
    max_day_trades: int = 3  # rolling 5-day day-trade limit under PDT rules


class LiquidityConfig(BaseModel):
    max_volatility: float = 0.08  # daily return stdev ceiling
    max_spread_pct: float = 1.0
    min_average_volume: float = 100000.0


class WashSaleConfig(BaseModel):
    """US wash-sale awareness (IRS 30-day rule). Advisory by default."""

    enabled: bool = True
    window_days: int = 30
    severity: float = 50.0
    blocking: bool = False


class MarketHoursConfig(BaseModel):
    """US (NYSE/Nasdaq) trading-session gate based on the snapshot timestamp."""

    block_when_closed: bool = True
    allow_extended_hours: bool = False


class BenchmarkConfig(BaseModel):
    """US market benchmark used for relative strength and alpha estimation."""

    symbol: str = "SPY"
    lookback_bars: int = 20


class MacroRegimeConfig(BaseModel):
    """Deterministic US market-regime classifier thresholds."""

    enabled: bool = True
    vix_risk_off: float = 25.0  # VIX at/above signals risk-off
    vix_risk_on: float = 15.0  # VIX at/below signals risk-on
    inverted_curve_penalty: bool = True  # penalize an inverted 10Y-2Y curve


class MarketDataConfig(BaseModel):
    """Market-data provider selection. Live US sources are gated stubs."""

    provider: str = "offline"  # offline | live


class MemoryConfig(BaseModel):
    enabled: bool = False
    path: str = ".agent_memory/memory.db"


class RiskConfig(BaseModel):
    position_size: PositionSizeConfig = Field(default_factory=PositionSizeConfig)
    concentration: ConcentrationLimitConfig = Field(default_factory=ConcentrationLimitConfig)
    daily_loss: DailyLossConfig = Field(default_factory=DailyLossConfig)
    order_rate: OrderRateConfig = Field(default_factory=OrderRateConfig)
    price_deviation: PriceDeviationConfig = Field(default_factory=PriceDeviationConfig)
    buying_power: BuyingPowerConfig = Field(default_factory=BuyingPowerConfig)
    pdt: PdtConfig = Field(default_factory=PdtConfig)
    liquidity: LiquidityConfig = Field(default_factory=LiquidityConfig)
    wash_sale: WashSaleConfig = Field(default_factory=WashSaleConfig)
    market_hours: MarketHoursConfig = Field(default_factory=MarketHoursConfig)


class StrategyConfig(BaseModel):
    toggles: StrategyToggles = Field(default_factory=StrategyToggles)
    rebalancing: RebalancingConfig = Field(default_factory=RebalancingConfig)
    momentum: MomentumConfig = Field(default_factory=MomentumConfig)
    mean_reversion: MeanReversionConfig = Field(default_factory=MeanReversionConfig)
    thematic: ThematicConfig = Field(default_factory=ThematicConfig)
    dca: DcaConfig = Field(default_factory=DcaConfig)
    news: NewsConfig = Field(default_factory=NewsConfig)
    relative_strength: RelativeStrengthConfig = Field(
        default_factory=RelativeStrengthConfig
    )


class EngineConfig(BaseModel):
    """Top-level engine configuration."""

    decision_policy: DecisionPolicy = Field(default_factory=DecisionPolicy)
    execution: ExecutionConfig = Field(default_factory=ExecutionConfig)
    strategy: StrategyConfig = Field(default_factory=StrategyConfig)
    risk: RiskConfig = Field(default_factory=RiskConfig)
    benchmark: BenchmarkConfig = Field(default_factory=BenchmarkConfig)
    macro: MacroRegimeConfig = Field(default_factory=MacroRegimeConfig)
    market_data: MarketDataConfig = Field(default_factory=MarketDataConfig)
    memory: MemoryConfig = Field(default_factory=MemoryConfig)


def _apply_env_overrides(config: EngineConfig) -> EngineConfig:
    """Apply a small set of environment overrides to the loaded config."""
    approval = os.getenv("RISK_APPROVAL_THRESHOLD")
    if approval:
        config.decision_policy.approval_threshold = float(approval)

    block = os.getenv("RISK_BLOCK_ON_CRITICAL")
    if block is not None:
        config.decision_policy.block_on_critical = block.strip().lower() in {"1", "true", "yes"}

    mode = os.getenv("EXECUTION_MODE")
    if mode:
        config.execution.mode = mode.strip().lower()

    live = os.getenv("LIVE_TRADING_ENABLED")
    if live is not None:
        config.execution.live_trading_enabled = live.strip().lower() in {"1", "true", "yes"}

    news_provider = os.getenv("NEWS_PROVIDER")
    if news_provider:
        config.strategy.news.provider = news_provider.strip().lower()

    benchmark = os.getenv("BENCHMARK_SYMBOL")
    if benchmark:
        config.benchmark.symbol = benchmark.strip().upper()

    market_provider = os.getenv("MARKET_DATA_PROVIDER")
    if market_provider:
        config.market_data.provider = market_provider.strip().lower()

    mem_enabled = os.getenv("MEMORY_ENABLED")
    if mem_enabled is not None:
        config.memory.enabled = mem_enabled.strip().lower() in {"1", "true", "yes"}

    mem_path = os.getenv("MEMORY_PATH")
    if mem_path:
        config.memory.path = mem_path

    return config


def _default_config_path() -> Path:
    return Path(__file__).resolve().parents[3] / "config" / "config.yaml"


def load_config(path: str | Path | None = None) -> EngineConfig:
    """Load engine configuration from YAML, then apply environment overrides."""
    config_path = Path(path) if path else _default_config_path()
    data: dict[str, Any] = {}
    if config_path.exists():
        loaded = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        if isinstance(loaded, dict):
            data = loaded
    config = EngineConfig.model_validate(data)
    return _apply_env_overrides(config)
