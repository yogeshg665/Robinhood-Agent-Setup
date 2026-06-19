"""Market-data models: instruments, quotes, price history, and news."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class Instrument(BaseModel):
    """A tradable equity instrument."""

    symbol: str
    name: str = ""
    sector: str = "unknown"
    asset_class: str = "equity"


class Quote(BaseModel):
    """A point-in-time market quote for a symbol.

    All fields are deterministic inputs to the engine. ``volatility`` is a daily
    return standard deviation expressed as a fraction (for example 0.03 == 3%).
    """

    symbol: str
    price: float = Field(..., gt=0.0)
    previous_close: float = Field(..., gt=0.0)
    average_volume: float = Field(default=0.0, ge=0.0)
    volatility: float = Field(default=0.0, ge=0.0)
    bid: float | None = None
    ask: float | None = None

    @property
    def day_change_pct(self) -> float:
        """Percentage change from the previous close (e.g. 1.5 == +1.5%)."""
        if self.previous_close <= 0.0:
            return 0.0
        return (self.price - self.previous_close) / self.previous_close * 100.0

    @property
    def spread_pct(self) -> float:
        """Bid/ask spread as a percentage of price, or 0 when not provided."""
        if self.bid is None or self.ask is None or self.price <= 0.0:
            return 0.0
        return max(self.ask - self.bid, 0.0) / self.price * 100.0


class PriceBar(BaseModel):
    """A single OHLCV bar used by trend and mean-reversion strategies."""

    symbol: str
    date: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0


class NewsItem(BaseModel):
    """A pseudonymous, deterministic news headline for a target company."""

    symbol: str
    published_at: datetime
    headline: str
    summary: str = ""
    source: str = "fixture"
    # Optional pre-scored sentiment in [-1, 1]; when absent the engine derives it
    # deterministically from the headline using a fixed keyword lexicon.
    sentiment: float | None = Field(default=None, ge=-1.0, le=1.0)


class MacroIndicators(BaseModel):
    """Deterministic US macro indicators for one run.

    All fields are optional. They feed the macro-regime agent, which classifies the
    US market environment (risk-on / neutral / risk-off). These values are part of
    the run input, so the regime is fully reproducible. In a live deployment they
    would be sourced from FRED (rates), CBOE (VIX), and ICE (dollar index).
    """

    vix: float | None = Field(default=None, ge=0.0)  # CBOE Volatility Index level
    ten_year_yield: float | None = None  # US 10Y Treasury yield, percent
    two_year_yield: float | None = None  # US 2Y Treasury yield, percent
    fed_funds_rate: float | None = None  # effective federal funds rate, percent
    dollar_index: float | None = None  # US dollar index (DXY) level

    @property
    def yield_curve_spread(self) -> float | None:
        """10Y-minus-2Y spread in percentage points; negative means inverted."""
        if self.ten_year_yield is None or self.two_year_yield is None:
            return None
        return round(self.ten_year_yield - self.two_year_yield, 4)
