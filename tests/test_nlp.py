from datetime import date
from types import SimpleNamespace

import personal_assistant.nlp as nlp
from personal_assistant.nlp import CommandParser


def test_parse_next_tuesday_meeting_example(monkeypatch) -> None:
    monkeypatch.setattr(nlp, "settings", SimpleNamespace(gemini_api_key="", llm_enabled=False))
    parser = CommandParser()
    parsed = parser.parse("다음 주 화요일 오후 2시에 회의 등록해줘.", today=date(2026, 6, 18))

    assert parsed.event is not None
    assert parsed.event.title == "회의"
    assert parsed.event.start_at.date().isoformat() == "2026-06-23"
    assert parsed.event.start_at.hour == 14
    assert parsed.event.start_at.minute == 0


def test_parse_important_tomorrow_event(monkeypatch) -> None:
    monkeypatch.setattr(nlp, "settings", SimpleNamespace(gemini_api_key="", llm_enabled=False))
    parser = CommandParser()
    parsed = parser.parse("내일 오전 10시에 중요한 면접 추가해줘", today=date(2026, 6, 18))

    assert parsed.event is not None
    assert parsed.event.title == "면접"
    assert parsed.event.importance == 5
    assert parsed.event.start_at.date().isoformat() == "2026-06-19"
