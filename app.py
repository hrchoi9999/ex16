from __future__ import annotations

import calendar
from datetime import date, datetime, time, timedelta
from html import escape

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


def init_state() -> None:
    today = date.today()
    st.session_state.setdefault("selected_date", today)
    st.session_state.setdefault("view_mode", "주")
    st.session_state.setdefault("search_query", "")


def inject_pc_styles() -> None:
    st.markdown(
        """
        <style>
        :root {
            --navy: #0F172A;
            --slate: #334155;
            --muted: #64748B;
            --line: #E2E8F0;
            --surface: #F8F9FA;
            --white: #FFFFFF;
            --green: #2F855A;
            --amber: #B7791F;
            --red: #C2410C;
            --font-sans: Pretendard, Inter, Roboto, "Noto Sans KR", Arial, sans-serif;
        }
        html, body, .stApp, [data-testid="stAppViewContainer"] {
            background: var(--white) !important;
            color: var(--navy) !important;
            font-family: var(--font-sans) !important;
        }
        [data-testid="stHeader"] {
            background: rgba(255, 255, 255, .95) !important;
            border-bottom: 1px solid var(--line);
        }
        .block-container {
            padding: .8rem 1rem 1.25rem;
            max-width: 100%;
        }
        * {
            letter-spacing: 0 !important;
        }
        h1, h2, h3, h4, p, span, label {
            font-family: var(--font-sans) !important;
            color: var(--navy);
        }
        h1 {
            font-size: 1.3rem !important;
            line-height: 1.2 !important;
            margin: 0 !important;
        }
        h4 {
            font-size: .95rem !important;
            margin: .35rem 0 .5rem !important;
        }
        div[data-testid="stVerticalBlockBorderWrapper"] {
            border-color: var(--line) !important;
            border-radius: 8px !important;
            background: var(--white) !important;
        }
        .pc-header {
            display: grid;
            grid-template-columns: 260px 1fr 170px 48px 42px;
            gap: .65rem;
            align-items: center;
            padding-bottom: .8rem;
            border-bottom: 1px solid var(--line);
            margin-bottom: .8rem;
        }
        .subtle {
            color: var(--muted) !important;
            font-size: .76rem;
            margin: .15rem 0 0;
        }
        .panel-title {
            color: var(--muted) !important;
            font-size: .72rem;
            font-weight: 800;
            text-transform: uppercase;
            margin: .1rem 0 .45rem;
        }
        .nav-item {
            border-radius: 7px;
            padding: .45rem .55rem;
            margin-bottom: .15rem;
            color: var(--slate);
            background: transparent;
            font-size: .84rem;
            font-weight: 650;
        }
        .nav-item.active {
            background: #EEF2FF;
            color: var(--navy);
            border: 1px solid #CBD5E1;
        }
        .mini-month {
            display: grid;
            grid-template-columns: repeat(7, 1fr);
            gap: .1rem;
        }
        .mini-label {
            text-align: center;
            color: var(--muted) !important;
            font-size: .62rem;
            margin: .05rem 0;
        }
        .mini-day {
            position: relative;
            min-height: 1.45rem;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 999px;
            font-size: .7rem;
            color: var(--slate);
        }
        .mini-day.today {
            background: var(--navy);
            color: #fff;
            font-weight: 800;
        }
        .mini-dot {
            position: absolute;
            bottom: .08rem;
            width: .24rem;
            height: .24rem;
            border-radius: 999px;
            background: var(--amber);
        }
        .stat {
            border: 1px solid var(--line);
            border-radius: 8px;
            padding: .6rem .65rem;
            background: var(--surface);
            margin-bottom: .45rem;
        }
        .stat-value {
            font-size: 1.05rem;
            font-weight: 850;
            margin: 0;
        }
        .stat-label {
            font-size: .72rem;
            color: var(--muted) !important;
            margin: 0;
        }
        .event-card {
            border: 1px solid var(--line);
            border-left: 4px solid var(--navy);
            border-radius: 8px;
            padding: .64rem .7rem;
            margin-bottom: .45rem;
            background: #fff;
        }
        .event-card.important {
            border-left-color: var(--amber);
        }
        .event-card.urgent {
            border-left-color: var(--red);
        }
        .event-title {
            font-size: .86rem;
            font-weight: 800;
            margin: 0 0 .16rem;
        }
        .event-meta {
            color: var(--muted) !important;
            font-size: .74rem;
            margin: 0;
        }
        .priority-tag {
            display: inline-block;
            padding: .1rem .38rem;
            border-radius: 999px;
            background: #E2E8F0;
            color: var(--slate);
            font-size: .68rem;
            font-weight: 800;
            margin-left: .25rem;
        }
        .priority-tag.high {
            background: #FEE2E2;
            color: var(--red);
        }
        .priority-tag.mid {
            background: #FEF3C7;
            color: var(--amber);
        }
        .calendar-grid-cell {
            min-height: 5.4rem;
            border: 1px solid var(--line);
            border-radius: 8px;
            padding: .42rem;
            background: #fff;
            margin-bottom: .42rem;
        }
        .calendar-grid-cell.today {
            background: #F8FAFC;
            border-color: var(--navy);
        }
        .date-label {
            font-weight: 850;
            font-size: .82rem;
            margin-bottom: .25rem;
        }
        .mini-event {
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
            border-radius: 6px;
            padding: .16rem .32rem;
            margin-top: .18rem;
            background: #EEF2FF;
            color: var(--navy);
            font-size: .72rem;
        }
        .empty-note {
            border: 1px dashed var(--line);
            border-radius: 8px;
            background: var(--surface);
            color: var(--muted) !important;
            padding: .75rem;
            font-size: .86rem;
        }
        .stButton > button {
            border-radius: 7px;
        }
        .stTextInput input, .stTextArea textarea {
            font-family: var(--font-sans) !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def event_status(event: ScheduleEvent) -> str:
    if event.importance >= 5:
        return "urgent"
    if event.importance >= 4:
        return "important"
    return ""


def render_event_card(event: ScheduleEvent, include_date: bool = True) -> str:
    tag = "high" if event.importance >= 5 else "mid" if event.importance >= 4 else ""
    date_text = f"{event.date_label} · " if include_date else ""
    desc = f"<p class='event-meta'>{escape(event.description)}</p>" if event.description else ""
    return f"""
    <div class="event-card {event_status(event)}">
        <p class="event-title">{escape(event.title)} <span class="priority-tag {tag}">P{event.importance}</span></p>
        <p class="event-meta">{date_text}{event.time_label}</p>
        {desc}
    </div>
    """


def events_for_day(events: list[ScheduleEvent], day: date) -> list[ScheduleEvent]:
    return [event for event in events if event.start_at.date() == day]


def week_start(day: date) -> date:
    return day - timedelta(days=day.weekday())


def month_start(day: date) -> date:
    return day.replace(day=1)


def mini_month(events: list[ScheduleEvent], anchor: date) -> str:
    event_days = {event.start_at.date() for event in events}
    today = date.today()
    parts = ["<div class='mini-month'>"]
    for label in ["일", "월", "화", "수", "목", "금", "토"]:
        parts.append(f"<p class='mini-label'>{label}</p>")
    for week in calendar.Calendar(firstweekday=6).monthdatescalendar(anchor.year, anchor.month):
        for current_day in week:
            muted = "opacity:.35;" if current_day.month != anchor.month else ""
            today_class = " today" if current_day == today else ""
            dot = "<span class='mini-dot'></span>" if current_day in event_days else ""
            parts.append(f"<div class='mini-day{today_class}' style='{muted}'>{current_day.day}{dot}</div>")
    parts.append("</div>")
    return "".join(parts)


def render_left_panel(events: list[ScheduleEvent], alerts: list[ScheduleEvent]) -> None:
    st.markdown("<p class='panel-title'>Navigation</p>", unsafe_allow_html=True)
    st.markdown("<div class='nav-item active'>Dashboard</div>", unsafe_allow_html=True)
    st.markdown("<div class='nav-item'>Calendar</div>", unsafe_allow_html=True)
    st.markdown("<div class='nav-item'>Tasks</div>", unsafe_allow_html=True)
    st.markdown("<div class='nav-item'>Insights</div>", unsafe_allow_html=True)
    st.markdown("<div class='nav-item'>Settings</div>", unsafe_allow_html=True)
    st.divider()
    st.markdown("<p class='panel-title'>Mini Calendar</p>", unsafe_allow_html=True)
    selected = st.session_state.selected_date
    st.markdown(f"**{selected:%Y년 %m월}**")
    st.markdown(mini_month(events, month_start(selected)), unsafe_allow_html=True)
    st.divider()
    today_events = events_for_day(events, date.today())
    st.markdown(
        f"""
        <div class="stat"><p class="stat-value">{len(today_events)}</p><p class="stat-label">오늘 일정</p></div>
        <div class="stat"><p class="stat-value">{len(alerts)}</p><p class="stat-label">중요/임박 알림</p></div>
        <div class="stat"><p class="stat-value">{len(events)}</p><p class="stat-label">전체 일정</p></div>
        """,
        unsafe_allow_html=True,
    )


def render_day_view(events: list[ScheduleEvent], selected: date) -> None:
    st.markdown(f"#### {selected:%Y년 %m월 %d일} 일간 일정")
    day_events = events_for_day(events, selected)
    if not day_events:
        st.markdown("<div class='empty-note'>선택한 날짜에 일정이 없습니다.</div>", unsafe_allow_html=True)
        return
    for event in day_events:
        st.markdown(render_event_card(event, include_date=False), unsafe_allow_html=True)


def render_week_view(events: list[ScheduleEvent], selected: date) -> None:
    start = week_start(selected)
    end = start + timedelta(days=6)
    st.markdown(f"#### {start:%m월 %d일} - {end:%m월 %d일} 주간 일정")
    cols = st.columns(7)
    for offset, col in enumerate(cols):
        current = start + timedelta(days=offset)
        day_events = events_for_day(events, current)
        today_class = " today" if current == date.today() else ""
        body = "".join(
            f"<div class='mini-event'>{escape(event.time_label)} {escape(event.title)}</div>"
            for event in day_events[:4]
        )
        if len(day_events) > 4:
            body += f"<div class='mini-event'>+{len(day_events) - 4} more</div>"
        col.markdown(
            f"""
            <div class="calendar-grid-cell{today_class}">
                <div class="date-label">{current:%a}<br>{current.day}</div>
                {body or "<p class='event-meta'>일정 없음</p>"}
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_month_view(events: list[ScheduleEvent], selected: date) -> None:
    anchor = month_start(selected)
    st.markdown(f"#### {anchor:%Y년 %m월} 월간 일정")
    header = st.columns(7)
    for col, label in zip(header, ["일", "월", "화", "수", "목", "금", "토"]):
        col.markdown(f"<p class='mini-label'>{label}</p>", unsafe_allow_html=True)
    for week in calendar.Calendar(firstweekday=6).monthdatescalendar(anchor.year, anchor.month):
        cols = st.columns(7)
        for col, current in zip(cols, week):
            day_events = events_for_day(events, current)
            muted = "opacity:.42;" if current.month != anchor.month else ""
            today_class = " today" if current == date.today() else ""
            body = "".join(f"<div class='mini-event'>{escape(event.title)}</div>" for event in day_events[:3])
            col.markdown(
                f"""
                <div class="calendar-grid-cell{today_class}" style="{muted}">
                    <div class="date-label">{current.day}</div>
                    {body or "<p class='event-meta'>-</p>"}
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_center(events: list[ScheduleEvent]) -> None:
    mode = st.session_state.view_mode
    selected = st.session_state.selected_date
    if mode == "일":
        render_day_view(events, selected)
    elif mode == "주":
        render_week_view(events, selected)
    else:
        render_month_view(events, selected)

    st.divider()
    st.markdown("#### 일정 조회 및 변경")
    if not events:
        st.markdown("<div class='empty-note'>등록된 일정이 없습니다.</div>", unsafe_allow_html=True)
        return
    for event in events:
        with st.expander(f"{event.date_label} {event.time_label} · {event.title}", expanded=False):
            with st.form(f"update_{event.id}"):
                updated_title = st.text_input("제목", value=event.title, key=f"title_{event.id}")
                updated_date = st.date_input("날짜", value=event.start_at.date(), key=f"date_{event.id}")
                updated_time = st.time_input("시작 시간", value=event.start_at.time(), key=f"time_{event.id}")
                updated_importance = st.slider("중요도", 1, 5, event.importance, key=f"importance_{event.id}")
                updated_description = st.text_area("설명", value=event.description, key=f"description_{event.id}")
                save_col, delete_col = st.columns(2)
                if save_col.form_submit_button("변경 저장", use_container_width=True):
                    start_at = datetime.combine(updated_date, updated_time)
                    store.update_event(
                        int(event.id),
                        title=updated_title.strip(),
                        start_at=start_at,
                        end_at=start_at + (event.end_at - event.start_at),
                        description=updated_description.strip(),
                        importance=int(updated_importance),
                    )
                    st.success("일정을 변경했습니다.")
                    st.rerun()
                if delete_col.form_submit_button("삭제", use_container_width=True):
                    store.delete_event(int(event.id))
                    st.success("일정을 삭제했습니다.")
                    st.rerun()


def create_event_from_ai(command: str) -> None:
    parsed = parser.parse(command)
    if parsed.event is None:
        st.info(parsed.message)
        return
    sync_result = calendar_client.create_event(parsed.event)
    if sync_result.google_event_id:
        parsed.event.google_event_id = sync_result.google_event_id
    saved = store.add_event(parsed.event)
    st.session_state.selected_date = saved.start_at.date()
    st.success("일정을 등록했습니다.")
    st.write(f"- 제목: {saved.title}")
    st.write(f"- 날짜: {saved.date_label}")
    st.write(f"- 시간: {saved.time_label}")
    st.caption(sync_result.message)


def render_right(events: list[ScheduleEvent], alerts: list[ScheduleEvent]) -> None:
    st.markdown("#### AI 일정 입력")
    command = st.text_area("AI 명령", placeholder="다음 주 화요일 오후 2시에 회의 등록해줘.", height=95)
    if st.button("AI로 등록", type="primary", use_container_width=True):
        if command.strip():
            create_event_from_ai(command)
        else:
            st.warning("일정 명령을 입력해 주세요.")

    with st.expander("직접 등록", expanded=False):
        with st.form("manual_event_form"):
            title = st.text_input("제목", placeholder="회의")
            start_date = st.date_input("날짜", value=st.session_state.selected_date)
            start_time = st.time_input("시작 시간", value=time(9, 0))
            duration = st.number_input("소요 시간(분)", 15, 480, 60, 15)
            importance = st.slider("중요도", 1, 5, 3)
            description = st.text_area("설명")
            if st.form_submit_button("일정 등록", type="primary", use_container_width=True):
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
                        importance=int(importance),
                    )
                    store.add_event(event)
                    st.session_state.selected_date = start_date
                    st.success("일정을 등록했습니다.")
                    st.rerun()

    st.divider()
    st.markdown("#### 중요한 일정 알림")
    if not alerts:
        st.markdown("<div class='empty-note'>표시할 중요/임박 일정이 없습니다.</div>", unsafe_allow_html=True)
    for event in alerts[:4]:
        st.markdown(render_event_card(event), unsafe_allow_html=True)

    st.divider()
    st.markdown("#### 우선순위 추천")
    upcoming = [event for event in events if event.end_at >= datetime.now()]
    recommendations = recommend_priorities(upcoming)
    if not recommendations:
        st.markdown("<div class='empty-note'>추천할 일정이 없습니다.</div>", unsafe_allow_html=True)
    for item in recommendations[:4]:
        st.metric(item.event.title, f"{item.score:.2f}점", item.reason)


init_state()
inject_pc_styles()

events = store.list_events(include_past=True)
alerts = store.upcoming_important()

st.markdown(
    """
    <div class="pc-header">
        <div>
            <h1>개인 일정 관리 AI 에이전트</h1>
            <p class="subtle">Personal Assistant Agent · PC workspace</p>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

top_search, top_date, top_view, top_notice, top_profile = st.columns([1.4, .55, .5, .3, .22], gap="small")
with top_search:
    st.text_input("전체 일정 검색", key="search_query", placeholder="제목 또는 설명 검색", label_visibility="collapsed")
with top_date:
    picked = st.date_input("기준 날짜", value=st.session_state.selected_date, label_visibility="collapsed")
    if picked != st.session_state.selected_date:
        st.session_state.selected_date = picked
        st.rerun()
with top_view:
    st.radio("보기", ["일", "주", "월"], key="view_mode", horizontal=True, label_visibility="collapsed")
with top_notice:
    st.button(f"알림 {len(alerts)}", use_container_width=True)
with top_profile:
    st.markdown("<div class='stat' style='text-align:center;padding:.45rem .2rem'><b>ME</b></div>", unsafe_allow_html=True)

if st.session_state.search_query.strip():
    query = st.session_state.search_query.strip().lower()
    events = [
        event
        for event in events
        if query in event.title.lower() or query in event.description.lower() or query in event.location.lower()
    ]
    st.caption(f"검색 결과 {len(events)}개")

left, center, right = st.columns([.82, 2.85, 1.05], gap="medium")
with left:
    with st.container(border=True):
        render_left_panel(events, alerts)
with center:
    with st.container(border=True):
        render_center(events)
with right:
    with st.container(border=True):
        render_right(events, alerts)

st.caption(
    "SQLite local-first · "
    f"DB: {settings.database_path} · "
    f"Google Calendar API: {'on' if calendar_client.enabled else 'off'} · "
    f"LLM parser: {'on' if settings.llm_enabled else 'rule-based'}"
)
