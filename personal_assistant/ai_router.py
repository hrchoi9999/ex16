from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AiRoute:
    intent: str
    menu: str = "상세 정보"


def route_ai_command(text: str) -> AiRoute:
    command = _normalize(text)
    if not command:
        return AiRoute("query")

    if _has_any(command, "삭제", "지워", "제거"):
        return AiRoute("delete_help", "일정 편집")
    if _has_any(command, "수정", "변경", "미뤄", "옮겨"):
        return AiRoute("edit_help", "일정 편집")
    if _has_any(command, "구글", "google", "캘린더 가져", "캘린더 동기", "동기화", "가져와"):
        return AiRoute("google_sync", "Google 연동")
    if _has_any(command, "관심 사이트", "공고", "모집", "크롤", "수집", "k-startup", "50플러스"):
        if _has_any(command, "캘린더", "일정", "등록", "넣어", "넣", "추가"):
            return AiRoute("collect_and_register_sites", "관심 사이트")
        return AiRoute("collect_sites", "관심 사이트")
    if _has_any(command, "우선순위", "우선 순위", "중요한", "먼저"):
        return AiRoute("priority", "우선순위")
    if _has_any(command, "리스크", "위험", "마감 위험", "늦을"):
        return AiRoute("risk", "리스크 코치")
    if _has_any(command, "실행 계획", "할 일", "작업 분해", "계획"):
        return AiRoute("execution_plan", "실행 계획")
    if _has_any(command, "브리핑", "요약", "정리"):
        return AiRoute("briefing", "브리핑")
    if _has_any(command, "ai 일정", "자연어 일정"):
        return AiRoute("ai_event_menu", "AI 일정")
    if _has_any(command, "등록", "추가", "넣어", "만들"):
        return AiRoute("create_event", "상세 정보")

    return AiRoute("query", "상세 정보")


def _normalize(text: str) -> str:
    return text.strip().lower().replace("\n", " ")


def _has_any(text: str, *keywords: str) -> bool:
    return any(keyword.lower() in text for keyword in keywords)
