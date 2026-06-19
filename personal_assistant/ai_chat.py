from __future__ import annotations

from dataclasses import dataclass

from .config import settings
from .models import ScheduleEvent


@dataclass
class AiChatResult:
    answer: str
    matched_event_ids: list[int]


def answer_schedule_question(question: str, events: list[ScheduleEvent]) -> AiChatResult:
    query = question.strip()
    if not query:
        return AiChatResult("질문을 입력해 주세요.", [])

    matched = _match_events(query, events)
    context = "\n".join(
        f"- id={event.id}, title={event.title}, date={event.date_label}, time={event.time_label}, "
        f"description={event.description}, source={event.source}"
        for event in matched[:12]
    )

    if settings.gemini_api_key:
        try:
            from google import genai

            client = genai.Client(api_key=settings.gemini_api_key)
            prompt = (
                "너는 개인 일정 관리 AI 비서다. 아래 일정 목록에서 사용자 질문과 관련된 일정을 찾아 "
                "한국어로 짧고 명확하게 답하라. 일정 목록에 없으면 없다고 말하라.\n\n"
                f"질문: {query}\n\n일정:\n{context or '(관련 일정 없음)'}"
            )
            response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
            return AiChatResult(response.text or "답변을 생성하지 못했습니다.", _ids(matched))
        except Exception as exc:
            return AiChatResult(f"Gemini 호출에 실패해 로컬 검색 결과로 답합니다. {exc}\n\n{_local_answer(matched)}", _ids(matched))

    return AiChatResult(_local_answer(matched), _ids(matched))


def _match_events(question: str, events: list[ScheduleEvent]) -> list[ScheduleEvent]:
    tokens = [token for token in question.lower().replace("?", " ").split() if len(token) >= 2]
    if not tokens:
        return []
    matched: list[ScheduleEvent] = []
    for event in events:
        haystack = " ".join([event.title, event.description, event.location, event.source]).lower()
        if any(token in haystack for token in tokens):
            matched.append(event)
    return matched


def _local_answer(events: list[ScheduleEvent]) -> str:
    if not events:
        return "질문과 직접 연결되는 일정을 찾지 못했습니다."
    lines = ["관련 일정은 다음과 같습니다."]
    for event in events[:5]:
        lines.append(f"- {event.date_label} {event.time_label}: {event.title}")
    return "\n".join(lines)


def _ids(events: list[ScheduleEvent]) -> list[int]:
    return [int(event.id) for event in events if event.id is not None]
