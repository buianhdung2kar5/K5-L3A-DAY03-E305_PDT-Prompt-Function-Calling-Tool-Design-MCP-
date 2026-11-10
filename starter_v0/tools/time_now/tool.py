from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Any

from tools._shared import err

# Fixed UTC+7 so the tool does not depend on a tz database (missing on some Windows installs).
VN_TZ = timezone(timedelta(hours=7))
WEEKDAYS = ["Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy", "Chủ nhật"]
WHEN_VALUES = ("now", "today", "yesterday", "this_week", "last_7_days", "this_month")
# Matches the `timeframe` enum of the lookup tool (day, week, month, year).
TIMEFRAME_HINT = {
    "now": "day", "today": "day", "yesterday": "day",
    "this_week": "week", "last_7_days": "week", "this_month": "month",
}


def _now() -> datetime:
    return datetime.now(VN_TZ)


def _range(when: str, today: date) -> tuple[date, date]:
    if when in ("now", "today"):
        return today, today
    if when == "yesterday":
        day = today - timedelta(days=1)
        return day, day
    if when == "this_week":
        monday = today - timedelta(days=today.weekday())
        return monday, monday + timedelta(days=6)
    if when == "last_7_days":
        return today - timedelta(days=6), today
    first = today.replace(day=1)
    next_month = (first + timedelta(days=32)).replace(day=1)
    return first, next_month - timedelta(days=1)


def get_time(when: str = "now") -> dict[str, Any]:
    """Current date/time in Vietnam plus the date range for a relative expression."""
    try:
        if when not in WHEN_VALUES:
            raise ValueError(f"when must be one of {', '.join(WHEN_VALUES)}")
        now = _now()
        start, end = _range(when, now.date())
        return {
            "tool": "time_now",
            "timezone": "UTC+7 (Việt Nam)",
            "now": now.isoformat(timespec="seconds"),
            "date": now.date().isoformat(),
            "weekday": WEEKDAYS[now.weekday()],
            "when": when,
            "start": start.isoformat(),
            "end": end.isoformat(),
            "timeframe_hint": TIMEFRAME_HINT[when],
        }
    except Exception as exc:
        return err("time_now", exc)
