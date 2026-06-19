"""Deterministic US equity market calendar (NYSE/Nasdaq regular session).

The session state is derived purely from the run's ``as_of`` timestamp, so it is
fully reproducible and requires no third-party calendar library. Eastern time is
computed with the standard US daylight-saving rule (second Sunday of March to the
first Sunday of November). Holidays are hardcoded for the supported years; a date
in an unsupported year falls back to a weekend check only.
"""

from __future__ import annotations

import calendar as _calendar
from datetime import date, datetime, time, timedelta, timezone

# NYSE full-day closures. Half-days (early close) are treated as open here.
_NYSE_HOLIDAYS: dict[int, set[tuple[int, int]]] = {
    2025: {
        (1, 1),  # New Year's Day
        (1, 20),  # MLK Jr. Day
        (2, 17),  # Washington's Birthday
        (4, 18),  # Good Friday
        (5, 26),  # Memorial Day
        (6, 19),  # Juneteenth
        (7, 4),  # Independence Day
        (9, 1),  # Labor Day
        (11, 27),  # Thanksgiving
        (12, 25),  # Christmas
    },
    2026: {
        (1, 1),  # New Year's Day
        (1, 19),  # MLK Jr. Day
        (2, 16),  # Washington's Birthday
        (4, 3),  # Good Friday
        (5, 25),  # Memorial Day
        (6, 19),  # Juneteenth
        (7, 3),  # Independence Day (observed)
        (9, 7),  # Labor Day
        (11, 26),  # Thanksgiving
        (12, 25),  # Christmas
    },
}

REGULAR_OPEN = time(9, 30)
REGULAR_CLOSE = time(16, 0)
EXTENDED_OPEN = time(4, 0)
EXTENDED_CLOSE = time(20, 0)


def _nth_weekday(year: int, month: int, weekday: int, n: int) -> date:
    """Return the date of the ``n``-th ``weekday`` (Mon=0) in a month."""
    first = date(year, month, 1)
    offset = (weekday - first.weekday()) % 7
    return first + timedelta(days=offset + 7 * (n - 1))


def _is_us_dst(dt_utc: datetime) -> bool:
    """US daylight-saving: 2:00 local 2nd Sun Mar to 2:00 local 1st Sun Nov."""
    year = dt_utc.year
    # 2:00 EST == 07:00 UTC; 2:00 EDT == 06:00 UTC.
    start = datetime(year, 3, _nth_weekday(year, 3, 6, 2).day, 7, tzinfo=timezone.utc)
    end = datetime(year, 11, _nth_weekday(year, 11, 6, 1).day, 6, tzinfo=timezone.utc)
    return start <= dt_utc < end


def to_eastern(dt: datetime) -> datetime:
    """Convert an aware (or assumed-UTC) datetime to naive US Eastern time."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    dt_utc = dt.astimezone(timezone.utc)
    offset = 4 if _is_us_dst(dt_utc) else 5
    return (dt_utc - timedelta(hours=offset)).replace(tzinfo=None)


def is_holiday(d: date) -> bool:
    return (d.month, d.day) in _NYSE_HOLIDAYS.get(d.year, set())


def is_trading_day(d: date) -> bool:
    """A weekday that is not a full-day NYSE holiday."""
    return d.weekday() < 5 and not is_holiday(d)


def parse_as_of(as_of: str | None) -> datetime | None:
    """Parse an ISO-8601 ``as_of`` string into an aware datetime, or ``None``."""
    if not as_of:
        return None
    try:
        dt = datetime.fromisoformat(as_of.replace("Z", "+00:00"))
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def session_state(dt: datetime, allow_extended_hours: bool = False) -> str:
    """Classify the US session at ``dt`` as ``open``, ``extended``, or ``closed``."""
    eastern = to_eastern(dt)
    if not is_trading_day(eastern.date()):
        return "closed"
    now = eastern.time()
    if REGULAR_OPEN <= now < REGULAR_CLOSE:
        return "open"
    if allow_extended_hours and EXTENDED_OPEN <= now < EXTENDED_CLOSE:
        return "extended"
    return "closed"


def describe(dt: datetime) -> str:
    """Human-readable Eastern-time description for audit narratives."""
    eastern = to_eastern(dt)
    weekday = _calendar.day_name[eastern.weekday()]
    return f"{weekday} {eastern:%Y-%m-%d %H:%M} ET"
