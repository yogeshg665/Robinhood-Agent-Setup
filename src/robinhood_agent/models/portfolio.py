"""Portfolio, account, position, and trading-goal models."""

from __future__ import annotations

from pydantic import BaseModel, Field


class Position(BaseModel):
    """A single open equity position."""

    symbol: str
    quantity: float = Field(..., ge=0.0)
    average_cost: float = Field(default=0.0, ge=0.0)
    current_price: float = Field(default=0.0, ge=0.0)
    sector: str = "unknown"

    @property
    def market_value(self) -> float:
        return self.quantity * self.current_price

    @property
    def unrealized_pnl(self) -> float:
        return (self.current_price - self.average_cost) * self.quantity


class Account(BaseModel):
    """Account-level balances and day-trading state for the agentic account."""

    account_id: str
    cash: float = Field(default=0.0, ge=0.0)
    buying_power: float = Field(default=0.0, ge=0.0)
    start_of_day_equity: float = Field(default=0.0, ge=0.0)
    day_trades_used: int = Field(default=0, ge=0)
    is_pattern_day_trader: bool = False


class RecentSale(BaseModel):
    """A recently closed lot, used by the wash-sale risk check.

    Under US IRS rules a loss is disallowed when the same or a substantially
    identical security is repurchased within 30 days. ``realized_loss`` is a
    positive number when the sale closed at a loss (0 for a gain).
    """

    symbol: str
    days_ago: int = Field(..., ge=0)
    realized_loss: float = Field(default=0.0, ge=0.0)


class Portfolio(BaseModel):
    """The agentic account plus its open positions."""

    account: Account
    positions: list[Position] = Field(default_factory=list)
    recent_sales: list[RecentSale] = Field(default_factory=list)

    def recent_loss_sale(self, symbol: str, window_days: int) -> RecentSale | None:
        """Return a within-window loss sale of ``symbol`` (wash-sale trigger), if any."""
        for sale in self.recent_sales:
            if (
                sale.symbol == symbol
                and sale.realized_loss > 0.0
                and sale.days_ago <= window_days
            ):
                return sale
        return None

    @property
    def positions_value(self) -> float:
        return sum(position.market_value for position in self.positions)

    @property
    def total_value(self) -> float:
        return self.account.cash + self.positions_value

    def position_for(self, symbol: str) -> Position | None:
        for position in self.positions:
            if position.symbol == symbol:
                return position
        return None

    def weight_of(self, symbol: str) -> float:
        """Fraction of total portfolio value held in ``symbol`` (0..1)."""
        total = self.total_value
        if total <= 0.0:
            return 0.0
        position = self.position_for(symbol)
        return (position.market_value / total) if position else 0.0

    def sector_weight(self, sector: str) -> float:
        """Fraction of total portfolio value held in a sector (0..1)."""
        total = self.total_value
        if total <= 0.0:
            return 0.0
        held = sum(p.market_value for p in self.positions if p.sector == sector)
        return held / total


class TradingGoals(BaseModel):
    """The investor mandate that constrains and directs the agent.

    Goals are declarative and deterministic. ``target_weights`` drives rebalancing;
    ``themes`` drives the thematic strategy; ``news_targets`` selects companies for
    the daily-news signal. All weights are fractions in [0, 1].
    """

    risk_tolerance: str = Field(default="moderate")  # conservative | moderate | aggressive
    target_weights: dict[str, float] = Field(default_factory=dict)
    max_position_pct: float = Field(default=0.20, gt=0.0, le=1.0)
    cash_reserve_pct: float = Field(default=0.05, ge=0.0, le=1.0)
    themes: list[str] = Field(default_factory=list)
    watchlist: list[str] = Field(default_factory=list)
    news_targets: list[str] = Field(default_factory=list)
    benchmark: str = Field(default="SPY")  # US relative-strength benchmark
