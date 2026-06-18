from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from .models import ScheduleEvent


@dataclass(frozen=True)
class PriorityRecommendation:
    event: ScheduleEvent
    score: float
    reason: str


def recommend_priorities(events: list[ScheduleEvent], now: datetime | None = None) -> list[PriorityRecommendation]:
    now = now or datetime.now()
    recommendations: list[PriorityRecommendation] = []
    for event in events:
        hours_left = max((event.start_at - now).total_seconds() / 3600, 0)
        urgency = max(0, 48 - hours_left) / 12
        score = event.importance * 2 + urgency
        reason = _build_reason(event, hours_left)
        recommendations.append(PriorityRecommendation(event=event, score=round(score, 2), reason=reason))
    return sorted(recommendations, key=lambda item: (-item.score, item.event.start_at))


def _build_reason(event: ScheduleEvent, hours_left: float) -> str:
    if event.importance >= 4 and hours_left <= 24:
        return "중요도가 높고 24시간 이내에 시작합니다."
    if event.importance >= 4:
        return "중요도가 높아 먼저 확인하는 것이 좋습니다."
    if hours_left <= 6:
        return "곧 시작하는 일정입니다."
    if hours_left <= 24:
        return "오늘 또는 내일 처리할 일정입니다."
    return "일정 시간이 가까운 순서로 관리하면 좋습니다."

