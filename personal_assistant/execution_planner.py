from __future__ import annotations

import json
import re
from datetime import date, timedelta

from .config import settings
from .models import ScheduleEvent, TaskPlanItem


STAGE_ORDER = ("today", "this_week", "before_deadline")
STAGE_LABELS = {
    "today": "오늘 할 일",
    "this_week": "이번주 준비",
    "before_deadline": "마감전 체크",
}


def generate_task_plan(event: ScheduleEvent) -> list[TaskPlanItem]:
    if settings.gemini_api_key:
        try:
            generated = _generate_with_gemini(event)
            if generated:
                return generated
        except Exception:
            pass
    return _generate_with_rules(event)


def _generate_with_gemini(event: ScheduleEvent) -> list[TaskPlanItem]:
    from google import genai

    client = genai.Client(api_key=settings.gemini_api_key)
    prompt = (
        "너는 개인 일정 실행 코치야. 일정 하나를 실행 가능한 체크리스트로 분해해.\n"
        "반드시 JSON 배열만 응답하고, 각 항목은 stage, title, due_date, estimated_minutes를 가진다.\n"
        "stage는 today, this_week, before_deadline 중 하나만 사용한다.\n"
        "due_date는 YYYY-MM-DD 형식으로 작성한다.\n"
        "총 5~7개 항목으로, 한국어 한 줄 할 일로 작성한다.\n\n"
        f"오늘: {date.today():%Y-%m-%d}\n"
        f"일정 제목: {event.title}\n"
        f"일정 날짜: {event.start_at:%Y-%m-%d}\n"
        f"설명: {event.description or '(없음)'}\n"
        f"출처: {event.source}\n"
    )
    response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
    payload = _extract_json(response.text or "")
    rows = json.loads(payload)
    return _rows_to_items(event, rows, source="gemini")


def _extract_json(text: str) -> str:
    fenced = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
    if fenced:
        return fenced.group(1).strip()
    start = text.find("[")
    end = text.rfind("]")
    if start >= 0 and end > start:
        return text[start : end + 1]
    return text.strip()


def _rows_to_items(event: ScheduleEvent, rows: list[dict[str, object]], source: str) -> list[TaskPlanItem]:
    items: list[TaskPlanItem] = []
    for index, row in enumerate(rows):
        stage = str(row.get("stage", "")).strip()
        title = str(row.get("title", "")).strip()
        if stage not in STAGE_ORDER or not title:
            continue
        try:
            due_date = date.fromisoformat(str(row.get("due_date", ""))[:10])
        except ValueError:
            due_date = _default_due_date(event, stage)
        minutes = _safe_minutes(row.get("estimated_minutes", 30))
        items.append(
            TaskPlanItem(
                id=None,
                event_id=int(event.id or 0),
                stage=stage,
                title=title,
                due_date=due_date,
                estimated_minutes=minutes,
                source=source,
                sort_order=index,
            )
        )
    return items[:8] or _generate_with_rules(event)


def _generate_with_rules(event: ScheduleEvent) -> list[TaskPlanItem]:
    is_deadline = event.title.startswith("[마감]") or bool(event.source_url)
    templates = _deadline_templates(event) if is_deadline else _general_templates(event)
    items: list[TaskPlanItem] = []
    for index, (stage, title, minutes) in enumerate(templates):
        items.append(
            TaskPlanItem(
                id=None,
                event_id=int(event.id or 0),
                stage=stage,
                title=title,
                due_date=_default_due_date(event, stage),
                estimated_minutes=minutes,
                source="rule",
                sort_order=index,
            )
        )
    return items


def _deadline_templates(event: ScheduleEvent) -> list[tuple[str, str, int]]:
    clean_title = event.title.replace("[마감]", "").strip()
    return [
        ("today", f"{clean_title} 공고 원문과 지원 조건 확인", 30),
        ("today", "필요 서류와 계정/제출 경로 목록 만들기", 30),
        ("this_week", "지원 내용 초안 작성 및 부족한 자료 요청", 90),
        ("this_week", "제출 파일명, 증빙자료, 연락처 정보 점검", 45),
        ("before_deadline", "최종 제출 전 필수 항목 누락 여부 확인", 30),
        ("before_deadline", "마감일 전에 제출 완료 후 접수 확인 저장", 30),
    ]


def _general_templates(event: ScheduleEvent) -> list[tuple[str, str, int]]:
    return [
        ("today", f"{event.title} 목적과 준비물 확인", 20),
        ("today", "참석자/장소/자료 링크 등 핵심 정보 정리", 20),
        ("this_week", "필요 자료 준비 및 사전 질문 작성", 45),
        ("this_week", "일정 전 실행 가능한 다음 행동 1개 완료", 30),
        ("before_deadline", "일정 직전 알림과 준비 상태 최종 확인", 15),
    ]


def _default_due_date(event: ScheduleEvent, stage: str) -> date:
    today = date.today()
    event_day = event.start_at.date()
    if stage == "today":
        return min(today, event_day)
    if stage == "this_week":
        return min(max(today, event_day - timedelta(days=7)), event_day)
    return max(today, event_day - timedelta(days=1))


def _safe_minutes(value: object) -> int:
    try:
        minutes = int(value)
    except (TypeError, ValueError):
        minutes = 30
    return min(max(minutes, 10), 240)
