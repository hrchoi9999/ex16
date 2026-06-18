from __future__ import annotations

from datetime import datetime, time, timedelta

import streamlit as st

from personal_assistant.config import settings
from personal_assistant.database import ScheduleStore
from personal_assistant.google_calendar import GoogleCalendarClient
from personal_assistant.models import ScheduleEvent
from personal_assistant.nlp import CommandParser
from personal_assistant.priority import recommend_priorities


st.set_page_config(page_title="Personal Assistant Agent", page_icon="📅", layout="wide")


@st.cache_resource
def get_store() -> ScheduleStore:
    return ScheduleStore(settings.database_path)


store = get_store()
parser = CommandParser()
calendar_client = GoogleCalendarClient()

st.title("개인 일정 관리 웹서비스 AI 에이전트")

command, manual = st.tabs(["AI 명령", "직접 등록"])

with command:
    st.subheader("자연어로 일정 등록")
    user_command = st.text_input("명령", placeholder="다음 주 화요일 오후 2시에 회의 등록해줘.")
    if st.button("AI 에이전트 실행", type="primary", use_container_width=True):
        if not user_command.strip():
            st.warning("일정 명령을 입력해 주세요.")
        else:
            parsed = parser.parse(user_command)
            if parsed.event is None:
                st.info(parsed.message)
            else:
                sync_result = calendar_client.create_event(parsed.event)
                if sync_result.google_event_id:
                    parsed.event.google_event_id = sync_result.google_event_id
                saved = store.add_event(parsed.event)
                st.success("일정을 등록했습니다.")
                st.write(f"- 제목: {saved.title}")
                st.write(f"- 날짜: {saved.date_label}")
                st.write(f"- 시간: {saved.time_label}")
                st.caption(sync_result.message)

with manual:
    st.subheader("폼으로 일정 등록")
    with st.form("manual_event_form"):
        title = st.text_input("제목", placeholder="회의")
        start_date = st.date_input("날짜")
        start_time = st.time_input("시작 시간", value=time(9, 0))
        duration = st.number_input("소요 시간(분)", min_value=15, max_value=480, value=60, step=15)
        importance = st.slider("중요도", min_value=1, max_value=5, value=3)
        location = st.text_input("장소")
        description = st.text_area("설명")
        submitted = st.form_submit_button("일정 등록", type="primary", use_container_width=True)
        if submitted:
            if not title.strip():
                st.warning("제목을 입력해 주세요.")
            else:
                start_at = datetime.combine(start_date, start_time)
                event = ScheduleEvent(
                    id=None,
                    title=title.strip(),
                    start_at=start_at,
                    end_at=start_at + timedelta(minutes=int(duration)),
                    description=description.strip(),
                    location=location.strip(),
                    importance=int(importance),
                )
                sync_result = calendar_client.create_event(event)
                if sync_result.google_event_id:
                    event.google_event_id = sync_result.google_event_id
                store.add_event(event)
                st.success("일정을 등록했습니다.")
                st.caption(sync_result.message)

events = store.list_events()
alerts = store.upcoming_important()
recommendations = recommend_priorities(events)

left, center, right = st.columns([1.2, 1.6, 1.2])

with left:
    st.subheader("중요 일정 알림")
    if not alerts:
        st.info("현재 표시할 중요/임박 일정이 없습니다.")
    for event in alerts:
        st.warning(f"{event.date_label} {event.time_label} · {event.title} · 중요도 {event.importance}")

with center:
    st.subheader("일정 조회 및 변경")
    if not events:
        st.info("등록된 일정이 없습니다.")
    for event in events:
        with st.expander(f"{event.date_label} {event.time_label} · {event.title}", expanded=False):
            with st.form(f"update_{event.id}"):
                updated_title = st.text_input("제목", value=event.title, key=f"title_{event.id}")
                updated_date = st.date_input("날짜", value=event.start_at.date(), key=f"date_{event.id}")
                updated_time = st.time_input("시작 시간", value=event.start_at.time(), key=f"time_{event.id}")
                updated_importance = st.slider(
                    "중요도",
                    min_value=1,
                    max_value=5,
                    value=event.importance,
                    key=f"importance_{event.id}",
                )
                updated_description = st.text_area("설명", value=event.description, key=f"description_{event.id}")
                save_col, delete_col = st.columns(2)
                save_clicked = save_col.form_submit_button("변경 저장", use_container_width=True)
                delete_clicked = delete_col.form_submit_button("삭제", use_container_width=True)
                if save_clicked:
                    start_at = datetime.combine(updated_date, updated_time)
                    store.update_event(
                        int(event.id),
                        title=updated_title.strip(),
                        start_at=start_at,
                        end_at=start_at + (event.end_at - event.start_at),
                        description=updated_description.strip(),
                        importance=int(updated_importance),
                    )
                    st.success("일정을 변경했습니다. 새로고침하면 목록에 반영됩니다.")
                if delete_clicked:
                    store.delete_event(int(event.id))
                    st.success("일정을 삭제했습니다. 새로고침하면 목록에 반영됩니다.")

with right:
    st.subheader("우선순위 추천")
    if not recommendations:
        st.info("추천할 일정이 없습니다.")
    for item in recommendations[:5]:
        st.metric(item.event.title, f"{item.score:.2f}점", item.reason)

st.caption(
    "SQLite local-first · "
    f"DB: {settings.database_path} · "
    f"Google Calendar: {'on' if calendar_client.enabled else 'off'} · "
    f"LLM parser: {'on' if settings.llm_enabled else 'rule-based'}"
)

