"""Tests for the deterministic US market calendar (NYSE/Nasdaq regular session)."""

from __future__ import annotations

from datetime import date, datetime, timezone

from robinhood_agent.market.calendar import (
    is_holiday,
    is_trading_day,
    parse_as_of,
    session_state,
    to_eastern,
)


def test_open_session_on_weekday() -> None:
    when = parse_as_of("2026-05-11T13:30:00+00:00")  # Monday 09:30 ET
    assert when is not None
    assert session_state(when) == "open"


def test_closed_on_weekend() -> None:
    when = parse_as_of("2026-05-09T13:30:00+00:00")  # Saturday
    assert when is not None
    assert session_state(when) == "closed"


def test_after_hours_is_closed_unless_allowed() -> None:
    when = parse_as_of("2026-05-11T11:00:00+00:00")  # 07:00 ET, pre-market
    assert when is not None
    assert session_state(when, allow_extended_hours=False) == "closed"
    assert session_state(when, allow_extended_hours=True) == "extended"


def test_holiday_is_not_a_trading_day() -> None:
    assert is_holiday(date(2026, 7, 3))  # Independence Day (observed)
    assert not is_trading_day(date(2026, 7, 3))


def test_dst_offset_changes_between_seasons() -> None:
    summer = to_eastern(datetime(2026, 7, 1, 16, 0, tzinfo=timezone.utc))  # EDT (-4)
    winter = to_eastern(datetime(2026, 1, 15, 16, 0, tzinfo=timezone.utc))  # EST (-5)
    assert summer.hour == 12
    assert winter.hour == 11


def test_parse_as_of_handles_z_suffix_and_blank() -> None:
    assert parse_as_of("2026-05-11T13:30:00Z") is not None
    assert parse_as_of("") is None
    assert parse_as_of("not-a-date") is None
