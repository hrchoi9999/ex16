from __future__ import annotations

from datetime import datetime, timedelta
from types import SimpleNamespace

import personal_assistant.ai_chat as ai_chat
from personal_assistant.ai_chat import answer_schedule_question
from personal_assistant.models import ScheduleEvent


def test_ai_chat_overview_fallback_without_api_key(monkeypatch) -> None:
    monkeypatch.setattr(ai_chat, "settings", SimpleNamespace(gemini_api_key=""))
    today = datetime.now().replace(hour=14, minute=0, second=0, microsecond=0)
    event = ScheduleEvent(id=1, title="팀 회의", start_at=today, end_at=today + timedelta(hours=1))

    result = answer_schedule_question("오늘 일정 알려줘", [event])

    assert "팀 회의" in result.answer
    assert result.matched_event_ids == [1]


def test_ai_chat_reports_empty_schedule(monkeypatch) -> None:
    monkeypatch.setattr(ai_chat, "settings", SimpleNamespace(gemini_api_key=""))
    result = answer_schedule_question("이번 주 일정 알려줘", [])

    assert "등록된 일정이 없습니다" in result.answer
    assert result.matched_event_ids == []
