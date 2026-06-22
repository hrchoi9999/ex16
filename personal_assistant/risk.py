from __future__ import annotations

from datetime import datetime

from .models import RiskAssessment, ScheduleEvent, TaskPlanItem


def assess_event_risk(
    event: ScheduleEvent,
    events: list[ScheduleEvent],
    task_items: list[TaskPlanItem],
    *,
    now: datetime | None = None,
) -> RiskAssessment:
    now = now or datetime.now()
    score = 0
    factors: list[str] = []
    next_action = "일정 내용을 확인하고 필요한 준비 작업을 정리하세요."
    days_left = (event.start_at.date() - now.date()).days
    is_deadline = event.title.startswith("[마감]") or bool(event.source_url)

    if event.end_at < now:
        return RiskAssessment(
            id=None,
            event_id=int(event.id or 0),
            risk_score=0,
            risk_level="safe",
            risk_factors=["이미 종료된 일정입니다."],
            next_action="필요하다면 완료 기록이나 후속 일정을 정리하세요.",
            assessed_at=now.isoformat(timespec="seconds"),
        )

    if is_deadline:
        if days_left <= 1:
            score += 45
            factors.append("마감이 1일 이내입니다.")
            next_action = "오늘 제출 가능 상태인지 확인하고 누락 항목을 먼저 처리하세요."
        elif days_left <= 3:
            score += 35
            factors.append("마감이 3일 이내입니다.")
            next_action = "오늘 안에 초안과 필수 서류를 점검하세요."
        elif days_left <= 7:
            score += 22
            factors.append("마감이 7일 이내입니다.")
            next_action = "이번 주 안에 제출 준비 체크리스트를 완료하세요."

    if event.importance >= 4 and days_left <= 7:
        score += 10
        factors.append("중요도가 높은 임박 일정입니다.")

    completion_ratio = _completion_ratio(task_items)
    if is_deadline and not task_items:
        score += 25
        factors.append("실행 계획이 아직 없습니다.")
        next_action = "실행 계획을 생성해 준비 작업을 분해하세요."
    elif task_items and completion_ratio < 0.5 and days_left <= 7:
        score += 20
        factors.append("실행 계획 완료율이 50% 미만입니다.")
        next_action = "남은 체크리스트 중 오늘 처리할 항목을 먼저 완료하세요."
    elif task_items and completion_ratio < 0.8 and days_left <= 2:
        score += 15
        factors.append("마감 직전인데 완료되지 않은 체크리스트가 남아 있습니다.")
        next_action = "마감전 체크 항목을 우선 완료하세요."

    conflict_count = _conflict_count(event, events)
    if conflict_count:
        score += min(conflict_count * 15, 30)
        factors.append(f"겹치는 일정이 {conflict_count}개 있습니다.")
        next_action = "겹치는 일정 시간을 조정하거나 우선 처리할 일정을 선택하세요."

    if event.importance >= 4 and event.sync_status != "synced":
        score += 8
        factors.append("중요 일정이 Google Calendar와 동기화되지 않은 상태입니다.")

    if not factors:
        factors.append("현재 감지된 주요 마감 리스크가 낮습니다.")

    score = min(score, 100)
    return RiskAssessment(
        id=None,
        event_id=int(event.id or 0),
        risk_score=score,
        risk_level=_risk_level(score),
        risk_factors=factors,
        next_action=next_action,
        assessed_at=now.isoformat(timespec="seconds"),
    )


def assess_risks(events: list[ScheduleEvent], task_plan_by_event: dict[int, list[TaskPlanItem]]) -> list[RiskAssessment]:
    now = datetime.now()
    upcoming = [event for event in events if event.id is not None and event.end_at >= now]
    return [
        assess_event_risk(event, upcoming, task_plan_by_event.get(int(event.id), []), now=now)
        for event in upcoming
    ]


def _completion_ratio(items: list[TaskPlanItem]) -> float:
    if not items:
        return 0.0
    return sum(1 for item in items if item.completed) / len(items)


def _conflict_count(event: ScheduleEvent, events: list[ScheduleEvent]) -> int:
    if event.id is None:
        return 0
    return sum(
        1
        for other in events
        if other.id != event.id and event.start_at < other.end_at and other.start_at < event.end_at
    )


def _risk_level(score: int) -> str:
    if score >= 60:
        return "danger"
    if score >= 30:
        return "caution"
    return "safe"
