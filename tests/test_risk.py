"""Tests for the risk guardian: each check blocks or passes as designed."""

from __future__ import annotations

from robinhood_agent.models.market import Instrument
from robinhood_agent.models.portfolio import RecentSale
from robinhood_agent.models.proposal import OrderType, Side
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
from tests.conftest import (
    build_config,
    make_account,
    make_context,
    make_position,
    make_proposal,
    make_quote,
)


def test_position_size_blocks_large_order_notional() -> None:
    context = make_context(account=make_account(cash=100_000.0))
    proposal = make_proposal("AAA", Side.BUY, 300, 100.0)  # 30,000 > 25,000
    finding = PositionSizeCheck(build_config()).evaluate(proposal, context, 0)
    assert finding is not None and finding.blocking


def test_position_size_blocks_oversized_weight() -> None:
    context = make_context(account=make_account(cash=50_000.0))
    proposal = make_proposal("AAA", Side.BUY, 200, 60.0)  # 12,000 -> 24% of 50,000
    finding = PositionSizeCheck(build_config()).evaluate(proposal, context, 0)
    assert finding is not None and finding.blocking
    assert finding.name == "position_size_exceeded"


def test_concentration_limit_blocks_sector_breach() -> None:
    context = make_context(
        positions=[make_position("AAA", 100, 100.0, sector="technology")],
        instruments=[Instrument(symbol="BBB", name="B", sector="technology")],
        account=make_account(cash=0.0),
    )
    proposal = make_proposal("BBB", Side.BUY, 50, 100.0)
    finding = ConcentrationLimitCheck(build_config()).evaluate(proposal, context, 0)
    assert finding is not None and finding.blocking


def test_buying_power_blocks_insufficient_cash() -> None:
    context = make_context(account=make_account(cash=1_000.0))
    proposal = make_proposal("AAA", Side.BUY, 50, 100.0)  # 5,000 > ~980 available
    finding = BuyingPowerCheck(build_config()).evaluate(proposal, context, 0)
    assert finding is not None and finding.blocking


def test_daily_loss_kill_switch_blocks_buys_only() -> None:
    context = make_context(
        positions=[make_position("AAA", 900, 100.0)],  # value 90,000
        account=make_account(cash=0.0, start_of_day_equity=100_000.0),  # -10%
    )
    buy = make_proposal("AAA", Side.BUY, 1, 100.0)
    sell = make_proposal("AAA", Side.SELL, 1, 100.0)
    check = DailyLossCheck(build_config())
    assert check.evaluate(buy, context, 0) is not None
    assert check.evaluate(sell, context, 0) is None


def test_order_rate_throttles_beyond_limit() -> None:
    context = make_context()
    proposal = make_proposal("AAA", Side.BUY, 1, 100.0)
    check = OrderRateCheck(build_config())
    assert check.evaluate(proposal, context, 0) is None
    assert check.evaluate(proposal, context, 10) is not None


def test_price_deviation_blocks_far_limit() -> None:
    context = make_context(quotes=[make_quote("AAA", 100.0)])
    far = make_proposal("AAA", Side.BUY, 1, 130.0, order_type=OrderType.LIMIT, limit_price=130.0)
    market = make_proposal("AAA", Side.BUY, 1, 100.0)
    check = PriceDeviationCheck(build_config())
    assert check.evaluate(far, context, 0) is not None
    assert check.evaluate(market, context, 0) is None


def test_pdt_blocks_when_limit_reached() -> None:
    proposal = make_proposal("AAA", Side.BUY, 1, 100.0)
    check = PdtCheck(build_config())
    flagged = make_context(account=make_account(day_trades_used=3, is_pattern_day_trader=True))
    capped = make_context(account=make_account(day_trades_used=3, is_pattern_day_trader=False))
    assert check.evaluate(proposal, flagged, 0) is None
    assert check.evaluate(proposal, capped, 0) is not None


def test_liquidity_is_advisory_not_blocking() -> None:
    context = make_context(quotes=[make_quote("HV", 40.0, volatility=0.10)])
    proposal = make_proposal("HV", Side.BUY, 1, 40.0)
    finding = LiquidityCheck(build_config()).evaluate(proposal, context, 0)
    assert finding is not None
    assert finding.blocking is False
    assert finding.severity == 65.0


def test_liquidity_passes_for_healthy_name() -> None:
    context = make_context(
        quotes=[make_quote("LQ", 40.0, volatility=0.01, average_volume=10_000_000.0)]
    )
    proposal = make_proposal("LQ", Side.BUY, 1, 40.0)
    assert LiquidityCheck(build_config()).evaluate(proposal, context, 0) is None


def test_wash_sale_flags_repurchase_within_window() -> None:
    context = make_context(
        recent_sales=[RecentSale(symbol="KO", days_ago=9, realized_loss=850.0)],
    )
    proposal = make_proposal("KO", Side.BUY, 1, 60.0)
    finding = WashSaleCheck(build_config()).evaluate(proposal, context, 0)
    assert finding is not None
    assert finding.name == "wash_sale_window"
    assert finding.blocking is False  # advisory by default


def test_wash_sale_ignores_sales_outside_window() -> None:
    context = make_context(
        recent_sales=[RecentSale(symbol="KO", days_ago=45, realized_loss=850.0)],
    )
    proposal = make_proposal("KO", Side.BUY, 1, 60.0)
    assert WashSaleCheck(build_config()).evaluate(proposal, context, 0) is None


def test_wash_sale_ignores_sells() -> None:
    context = make_context(
        recent_sales=[RecentSale(symbol="KO", days_ago=9, realized_loss=850.0)],
    )
    proposal = make_proposal("KO", Side.SELL, 1, 60.0)
    assert WashSaleCheck(build_config()).evaluate(proposal, context, 0) is None


def test_market_hours_passes_during_open_session() -> None:
    # Default context as_of is a Monday 09:30 ET (regular session open).
    context = make_context()
    proposal = make_proposal("AAA", Side.BUY, 1, 100.0)
    assert MarketHoursCheck(build_config()).evaluate(proposal, context, 0) is None


def test_market_hours_blocks_weekend() -> None:
    context = make_context(as_of="2026-05-09T13:30:00+00:00")  # Saturday
    proposal = make_proposal("AAA", Side.BUY, 1, 100.0)
    finding = MarketHoursCheck(build_config()).evaluate(proposal, context, 0)
    assert finding is not None and finding.blocking
    assert finding.name == "market_closed"


def test_market_hours_blocks_exchange_holiday() -> None:
    context = make_context(as_of="2026-07-03T13:30:00+00:00")  # Independence Day (obs)
    proposal = make_proposal("AAA", Side.BUY, 1, 100.0)
    finding = MarketHoursCheck(build_config()).evaluate(proposal, context, 0)
    assert finding is not None and finding.blocking


def test_market_hours_blocks_after_hours_by_default() -> None:
    context = make_context(as_of="2026-05-11T22:00:00+00:00")  # 18:00 ET, after close
    proposal = make_proposal("AAA", Side.BUY, 1, 100.0)
    finding = MarketHoursCheck(build_config()).evaluate(proposal, context, 0)
    assert finding is not None and finding.blocking


def test_market_hours_passes_when_timestamp_missing() -> None:
    context = make_context(as_of="")
    proposal = make_proposal("AAA", Side.BUY, 1, 100.0)
    assert MarketHoursCheck(build_config()).evaluate(proposal, context, 0) is None
