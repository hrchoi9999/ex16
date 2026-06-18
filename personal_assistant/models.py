from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class ScheduleEvent:
    id: int | None
    title: str
    start_at: datetime
    end_at: datetime
    description: str = ""
    location: str = ""
    importance: int = 3
    google_event_id: str | None = None

    @property
    def date_label(self) -> str:
        return self.start_at.strftime("%Y-%m-%d")

    @property
    def time_label(self) -> str:
        hour = self.start_at.hour
        minute = self.start_at.minute
        meridiem = "오전" if hour < 12 else "오후"
        display_hour = hour % 12 or 12
        if minute:
            return f"{meridiem} {display_hour}시 {minute}분"
        return f"{meridiem} {display_hour}시"

