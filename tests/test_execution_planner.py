from datetime import datetime, timedelta

from personal_assistant import execution_planner
from personal_assistant.models import ScheduleEvent


def test_generate_task_plan_for_deadline_event(monkeypatch) -> None:
    monkeypatch.setattr(execution_planner, "settings", type("Settings", (), {"gemini_api_key": ""})())
    start_at = datetime.now() + timedelta(days=10)
    event = ScheduleEvent(
        id=1,
        title="[마감] 창업 지원 사업",
        start_at=start_at,
        end_at=start_at + timedelta(hours=1),
        source_url="https://example.com/notice",
    )

    items = execution_planner.generate_task_plan(event)

    assert len(items) >= 5
    assert {"today", "this_week", "before_deadline"}.issubset({item.stage for item in items})
    assert any("원문" in item.title or "지원 조건" in item.title for item in items)
