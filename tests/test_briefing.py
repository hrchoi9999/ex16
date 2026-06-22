from datetime import datetime, timedelta

from personal_assistant.briefing import generate_briefing
from personal_assistant.models import RiskAssessment, ScheduleEvent, TaskPlanItem


def test_generate_briefing_includes_context() -> None:
    start_at = datetime(2026, 6, 22, 9, 0)
    event = ScheduleEvent(
        id=1,
        title="[마감] 창업 지원",
        start_at=start_at,
        end_at=start_at + timedelta(hours=1),
        importance=4,
        source_url="https://example.com/notice",
    )
    task = TaskPlanItem(
        id=1,
        event_id=1,
        stage="today",
        title="조건 확인",
        due_date=start_at.date(),
        completed=False,
    )
    risk = RiskAssessment(
        id=1,
        event_id=1,
        risk_score=75,
        risk_level="danger",
        risk_factors=["마감 임박"],
        next_action="오늘 제출 상태를 확인하세요.",
    )

    snapshot = generate_briefing(
        scope_key="day:2026-06-22",
        scope_label="2026-06-22",
        events=[event],
        task_plan_by_event={1: [task]},
        risk_by_event={1: risk},
        generated_at=start_at,
    )

    assert "일정 1개" in snapshot.summary
    assert snapshot.source_links == ["https://example.com/notice"]
    assert snapshot.related_event_ids == [1]
    assert any("위험" in highlight for highlight in snapshot.highlights)
