from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

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
    if not matched and _asks_for_schedule_overview(query):
        matched = _overview_events(query, events)

    context = "\n".join(
        f"- id={event.id}, title={event.title}, "
        f"start_date={event.start_at:%Y-%m-%d}, start_time={event.start_at:%H:%M}, "
        f"end_date={event.end_at:%Y-%m-%d}, end_time={event.end_at:%H:%M}, "
        f"description={event.description}, source={event.source}"
        for event in matched[:12]
    )

    if settings.gemini_api_key:
        try:
            from google import genai

            client = genai.Client(api_key=settings.gemini_api_key)
            prompt = (
                "너는 개인 일정 관리 AI 비서야. 아래 일정 목록에서 사용자 질문과 관련된 일정을 찾아 "
                "한국어로 짧고 명확하게 답해. 사용자가 언제 끝나는지, 종료일, 마감일을 물으면 "
                "end_date와 end_time을 기준으로 답해. 일정 목록이 없으면 없다고 말해.\n\n"
                f"질문: {query}\n\n일정:\n{context or '(관련 일정 없음)'}"
            )
            response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
            return AiChatResult(response.text or "응답을 생성하지 못했습니다.", _ids(matched))
        except Exception as exc:
            return AiChatResult(
                f"Gemini 호출에 실패해 로컬 일정 검색으로 답합니다. {exc}\n\n{_local_answer(query, matched, bool(events))}",
                _ids(matched),
            )

    return AiChatResult(_local_answer(query, matched, bool(events)), _ids(matched))


def _match_events(question: str, events: list[ScheduleEvent]) -> list[ScheduleEvent]:
    stopwords = {"일정", "알려줘", "보여줘", "확인", "검색", "오늘", "내일", "이번", "다음"}
    tokens = [
        token
        for token in question.lower().replace("?", " ").split()
        if len(token) >= 2 and token not in stopwords
    ]
    if not tokens:
        return []
    matched: list[ScheduleEvent] = []
    for event in events:
        haystack = " ".join([event.title, event.description, event.location, event.source]).lower()
        if any(token in haystack for token in tokens):
            matched.append(event)
    return matched


def _asks_for_schedule_overview(question: str) -> bool:
    return any(keyword in question for keyword in ("일정", "오늘", "내일", "이번 주", "이번주", "이번 달", "이번달", "다음", "뭐", "알려"))


def _overview_events(question: str, events: list[ScheduleEvent]) -> list[ScheduleEvent]:
    today = date.today()
    if "오늘" in question:
        return [event for event in events if event.start_at.date() == today]
    if "내일" in question:
        tomorrow = today + timedelta(days=1)
        return [event for event in events if event.start_at.date() == tomorrow]
    if "이번 주" in question or "이번주" in question:
        start = today - timedelta(days=today.weekday())
        end = start + timedelta(days=7)
        return [event for event in events if start <= event.start_at.date() < end]
    if "이번 달" in question or "이번달" in question:
        return [event for event in events if event.start_at.year == today.year and event.start_at.month == today.month]
    return sorted(events, key=lambda event: event.start_at)[:5]


def _local_answer(question: str, events: list[ScheduleEvent], has_total_events: bool) -> str:
    if not events:
        if has_total_events:
            return "질문과 직접 연결되는 일정을 찾지 못했습니다. 제목, 장소, 출처 키워드나 '오늘 일정', '이번 주 일정'처럼 질문해 보세요."
        return "등록된 일정이 없습니다. 일정을 먼저 등록하거나 Google Calendar 가져오기를 실행해 주세요."
    if _asks_for_end_time(question):
        lines = ["관련 일정의 종료 시점은 다음과 같습니다."]
        for event in events[:5]:
            lines.append(f"- {event.title}: {event.end_at:%Y-%m-%d %H:%M} 종료")
        return "\n".join(lines)
    lines = ["관련 일정은 다음과 같습니다."]
    for event in events[:5]:
        lines.append(f"- {event.start_at:%Y-%m-%d %H:%M} ~ {event.end_at:%Y-%m-%d %H:%M}: {event.title}")
    return "\n".join(lines)


def _asks_for_end_time(question: str) -> bool:
    return any(keyword in question for keyword in ("끝", "종료", "마감", "언제까지", "끝나"))


def _ids(events: list[ScheduleEvent]) -> list[int]:
    return [int(event.id) for event in events if event.id is not None]
