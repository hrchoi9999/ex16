from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta

from .config import settings
from .models import ScheduleEvent


WEEKDAYS = {
    "월요일": 0,
    "화요일": 1,
    "수요일": 2,
    "목요일": 3,
    "금요일": 4,
    "토요일": 5,
    "일요일": 6,
}


@dataclass(frozen=True)
class ParsedCommand:
    intent: str
    event: ScheduleEvent | None
    message: str


class CommandParser:
    def parse(self, text: str, today: date | None = None) -> ParsedCommand:
        today = today or date.today()
        cleaned = text.strip()
        intent = self._detect_intent(cleaned)
        if intent != "create":
            return ParsedCommand(intent=intent, event=None, message="조회/변경 명령은 화면의 일정 목록에서 처리하세요.")

        llm_event = self._parse_with_llm(cleaned, today)
        if llm_event:
            return ParsedCommand(intent="create", event=llm_event, message="LLM 파서로 일정을 해석했습니다.")

        start_day = self._parse_date(cleaned, today)
        start_time = self._parse_time(cleaned)
        title = self._parse_title(cleaned)
        start_at = datetime.combine(start_day, start_time)
        event = ScheduleEvent(
            id=None,
            title=title,
            start_at=start_at,
            end_at=start_at + timedelta(hours=1),
            importance=self._parse_importance(cleaned),
            description=cleaned,
        )
        return ParsedCommand(intent="create", event=event, message="규칙 기반 파서로 일정을 해석했습니다.")

    def _detect_intent(self, text: str) -> str:
        if any(keyword in text for keyword in ["등록", "추가", "넣어", "만들"]):
            return "create"
        if any(keyword in text for keyword in ["조회", "보여", "확인", "알려"]):
            return "list"
        if any(keyword in text for keyword in ["변경", "수정", "미뤄", "옮겨"]):
            return "update"
        return "create"

    def _parse_date(self, text: str, today: date) -> date:
        if "모레" in text:
            return today + timedelta(days=2)
        if "내일" in text:
            return today + timedelta(days=1)
        if "오늘" in text:
            return today

        for label, weekday in WEEKDAYS.items():
            if label not in text:
                continue
            if "다음 주" in text or "다음주" in text:
                next_monday = today + timedelta(days=(7 - today.weekday()))
                return next_monday + timedelta(days=weekday)
            days_ahead = (weekday - today.weekday()) % 7
            if days_ahead == 0:
                days_ahead = 7
            return today + timedelta(days=days_ahead)

        iso_match = re.search(r"(20\d{2})[-./년]\s*(\d{1,2})[-./월]\s*(\d{1,2})", text)
        if iso_match:
            year, month, day = map(int, iso_match.groups())
            return date(year, month, day)

        month_day_match = re.search(r"(\d{1,2})월\s*(\d{1,2})일", text)
        if month_day_match:
            month, day = map(int, month_day_match.groups())
            parsed = date(today.year, month, day)
            if parsed < today:
                parsed = date(today.year + 1, month, day)
            return parsed

        return today

    def _parse_time(self, text: str) -> time:
        match = re.search(r"(오전|오후)?\s*(\d{1,2})시(?:\s*(\d{1,2})분|반)?", text)
        if not match:
            return time(9, 0)
        meridiem, hour_text, minute_text = match.groups()
        hour = int(hour_text)
        minute = 30 if "반" in match.group(0) else int(minute_text or 0)
        if meridiem == "오후" and hour < 12:
            hour += 12
        if meridiem == "오전" and hour == 12:
            hour = 0
        return time(hour, minute)

    def _parse_title(self, text: str) -> str:
        title = text
        patterns = [
            r"다음\s*주\s*[월화수목금토일]요일",
            r"이번\s*주\s*[월화수목금토일]요일",
            r"[월화수목금토일]요일",
            r"오늘|내일|모레",
            r"(20\d{2})[-./년]\s*(\d{1,2})[-./월]\s*(\d{1,2})일?",
            r"\d{1,2}월\s*\d{1,2}일",
            r"(오전|오후)?\s*\d{1,2}시(?:\s*\d{1,2}분|반)?",
            r"중요한|긴급한|필수",
            r"등록해줘|등록|추가해줘|추가|넣어줘|넣어|만들어줘|만들어",
        ]
        for pattern in patterns:
            title = re.sub(pattern, " ", title)
        title = re.sub(r"\b[에은는이가을를]\b", " ", title)
        title = re.sub(r"\s+", " ", title).strip(" .,요에")
        return title or "새 일정"

    def _parse_importance(self, text: str) -> int:
        if any(keyword in text for keyword in ["중요", "긴급", "필수"]):
            return 5
        if any(keyword in text for keyword in ["가벼운", "참고"]):
            return 2
        return 3

    def _parse_with_llm(self, text: str, today: date) -> ScheduleEvent | None:
        if not settings.llm_enabled:
            return None
        prompt = (
            "Extract a calendar event from Korean text as JSON with keys "
            "title, date(YYYY-MM-DD), time(HH:MM), importance(1-5), description. "
            f"Today is {today.isoformat()}. Text: {text}"
        )
        try:
            if settings.gemini_api_key:
                from google import genai

                client = genai.Client(api_key=settings.gemini_api_key)
                response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
                payload = self._extract_json(response.text or "")
            else:
                from openai import OpenAI

                client = OpenAI(api_key=settings.openai_api_key)
                response = client.responses.create(model="gpt-4.1-mini", input=prompt)
                payload = self._extract_json(response.output_text)
            start_at = datetime.fromisoformat(f"{payload['date']}T{payload['time']}")
            return ScheduleEvent(
                id=None,
                title=str(payload["title"]),
                start_at=start_at,
                end_at=start_at + timedelta(hours=1),
                importance=int(payload.get("importance", 3)),
                description=str(payload.get("description", text)),
            )
        except Exception:
            return None

    @staticmethod
    def _extract_json(raw: str) -> dict[str, object]:
        match = re.search(r"\{.*\}", raw, re.S)
        if not match:
            raise ValueError("LLM response did not include JSON.")
        return json.loads(match.group(0))
