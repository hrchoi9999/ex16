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


st.set_page_config(page_title="AI 일정 관리", page_icon="📅", layout="wide")


@st.cache_resource
def get_store() -> ScheduleStore:
    return ScheduleStore(settings.database_path)


store = get_store()
parser = CommandParser()
calendar_client = GoogleCalendarClient()


def initialize_state() -> None:
    today = date.today()
    st.session_state.setdefault("selected_date", today)
    st.session_state.setdefault("calendar_anchor", today.replace(day=1))
    st.session_state.setdefault("view_mode", "주")
    st.session_state.setdefault("menu_collapsed", False)
    st.session_state.setdefault("global_search", "")


def inject_styles() -> None:
    st.markdown(
        """
        <style>
        :root {
            --navy: #0F172A;
            --slate: #334155;
            --muted: #64748b;
            --line: #e2e8f0;
            --surface: #F8F9FA;
            --card: #FFFFFF;
            --green: #2F855A;
            --amber: #B7791F;
            --red: #C2410C;
            --font-sans: Pretendard, Inter, Roboto, "Noto Sans KR", Arial, sans-serif;
        }
        html, body, .stApp, [data-testid="stAppViewContainer"] {
            background: var(--card) !important;
            color: var(--navy) !important;
            font-family: var(--font-sans) !important;
        }
        [data-testid="stHeader"] {
            background: rgba(255, 255, 255, .92) !important;
            border-bottom: 1px solid var(--line);
        }
        * {
            letter-spacing: 0 !important;
        }
        .block-container {
            padding: .75rem 1rem 1.1rem;
            max-width: 100%;
        }
        h1, h2, h3, h4, p, label, span {
            color: var(--navy);
            font-family: var(--font-sans) !important;
        }
        h4 {
            font-size: .98rem !important;
            margin: .35rem 0 .55rem !important;
        }
        div[data-testid="stVerticalBlockBorderWrapper"] {
            border-color: var(--line) !important;
            border-radius: 8px !important;
            background: var(--card);
        }
        [data-testid="stSidebar"], [data-testid="stSidebarContent"] {
            background: var(--surface) !important;
            color: var(--navy) !important;
        }
        .app-title {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 1rem;
            padding: .2rem 0 .85rem;
            border-bottom: 1px solid var(--line);
            margin-bottom: .85rem;
        }
        .app-title h1 {
            color: var(--navy) !important;
            font-size: 1.35rem;
            line-height: 1.15;
            margin: 0;
        }
        .top-header {
            display: grid;
            grid-template-columns: minmax(220px, 1fr) 180px 44px 44px;
            gap: .6rem;
            align-items: center;
            margin-bottom: .75rem;
        }
        .icon-button, .profile-dot {
            width: 38px;
            height: 38px;
            border: 1px solid var(--line);
            border-radius: 999px;
            display: flex;
            align-items: center;
            justify-content: center;
            background: var(--surface);
            color: var(--navy);
            font-size: .85rem;
            font-weight: 800;
        }
        .workspace-label {
            color: var(--muted);
            font-size: .76rem;
            margin: 0;
        }
        .panel-title {
            font-size: .82rem;
            font-weight: 700;
            color: var(--navy);
            margin: .05rem 0 .38rem;
            text-transform: uppercase;
        }
        .nav-item {
            display: flex;
            align-items: center;
            gap: .5rem;
            padding: .4rem .46rem;
            border-radius: 7px;
            color: var(--slate);
            font-size: .82rem;
            border: 1px solid transparent;
            margin-bottom: .12rem;
        }
        .nav-item.active {
            color: var(--navy);
            background: #eef2ff;
            border-color: #c7d2fe;
            font-weight: 700;
        }
        .summary-card {
            border: 1px solid var(--line);
            border-radius: 8px;
            padding: .55rem .6rem;
            background: #fff;
            margin-bottom: .42rem;
        }
        .summary-value {
            font-size: 1rem;
            font-weight: 800;
            color: var(--navy);
            margin: 0;
        }
        .summary-label {
            color: var(--muted);
            font-size: .72rem;
            margin: 0;
        }
        .event-card {
            border: 1px solid var(--line);
            border-left: 4px solid var(--navy);
            border-radius: 8px;
            padding: .7rem .75rem;
            margin-bottom: .55rem;
            background: #fff;
        }
        .event-card.urgent {
            border-left-color: var(--red);
        }
        .event-card.important {
            border-left-color: var(--amber);
        }
        .event-title {
            font-weight: 800;
            color: var(--navy);
            font-size: .86rem;
            margin: 0 0 .2rem;
        }
        .event-meta {
            color: var(--muted);
            font-size: .76rem;
            margin: 0;
        }
        .tag {
            display: inline-block;
            padding: .13rem .42rem;
            border-radius: 999px;
            font-size: .72rem;
            font-weight: 700;
            background: #e2e8f0;
            color: var(--slate);
            margin-left: .35rem;
        }
        .tag.high {
            background: #fee2e2;
            color: var(--red);
        }
        .tag.mid {
            background: #fef3c7;
            color: var(--amber);
        }
        .calendar-cell {
            min-height: 5.45rem;
            border: 1px solid var(--line);
            border-radius: 8px;
            padding: .45rem;
            background: #fff;
            margin-bottom: .5rem;
        }
        .mini-month {
            display: grid;
            grid-template-columns: repeat(7, minmax(0, 1fr));
            gap: .08rem;
            margin-top: .35rem;
        }
        .mini-month-label {
            color: var(--muted) !important;
            font-size: .64rem;
            text-align: center;
            margin: 0 0 .12rem;
        }
        .mini-day {
            position: relative;
            min-height: 1.42rem;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 999px;
            color: var(--slate);
            font-size: .7rem;
            line-height: 1;
        }
        .mini-day.today-dot {
            background: var(--navy);
            color: #fff;
            font-weight: 800;
        }
        .day-dot {
            position: absolute;
            width: .25rem;
            height: .25rem;
            border-radius: 999px;
            background: var(--amber);
            bottom: .1rem;
        }
        .calendar-cell.today {
            border-color: var(--navy);
            background: #f8fafc;
        }
        .calendar-date {
            font-weight: 800;
            color: var(--navy);
            margin-bottom: .35rem;
        }
        .mini-event {
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
            border-radius: 6px;
            background: #eef2ff;
            color: var(--navy);
            font-size: .74rem;
            padding: .18rem .32rem;
            margin-top: .22rem;
        }
        .mini-event.urgent {
            background: #fee2e2;
            color: var(--red);
        }
        .mini-event.important {
            background: #fef3c7;
            color: var(--amber);
        }
        .empty-note {
            color: var(--muted);
            border: 1px dashed var(--line);
            border-radius: 8px;
            padding: .8rem;
            background: var(--surface);
            font-size: .9rem;
        }
        .stButton > button {
            border-radius: 7px;
        }
        .stTextInput input, .stTextArea textarea {
            font-family: var(--font-sans) !important;
        }
        .stProgress > div > div > div {
            background-color: var(--green) !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def event_style(event: ScheduleEvent) -> str:
    if event.importance >= 5:
        return "urgent"
    if event.importance >= 4:
        return "important"
    return ""


def event_card(event: ScheduleEvent, show_date: bool = True) -> str:
    tag_class = "high" if event.importance >= 5 else "mid" if event.importance >= 4 else ""
    date_text = f"{event.date_label} · " if show_date else ""
    description = f"<p class='event-meta'>{escape(event.description)}</p>" if event.description else ""
    return f"""
    <div class="event-card {event_style(event)}">
        <p class="event-title">{escape(event.title)}
            <span class="tag {tag_class}">중요도 {event.importance}</span>
        </p>
        <p class="event-meta">{date_text}{event.time_label}</p>
        {description}
    </div>
    """


def events_for_day(events: list[ScheduleEvent], selected_day: date) -> list[ScheduleEvent]:
    return [event for event in events if event.start_at.date() == selected_day]


def events_for_range(events: list[ScheduleEvent], start_day: date, end_day: date) -> list[ScheduleEvent]:
    return [event for event in events if start_day <= event.start_at.date() <= end_day]


def week_start(day: date) -> date:
    return day - timedelta(days=day.weekday())


def add_months(day: date, months: int) -> date:
    month_index = day.month - 1 + months
    year = day.year + month_index // 12
    month = month_index % 12 + 1
    return date(year, month, 1)


def mini_month_html(events: list[ScheduleEvent], anchor: date) -> str:
    event_days = {event.start_at.date() for event in events}
    today = date.today()
    rows: list[str] = []
    rows.append("<div class='mini-month'>")
    for label in ["일", "월", "화", "수", "목", "금", "토"]:
        rows.append(f"<p class='mini-month-label'>{label}</p>")
    for week in calendar.Calendar(firstweekday=6).monthdatescalendar(anchor.year, anchor.month):
        for current_day in week:
            is_muted = current_day.month != anchor.month
            is_today = current_day == today
            has_event = current_day in event_days
            style = "opacity:.34;" if is_muted else ""
            marker = "<span class='day-dot'></span>" if has_event else ""
            today_class = " today-dot" if is_today else ""
            rows.append(
                f"<div class='mini-day{today_class}' style='{style}'>{current_day.day}{marker}</div>"
            )
    rows.append("</div>")
    return "".join(rows)


def render_left_panel(events: list[ScheduleEvent], alerts: list[ScheduleEvent]) -> None:
    st.markdown("<p class='panel-title'>워크스페이스</p>", unsafe_allow_html=True)
    if st.button(
        "메뉴 펼치기" if st.session_state.menu_collapsed else "메뉴 접기",
        use_container_width=True,
        key="toggle_menu",
    ):
        st.session_state.menu_collapsed = not st.session_state.menu_collapsed
        st.rerun()
    if st.session_state.menu_collapsed:
        st.markdown("<div class='nav-item active'>D</div>", unsafe_allow_html=True)
        st.markdown("<div class='nav-item'>C</div>", unsafe_allow_html=True)
        st.markdown("<div class='nav-item'>P</div>", unsafe_allow_html=True)
        st.markdown("<div class='nav-item'>A</div>", unsafe_allow_html=True)
        st.markdown("<div class='nav-item'>S</div>", unsafe_allow_html=True)
    else:
        st.markdown("<div class='nav-item active'>Dashboard</div>", unsafe_allow_html=True)
        st.markdown("<div class='nav-item'>Calendar</div>", unsafe_allow_html=True)
        st.markdown("<div class='nav-item'>Projects</div>", unsafe_allow_html=True)
        st.markdown("<div class='nav-item'>Analytics</div>", unsafe_allow_html=True)
        st.markdown("<div class='nav-item'>Settings</div>", unsafe_allow_html=True)

    st.divider()
    st.markdown("<p class='panel-title'>월간 캘린더</p>", unsafe_allow_html=True)
    prev_col, title_col, next_col = st.columns([.55, 1.7, .55])
    if prev_col.button("‹", use_container_width=True, key="prev_month"):
        st.session_state.calendar_anchor = add_months(st.session_state.calendar_anchor, -1)
        st.rerun()
    title_col.markdown(
        f"<p style='text-align:center;font-weight:800;margin:.35rem 0'>{st.session_state.calendar_anchor:%Y년 %m월}</p>",
        unsafe_allow_html=True,
    )
    if next_col.button("›", use_container_width=True, key="next_month"):
        st.session_state.calendar_anchor = add_months(st.session_state.calendar_anchor, 1)
        st.rerun()

    st.markdown(mini_month_html(events, st.session_state.calendar_anchor), unsafe_allow_html=True)

    st.divider()
    st.markdown("<p class='panel-title'>오늘 요약</p>", unsafe_allow_html=True)
    today_events = events_for_day(events, date.today())
    st.markdown(
        f"""
        <div class="summary-card">
            <p class="summary-value">{len(today_events)}</p>
            <p class="summary-label">오늘 일정</p>
        </div>
        <div class="summary-card">
            <p class="summary-value">{len(alerts)}</p>
            <p class="summary-label">중요/임박 알림</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_day_view(events: list[ScheduleEvent], selected_day: date) -> None:
    day_events = events_for_day(events, selected_day)
    st.markdown(f"#### {selected_day:%Y년 %m월 %d일} 일간 일정")
    if not day_events:
        st.markdown("<div class='empty-note'>선택한 날짜에 등록된 일정이 없습니다.</div>", unsafe_allow_html=True)
        return
    for event in day_events:
        st.markdown(event_card(event, show_date=False), unsafe_allow_html=True)


def render_week_view(events: list[ScheduleEvent], selected_day: date) -> None:
    start_day = week_start(selected_day)
    end_day = start_day + timedelta(days=6)
    st.markdown(f"#### {start_day:%m월 %d일} - {end_day:%m월 %d일} 주간 일정")
    day_cols = st.columns(7)
    for offset, col in enumerate(day_cols):
        current_day = start_day + timedelta(days=offset)
        day_events = events_for_day(events, current_day)
        today_class = " today" if current_day == date.today() else ""
        body = "".join(
            f"<div class='mini-event {event_style(event)}'>{escape(event.time_label)} {escape(event.title)}</div>"
            for event in day_events[:4]
        )
        if len(day_events) > 4:
            body += f"<div class='mini-event'>+{len(day_events) - 4}개 더보기</div>"
        col.markdown(
            f"""
            <div class="calendar-cell{today_class}">
                <div class="calendar-date">{current_day:%a}<br>{current_day.day}</div>
                {body or "<p class='event-meta'>일정 없음</p>"}
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_month_view(events: list[ScheduleEvent], selected_day: date) -> None:
    anchor = selected_day.replace(day=1)
    st.markdown(f"#### {anchor:%Y년 %m월} 월간 일정")
    weekdays = ["일", "월", "화", "수", "목", "금", "토"]
    header_cols = st.columns(7)
    for col, label in zip(header_cols, weekdays):
        col.markdown(f"<p style='text-align:center;font-weight:800;color:#64748b'>{label}</p>", unsafe_allow_html=True)
    for week in calendar.Calendar(firstweekday=6).monthdatescalendar(anchor.year, anchor.month):
        week_cols = st.columns(7)
        for current_day, col in zip(week, week_cols):
            day_events = events_for_day(events, current_day)
            muted = "opacity:.38;" if current_day.month != anchor.month else ""
            today_class = " today" if current_day == date.today() else ""
            body = "".join(
                f"<div class='mini-event {event_style(event)}'>{escape(event.title)}</div>"
                for event in day_events[:3]
            )
            col.markdown(
                f"""
                <div class="calendar-cell{today_class}" style="{muted}">
                    <div class="calendar-date">{current_day.day}</div>
                    {body or "<p class='event-meta'>-</p>"}
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_center_panel(events: list[ScheduleEvent]) -> None:
    selected_day = st.session_state.selected_date
    st.markdown("<p class='panel-title'>캘린더</p>", unsafe_allow_html=True)
    top_left, top_right = st.columns([1.4, 1])
    with top_left:
        picked_day = st.date_input("기준 날짜", value=selected_day, label_visibility="collapsed")
        if picked_day != selected_day:
            st.session_state.selected_date = picked_day
            st.session_state.calendar_anchor = picked_day.replace(day=1)
            st.rerun()
    with top_right:
        view_mode = st.radio(
            "보기",
            ["일", "주", "월"],
            horizontal=True,
            key="view_mode",
            label_visibility="collapsed",
        )

    if view_mode == "일":
        render_day_view(events, st.session_state.selected_date)
    elif view_mode == "주":
        render_week_view(events, st.session_state.selected_date)
    else:
        render_month_view(events, st.session_state.selected_date)

    st.divider()
    st.markdown("#### 일정 조회 및 변경")
    if not events:
        st.markdown("<div class='empty-note'>등록된 일정이 없습니다.</div>", unsafe_allow_html=True)
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
                    st.success("일정을 변경했습니다.")
                    st.rerun()
                if delete_clicked:
                    store.delete_event(int(event.id))
                    st.success("일정을 삭제했습니다.")
                    st.rerun()


def render_right_panel(events: list[ScheduleEvent], alerts: list[ScheduleEvent]) -> None:
    st.markdown("<p class='panel-title'>작업 공간</p>", unsafe_allow_html=True)
    search_query = st.text_input("검색", placeholder="일정 제목, 설명 검색")
    if search_query.strip():
        query = search_query.strip().lower()
        matches = [
            event
            for event in events
            if query in event.title.lower()
            or query in event.description.lower()
            or query in event.location.lower()
        ]
        st.caption(f"검색 결과 {len(matches)}개")
        for event in matches[:5]:
            st.markdown(event_card(event), unsafe_allow_html=True)

    st.divider()
    st.markdown("#### 주간 완료율")
    current_week_start = week_start(st.session_state.selected_date)
    current_week_end = current_week_start + timedelta(days=6)
    weekly_events = events_for_range(events, current_week_start, current_week_end)
    completed_events = [event for event in weekly_events if event.end_at < datetime.now()]
    completion_ratio = len(completed_events) / len(weekly_events) if weekly_events else 0
    st.progress(completion_ratio)
    st.caption(f"{len(completed_events)} / {len(weekly_events)} 일정 완료 기준")

    st.divider()
    st.markdown("#### AI 일정 입력")
    user_command = st.text_area(
        "AI 명령",
        placeholder="다음 주 화요일 오후 2시에 회의 등록해줘.",
        height=92,
    )
    if st.button("AI로 등록", type="primary", use_container_width=True):
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
                st.session_state.selected_date = saved.start_at.date()
                st.session_state.calendar_anchor = saved.start_at.date().replace(day=1)
                st.success("일정을 등록했습니다.")
                st.write(f"- 제목: {saved.title}")
                st.write(f"- 날짜: {saved.date_label}")
                st.write(f"- 시간: {saved.time_label}")
                st.caption(sync_result.message)

    with st.expander("직접 입력", expanded=False):
        with st.form("manual_event_form"):
            title = st.text_input("제목", placeholder="회의")
            start_date = st.date_input("날짜", value=st.session_state.selected_date)
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
                    st.session_state.selected_date = start_date
                    st.session_state.calendar_anchor = start_date.replace(day=1)
                    st.success("일정을 등록했습니다.")
                    st.caption(sync_result.message)
                    st.rerun()

    st.divider()
    st.markdown("#### 중요 일정 알림")
    if not alerts:
        st.markdown("<div class='empty-note'>현재 표시할 중요/임박 일정이 없습니다.</div>", unsafe_allow_html=True)
    for event in alerts[:4]:
        st.markdown(event_card(event), unsafe_allow_html=True)

    st.divider()
    st.markdown("#### 우선순위 추천")
    upcoming_events = [event for event in events if event.end_at >= datetime.now()]
    recommendations = recommend_priorities(upcoming_events)
    if not recommendations:
        st.markdown("<div class='empty-note'>추천할 일정이 없습니다.</div>", unsafe_allow_html=True)
    for item in recommendations[:4]:
        st.metric(item.event.title, f"{item.score:.2f}점", item.reason)


initialize_state()
inject_styles()

events = store.list_events(include_past=True)
alerts = store.upcoming_important()

st.markdown(
    """
    <div class="app-title">
        <div>
            <h1>AI 일정 관리</h1>
            <p class="workspace-label">Calendar-first workspace for schedule, task, and AI planning</p>
        </div>
        <p class="workspace-label">SQLite local-first · AI workspace</p>
    </div>
    """,
    unsafe_allow_html=True,
)

header_search, header_date, header_notice, header_profile = st.columns([1.5, .55, .24, .2], gap="small")
with header_search:
    st.text_input("글로벌 검색", placeholder="전체 일정 검색", label_visibility="collapsed", key="global_search")
with header_date:
    header_day = st.date_input("날짜 선택", value=st.session_state.selected_date, label_visibility="collapsed")
    if header_day != st.session_state.selected_date:
        st.session_state.selected_date = header_day
        st.session_state.calendar_anchor = header_day.replace(day=1)
        st.rerun()
with header_notice:
    st.button(f"알림 {len(alerts)}", use_container_width=True)
with header_profile:
    st.markdown("<div class='profile-dot'>HC</div>", unsafe_allow_html=True)

if st.session_state.global_search.strip():
    query = st.session_state.global_search.strip().lower()
    global_matches = [
        event
        for event in events
        if query in event.title.lower()
        or query in event.description.lower()
        or query in event.location.lower()
    ]
    st.caption(f"글로벌 검색 결과 {len(global_matches)}개")

left, center, right = st.columns([.82, 2.8, 1.0], gap="medium")

with left:
    with st.container(border=True):
        render_left_panel(events, alerts)

with center:
    with st.container(border=True):
        render_center_panel(events)

with right:
    with st.container(border=True):
        render_right_panel(events, alerts)

st.caption(
    "SQLite local-first · "
    f"DB: {settings.database_path} · "
    f"Google Calendar: {'on' if calendar_client.enabled else 'off'} · "
    f"LLM parser: {'on' if settings.llm_enabled else 'rule-based'}"
)
