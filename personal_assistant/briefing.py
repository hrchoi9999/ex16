from __future__ import annotations

from datetime import datetime

from .models import BriefingSnapshot, RiskAssessment, ScheduleEvent, TaskPlanItem


def generate_briefing(
    *,
    scope_key: str,
    scope_label: str,
    events: list[ScheduleEvent],
    task_plan_by_event: dict[int, list[TaskPlanItem]],
    risk_by_event: dict[int, RiskAssessment],
    generated_at: datetime | None = None,
) -> BriefingSnapshot:
    generated_at = generated_at or datetime.now()
    sorted_events = sorted(events, key=lambda event: (_risk_score(event, risk_by_event), event.importance), reverse=True)
    deadlines = [event for event in events if event.title.startswith("[마감]") or bool(event.source_url)]
    high_risk = [
        event
        for event in events
        if event.id is not None and risk_by_event.get(int(event.id)) and risk_by_event[int(event.id)].risk_level in {"danger", "caution"}
    ]
    incomplete_tasks = sum(
        1
        for items in task_plan_by_event.values()
        for item in items
        if not item.completed
    )

    summary = _summary(scope_label, events, deadlines, high_risk, incomplete_tasks)
    highlights = [
        _highlight(event, task_plan_by_event.get(int(event.id or 0), []), risk_by_event.get(int(event.id or 0)))
        for event in sorted_events[:6]
    ]
    if not highlights:
        highlights = ["선택한 범위에 등록된 일정이 없습니다."]

    source_links = []
    for event in sorted_events:
        if event.source_url and event.source_url not in source_links:
            source_links.append(event.source_url)

    return BriefingSnapshot(
        id=None,
        scope_key=scope_key,
        scope_label=scope_label,
        summary=summary,
        highlights=highlights,
        related_event_ids=[int(event.id) for event in sorted_events if event.id is not None],
        source_links=source_links[:8],
        generated_at=generated_at.isoformat(timespec="seconds"),
    )


def _summary(
    scope_label: str,
    events: list[ScheduleEvent],
    deadlines: list[ScheduleEvent],
    high_risk: list[ScheduleEvent],
    incomplete_tasks: int,
) -> str:
    if not events:
        return f"{scope_label}에는 등록된 일정이 없습니다. 새 일정이나 관심 사이트 공고를 추가해 보세요."
    return (
        f"{scope_label}에는 일정 {len(events)}개가 있습니다. "
        f"마감/외부 공고 {len(deadlines)}개, 주의가 필요한 일정 {len(high_risk)}개, "
        f"미완료 실행 항목 {incomplete_tasks}개를 우선 확인하세요."
    )


def _highlight(event: ScheduleEvent, tasks: list[TaskPlanItem], risk: RiskAssessment | None) -> str:
    reasons: list[str] = []
    if event.source_url:
        reasons.append("원문 링크가 있는 외부 공고")
    if event.google_event_id:
        reasons.append("Google Calendar 연결")
    if risk and risk.risk_level != "safe":
        reasons.append(f"{risk.level_label} 리스크 {risk.risk_score}점")
    if tasks:
        done = sum(1 for item in tasks if item.completed)
        reasons.append(f"실행 계획 {done}/{len(tasks)} 완료")
    if event.importance >= 4:
        reasons.append(f"중요도 {event.importance}")
    if not reasons:
        reasons.append("일정 확인 필요")
    return f"{event.date_label} {event.time_label} · {event.title}: {', '.join(reasons)}"


def _risk_score(event: ScheduleEvent, risk_by_event: dict[int, RiskAssessment]) -> int:
    if event.id is None:
        return 0
    assessment = risk_by_event.get(int(event.id))
    return assessment.risk_score if assessment else 0
