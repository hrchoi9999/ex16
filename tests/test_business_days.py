from __future__ import annotations

from datetime import date, datetime, time

from personal_assistant.business_days import eligible_registration_days, holiday_dates_from_events
from personal_assistant.models import ScheduleEvent


def test_period_registration_excludes_weekends_and_holidays() -> None:
    holidays = {date(2026, 6, 24)}

    days = eligible_registration_days(date(2026, 6, 19), date(2026, 6, 25), holidays)

    assert days == [
        date(2026, 6, 19),
        date(2026, 6, 22),
        date(2026, 6, 23),
        date(2026, 6, 25),
    ]


def test_single_holiday_registration_is_allowed() -> None:
    holidays = {date(2026, 6, 24)}

    days = eligible_registration_days(date(2026, 6, 24), date(2026, 6, 24), holidays)

    assert days == [date(2026, 6, 24)]


def test_single_weekend_registration_is_excluded() -> None:
    days = eligible_registration_days(date(2026, 6, 20), date(2026, 6, 20), set())

    assert days == []


def test_holiday_dates_can_be_derived_from_imported_calendar_events() -> None:
    event = ScheduleEvent(
        id=1,
        title="현충일",
        start_at=datetime.combine(date(2026, 6, 6), time(0, 0)),
        end_at=datetime.combine(date(2026, 6, 6), time(23, 59)),
        source="google_calendar",
    )

    assert holiday_dates_from_events([event]) == {date(2026, 6, 6)}
