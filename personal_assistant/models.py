from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime


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
    source: str = "local"
    source_url: str = ""
    sync_status: str = "local"

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


@dataclass
class AppUser:
    id: int | None
    email: str
    display_name: str = ""
    provider: str = "google"
    linked_at: str = ""
    auto_sync: bool = True


@dataclass
class ExternalScheduleCandidate:
    id: int | None
    source: str
    category: str
    title: str
    recruitment_period: str
    url: str
    status: str = "모집중"
    collected_at: str = ""
    selected: bool = False


@dataclass
class TaskPlanItem:
    id: int | None
    event_id: int
    stage: str
    title: str
    due_date: date
    estimated_minutes: int = 30
    completed: bool = False
    source: str = "rule"
    sort_order: int = 0

    @property
    def stage_label(self) -> str:
        labels = {
            "today": "오늘 할 일",
            "this_week": "이번주 준비",
            "before_deadline": "마감전 체크",
        }
        return labels.get(self.stage, self.stage)


@dataclass
class RiskAssessment:
    id: int | None
    event_id: int
    risk_score: int
    risk_level: str
    risk_factors: list[str] = field(default_factory=list)
    next_action: str = ""
    assessed_at: str = ""

    @property
    def level_label(self) -> str:
        labels = {
            "safe": "안전",
            "caution": "주의",
            "danger": "위험",
        }
        return labels.get(self.risk_level, self.risk_level)


@dataclass
class BriefingSnapshot:
    id: int | None
    scope_key: str
    scope_label: str
    summary: str
    highlights: list[str] = field(default_factory=list)
    related_event_ids: list[int] = field(default_factory=list)
    source_links: list[str] = field(default_factory=list)
    generated_at: str = ""
