from __future__ import annotations

from datetime import date, timedelta
from typing import Iterable

from .models import ScheduleEvent


HOLIDAY_TITLE_KEYWORDS = (
    "공휴일",
    "휴일",
    "설날",
    "추석",
    "어린이날",
    "부처님",
    "석가탄신일",
    "현충일",
    "광복절",
    "개천절",
    "한글날",
    "성탄절",
    "크리스마스",
    "신정",
    "대체공휴일",
    "대체 휴일",
    "선거일",
)

KOREAN_FIXED_HOLIDAYS = {
    (1, 1),
    (3, 1),
    (5, 5),
    (6, 6),
    (8, 15),
    (10, 3),
    (10, 9),
    (12, 25),
}

KNOWN_KOREAN_PUBLIC_HOLIDAYS = {
    2026: {
        date(2026, 1, 1),
        date(2026, 2, 16),
        date(2026, 2, 17),
        date(2026, 2, 18),
        date(2026, 3, 2),
        date(2026, 5, 5),
        date(2026, 5, 25),
        date(2026, 6, 3),
        date(2026, 6, 6),
        date(2026, 8, 15),
        date(2026, 9, 24),
        date(2026, 9, 25),
        date(2026, 9, 26),
        date(2026, 10, 5),
        date(2026, 10, 9),
        date(2026, 12, 25),
    }
}


def is_holiday_event(event: ScheduleEvent) -> bool:
    text = " ".join([event.title, event.description, event.location, event.source]).lower()
    return any(keyword.lower() in text for keyword in HOLIDAY_TITLE_KEYWORDS)


def iter_event_dates(event: ScheduleEvent) -> Iterable[date]:
    current = event.start_at.date()
    end = event.end_at.date()
    while current <= end:
        yield current
        current += timedelta(days=1)


def holiday_dates_from_events(events: Iterable[ScheduleEvent]) -> set[date]:
    dates: set[date] = set()
    for event in events:
        if is_holiday_event(event):
            dates.update(iter_event_dates(event))
    return dates


def is_known_korean_holiday(day: date, holiday_dates: set[date] | None = None) -> bool:
    if holiday_dates and day in holiday_dates:
        return True
    if (day.month, day.day) in KOREAN_FIXED_HOLIDAYS:
        return True
    return day in KNOWN_KOREAN_PUBLIC_HOLIDAYS.get(day.year, set())


def is_weekend(day: date) -> bool:
    return day.weekday() >= 5


def is_business_day(day: date, holiday_dates: set[date] | None = None) -> bool:
    return not is_weekend(day) and not is_known_korean_holiday(day, holiday_dates)


def eligible_registration_days(start_day: date, end_day: date, holiday_dates: set[date] | None = None) -> list[date]:
    if start_day == end_day:
        if is_business_day(start_day, holiday_dates) or is_known_korean_holiday(start_day, holiday_dates):
            return [start_day]
        return []

    days: list[date] = []
    current = start_day
    while current <= end_day:
        if is_business_day(current, holiday_dates):
            days.append(current)
        current += timedelta(days=1)
    return days
