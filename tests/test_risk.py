from datetime import datetime, timedelta

from personal_assistant.models import ScheduleEvent, TaskPlanItem
from personal_assistant.risk import assess_event_risk


def test_deadline_without_task_plan_is_danger() -> None:
    now = datetime(2026, 6, 22, 9, 0)
    event = ScheduleEvent(
        id=1,
        title="[마감] 창업 지원 사업",
        start_at=now + timedelta(days=1),
        end_at=now + timedelta(days=1, hours=1),
        importance=4,
        source_url="https://example.com/notice",
    )

    assessment = assess_event_risk(event, [event], [], now=now)

    assert assessment.risk_level == "danger"
    assert assessment.risk_score >= 60
    assert any("실행 계획" in factor for factor in assessment.risk_factors)


def test_completed_task_plan_lowers_risk() -> None:
    now = datetime(2026, 6, 22, 9, 0)
    event = ScheduleEvent(
        id=1,
        title="[마감] 창업 지원 사업",
        start_at=now + timedelta(days=5),
        end_at=now + timedelta(days=5, hours=1),
        source_url="https://example.com/notice",
    )
    items = [
        TaskPlanItem(id=1, event_id=1, stage="today", title="조건 확인", due_date=now.date(), completed=True),
        TaskPlanItem(id=2, event_id=1, stage="before_deadline", title="제출", due_date=now.date(), completed=True),
    ]

    assessment = assess_event_risk(event, [event], items, now=now)

    assert assessment.risk_level in {"safe", "caution"}
    assert not any("실행 계획이 아직 없습니다" in factor for factor in assessment.risk_factors)
