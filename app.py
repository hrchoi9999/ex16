from __future__ import annotations

import calendar
import re
from datetime import date, datetime, time, timedelta
from html import escape

import streamlit as st

from personal_assistant.ai_chat import answer_schedule_question
from personal_assistant.config import settings
from personal_assistant.database import ScheduleStore
from personal_assistant.google_calendar import GoogleCalendarClient
from personal_assistant.models import ExternalScheduleCandidate, ScheduleEvent
from personal_assistant.nlp import CommandParser
from personal_assistant.priority import recommend_priorities
from personal_assistant.site_collector import collect_interest_sites


st.set_page_config(page_title="AI Scheduler", page_icon=":calendar:", layout="wide")

VIEW_TITLES = {"day": "일 보기", "week": "주 보기", "month": "월 보기"}
WEEKDAY_LABELS = ["월", "화", "수", "목", "금", "토", "일"]


@st.cache_resource
def get_store() -> ScheduleStore:
    return ScheduleStore(settings.database_path)


store = get_store()
parser = CommandParser()
calendar_client = GoogleCalendarClient()


def init_state() -> None:
    today = date.today()
    st.session_state.setdefault("selected_date", today)
    st.session_state.setdefault("view_mode", "month")
    st.session_state.setdefault("sync_message", "")
    st.session_state.setdefault("site_message", "")
    st.session_state.setdefault("chat_answer", "")
    st.session_state.setdefault("highlight_event_ids", [])
    st.session_state.setdefault("show_day_dialog", False)
    st.session_state.setdefault("last_site_collection_at", None)


def inject_styles() -> None:
    st.html(
        """
        <style>
        :root {
            --bg: #f8f9fa;
            --pane: #ffffff;
            --side: #eaf1ff;
            --line: #d6dbe8;
            --line-soft: #e8ecf4;
            --text: #0f172a;
            --muted: #596275;
            --primary: #2563eb;
            --primary-dark: #0f172a;
            --green: #16a34a;
            --amber: #b7791f;
            --red: #dc2626;
            --font: Pretendard, "Noto Sans KR", "Apple SD Gothic Neo", "Malgun Gothic", Inter, Roboto, Arial, sans-serif;
        }
        html, body, .stApp, [data-testid="stAppViewContainer"] {
            background: var(--bg) !important;
            color: var(--text) !important;
            font-family: var(--font) !important;
        }
        [data-testid="stHeader"], [data-testid="stToolbar"], [data-testid="stDecoration"],
        [data-testid="stStatusWidget"], #MainMenu, footer {
            display: none !important;
            visibility: hidden !important;
        }
        .block-container {
            padding: 0 !important;
            max-width: 100% !important;
        }
        * {
            letter-spacing: 0 !important;
            font-family: var(--font) !important;
        }
        .app-shell {
            display: grid;
            grid-template-columns: 252px minmax(620px, 1fr) 348px;
            min-height: 100vh;
            background: var(--pane);
        }
        .left-shell {
            background: var(--side);
            border-right: 1px solid var(--line);
            padding: 24px 22px;
        }
        .center-shell {
            background: var(--pane);
            border-right: 1px solid var(--line);
            min-height: 720px;
        }
        .right-shell {
            background: #f3f6fd;
            padding: 22px;
        }
        .brand {
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 24px;
        }
        .brand-icon {
            width: 42px;
            height: 42px;
            border-radius: 8px;
            background: var(--primary);
            color: white;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 900;
        }
        .brand-title {
            margin: 0;
            color: var(--primary);
            font-weight: 900;
            font-size: 1.05rem;
        }
        .brand-subtitle {
            margin: 2px 0 0;
            color: var(--muted);
            font-size: .82rem;
        }
        .section-label {
            color: var(--primary-dark);
            font-size: .72rem;
            font-weight: 900;
            text-transform: uppercase;
            margin: 22px 0 10px;
        }
        .mini-grid {
            display: grid;
            grid-template-columns: repeat(7, 1fr);
            gap: 4px;
            text-align: center;
            font-size: .73rem;
        }
        .mini-cell {
            min-height: 24px;
            border-radius: 6px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: var(--muted);
        }
        .mini-cell.today {
            background: var(--primary);
            color: #fff;
            font-weight: 900;
        }
        .mini-cell.selected {
            box-shadow: inset 0 0 0 2px var(--primary);
            color: var(--text);
            font-weight: 900;
        }
        .calendar-header {
            padding: 24px 26px 18px;
            border-bottom: 1px solid var(--line);
        }
        .calendar-title-row {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 12px;
        }
        .calendar-title {
            margin: 0;
            font-size: 1.35rem;
            font-weight: 900;
        }
        .calendar-subtitle {
            margin: 6px 0 0;
            color: var(--muted);
        }
        .pill {
            display: inline-flex;
            align-items: center;
            gap: 4px;
            padding: 4px 8px;
            border-radius: 8px;
            background: #edf2fb;
            color: var(--muted);
            font-size: .72rem;
            font-weight: 800;
        }
        .month-grid {
            display: grid;
            grid-template-columns: repeat(7, minmax(0, 1fr));
            border-top: 1px solid var(--line-soft);
            border-left: 1px solid var(--line-soft);
        }
        .month-head {
            background: #f2f5fb;
            color: var(--muted);
            font-weight: 900;
            text-align: center;
            padding: 10px;
            border-right: 1px solid var(--line-soft);
            border-bottom: 1px solid var(--line-soft);
        }
        .day-box {
            min-height: 112px;
            padding: 8px;
            border-right: 1px solid var(--line-soft);
            border-bottom: 1px solid var(--line-soft);
            background: #fff;
        }
        .day-box.outside {
            background: #f8fafc;
            opacity: .55;
        }
        .day-box.today {
            box-shadow: inset 0 0 0 2px var(--primary);
        }
        .day-box.selected {
            background: #eef5ff;
        }
        .event-pill {
            display: block;
            margin-top: 5px;
            padding: 4px 6px;
            border-radius: 6px;
            background: rgba(37,99,235,.12);
            color: var(--primary);
            font-size: .72rem;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        .event-pill.highlight {
            animation: blink-event 1s ease-in-out infinite;
            background: #fff3bf;
            color: #7a4b00;
        }
        @keyframes blink-event {
            0%, 100% { box-shadow: 0 0 0 0 rgba(245,158,11,.2); }
            50% { box-shadow: 0 0 0 4px rgba(245,158,11,.35); }
        }
        .week-grid {
            display: grid;
            grid-template-columns: 58px repeat(7, minmax(0, 1fr));
        }
        .time-cell {
            height: 54px;
            border-bottom: 1px solid var(--line-soft);
            color: var(--muted);
            font-size: .76rem;
            padding-top: 8px;
            text-align: center;
        }
        .week-col {
            position: relative;
            min-height: 756px;
            border-left: 1px solid var(--line-soft);
            background: repeating-linear-gradient(to bottom, transparent 0, transparent 53px, var(--line-soft) 54px);
        }
        .timeline-event {
            position: absolute;
            left: 6px;
            right: 6px;
            border-left: 4px solid var(--primary);
            background: rgba(37,99,235,.12);
            color: var(--primary-dark);
            border-radius: 8px;
            padding: 7px 8px;
            overflow: hidden;
            font-size: .76rem;
            font-weight: 800;
        }
        .timeline-event.highlight {
            animation: blink-event 1s ease-in-out infinite;
            background: #fff3bf;
        }
        .card {
            background: #fff;
            border: 1px solid var(--line);
            border-radius: 10px;
            padding: 14px;
            margin-bottom: 14px;
        }
        .muted {
            color: var(--muted);
            font-size: .84rem;
        }
        .bottom-shell {
            border-top: 1px solid var(--line);
            background: #fff;
            padding: 18px 24px 24px;
        }
        .small-note {
            color: var(--muted);
            font-size: .78rem;
        }
        .stButton > button {
            border-radius: 8px !important;
            font-weight: 800 !important;
        }
        .left-shell .stButton > button {
            justify-content: flex-start;
        }
        @media (max-width: 1100px) {
            .app-shell {
                grid-template-columns: 220px minmax(600px, 1fr) 320px;
                overflow-x: auto;
            }
        }
        </style>
        """
    )


def add_months(day: date, months: int) -> date:
    month_index = day.month - 1 + months
    year = day.year + month_index // 12
    month = month_index % 12 + 1
    last_day = calendar.monthrange(year, month)[1]
    return day.replace(year=year, month=month, day=min(day.day, last_day))


def week_start(day: date) -> date:
    return day - timedelta(days=day.weekday())


def period_bounds(selected: date, view_mode: str) -> tuple[datetime, datetime]:
    if view_mode == "day":
        start = selected
        end = selected + timedelta(days=1)
    elif view_mode == "week":
        start = week_start(selected)
        end = start + timedelta(days=7)
    else:
        start = selected.replace(day=1)
        end = add_months(start, 1)
    return datetime.combine(start, time.min), datetime.combine(end, time.min)


def events_for_day(events: list[ScheduleEvent], day: date) -> list[ScheduleEvent]:
    return [event for event in events if event.start_at.date() <= day <= event.end_at.date()]


def events_in_period(events: list[ScheduleEvent], start_at: datetime, end_at: datetime) -> list[ScheduleEvent]:
    return [event for event in events if start_at <= event.start_at < end_at]


def compact(text: str, limit: int = 22) -> str:
    return text[:limit] + "..." if len(text) > limit else text


def run_auto_site_collection() -> None:
    last = st.session_state.last_site_collection_at
    due = last is None or datetime.now() - last >= timedelta(hours=settings.site_collection_interval_hours)
    if not due:
        return
    result = collect_interest_sites()
    for candidate in result.candidates:
        store.upsert_candidate(candidate)
    st.session_state.last_site_collection_at = datetime.now()
    st.session_state.site_message = result.message


def import_google_events_for_current_period() -> None:
    start_at, end_at = period_bounds(st.session_state.selected_date, st.session_state.view_mode)
    result = calendar_client.list_events(start_at, end_at)
    if result.success:
        for event in result.events:
            store.upsert_google_event(event)
    st.session_state.sync_message = result.message


def create_event(event: ScheduleEvent) -> ScheduleEvent:
    sync = calendar_client.create_event(event)
    if sync.google_event_id:
        event.google_event_id = sync.google_event_id
        event.sync_status = "synced"
        event.source = "google_calendar"
    saved = store.add_event(event)
    st.session_state.sync_message = sync.message
    return saved


def update_event(event: ScheduleEvent, **updates: object) -> None:
    updated = store.update_event(int(event.id), **updates)
    if updated is None:
        return
    sync = calendar_client.update_event(updated)
    if sync.google_event_id and updated.google_event_id != sync.google_event_id:
        store.update_event(int(updated.id), google_event_id=sync.google_event_id, sync_status="synced")
    st.session_state.sync_message = sync.message


def delete_event(event: ScheduleEvent) -> None:
    sync = calendar_client.delete_event(event)
    store.delete_event(int(event.id))
    st.session_state.sync_message = sync.message


def candidate_to_event(candidate: ExternalScheduleCandidate) -> ScheduleEvent:
    start_day, end_day = parse_period(candidate.recruitment_period)
    return ScheduleEvent(
        id=None,
        title=candidate.title,
        start_at=datetime.combine(start_day, time(9, 0)),
        end_at=datetime.combine(end_day, time(18, 0)),
        description=f"{candidate.source} {candidate.category}\n모집기간: {candidate.recruitment_period}\nURL: {candidate.url}",
        location=candidate.source,
        importance=4,
        source=candidate.source,
        source_url=candidate.url,
        sync_status="local",
    )


def parse_period(period: str) -> tuple[date, date]:
    matches = re.findall(r"(20\d{2})[.년/-]\s*(\d{1,2})[.월/-]\s*(\d{1,2})", period)
    if matches:
        first = date(*map(int, matches[0]))
        last = date(*map(int, matches[-1]))
        return first, max(first, last)
    return date.today(), date.today()


def render_left(events: list[ScheduleEvent]) -> None:
    st.markdown(
        """
        <div class="brand">
            <div class="brand-icon">AI</div>
            <div>
                <p class="brand-title">AI Scheduler</p>
                <p class="brand-subtitle">개인 일정 관리 · PC Workspace</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("<p class='section-label'>Calendar View</p>", unsafe_allow_html=True)
    for view_mode, label in [("month", "월 보기"), ("week", "주 보기"), ("day", "일 보기")]:
        button_type = "primary" if st.session_state.view_mode == view_mode else "secondary"
        if st.button(label, key=f"view_{view_mode}", type=button_type, use_container_width=True):
            st.session_state.view_mode = view_mode
            st.rerun()

    st.markdown("<p class='section-label'>Google Account</p>", unsafe_allow_html=True)
    active_user = store.get_active_user()
    st.caption(active_user.email if active_user else "등록된 Google 계정 없음")
    google_email = st.text_input("Google 이메일", value=settings.google_registered_email, placeholder="name@gmail.com")
    if st.button("Google 계정 등록/연동", use_container_width=True):
        result = calendar_client.register_account()
        if result.success:
            email = google_email.strip() or result.email or "google-user"
            store.register_user(email=email, display_name=result.display_name)
            import_google_events_for_current_period()
        st.session_state.sync_message = result.message
        st.rerun()

    st.markdown("<p class='section-label'>Interest Sites</p>", unsafe_allow_html=True)
    if st.button("관심 사이트 지금 수집", use_container_width=True):
        result = collect_interest_sites()
        for candidate in result.candidates:
            store.upsert_candidate(candidate)
        st.session_state.last_site_collection_at = datetime.now()
        st.session_state.site_message = result.message
        st.rerun()
    st.caption(st.session_state.site_message or "서버 시작 후 1회, 이후 3시간마다 자동 수집합니다.")

    st.markdown("<p class='section-label'>Mini Calendar</p>", unsafe_allow_html=True)
    st.markdown(mini_calendar_html(events), unsafe_allow_html=True)


def mini_calendar_html(events: list[ScheduleEvent]) -> str:
    selected = st.session_state.selected_date
    month = selected.replace(day=1)
    event_days = {event.start_at.date() for event in events}
    parts = [f"<p style='font-weight:900;margin:0 0 8px;'>{selected:%Y년 %m월}</p>", "<div class='mini-grid'>"]
    for label in ["일", "월", "화", "수", "목", "금", "토"]:
        parts.append(f"<div class='mini-cell' style='font-weight:900'>{label}</div>")
    for week in calendar.Calendar(firstweekday=6).monthdatescalendar(month.year, month.month):
        for day in week:
            classes = ["mini-cell"]
            if day == date.today():
                classes.append("today")
            if day == selected:
                classes.append("selected")
            suffix = "•" if day in event_days else ""
            opacity = "opacity:.35;" if day.month != month.month else ""
            parts.append(f"<div class='{' '.join(classes)}' style='{opacity}'>{day.day}{suffix}</div>")
    parts.append("</div>")
    return "".join(parts)


def render_center(events: list[ScheduleEvent]) -> None:
    selected = st.session_state.selected_date
    view_mode = st.session_state.view_mode
    start_at, end_at = period_bounds(selected, view_mode)
    visible_events = events_in_period(events, start_at, end_at)

    title = f"{selected:%Y년 %m월}" if view_mode == "month" else (
        f"{week_start(selected):%Y.%m.%d} - {(week_start(selected) + timedelta(days=6)):%m.%d}"
        if view_mode == "week"
        else f"{selected:%Y년 %m월 %d일}"
    )

    prev_col, title_col, next_col = st.columns([0.12, 0.76, 0.12])
    with prev_col:
        if st.button("‹", key="calendar_prev", use_container_width=True):
            shift_current(-1)
            st.rerun()
    with title_col:
        st.markdown(
            f"""
            <div class="calendar-header" style="border-bottom:0;padding:0 0 8px;">
                <h2 class="calendar-title">{title}</h2>
                <p class="calendar-subtitle">{VIEW_TITLES[view_mode]} · 일정 {len(visible_events)}개</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with next_col:
        if st.button("›", key="calendar_next", use_container_width=True):
            shift_current(1)
            st.rerun()

    if view_mode == "month":
        render_month(events, selected)
    elif view_mode == "week":
        render_week(events, selected)
    else:
        render_day(events, selected)


def shift_current(direction: int) -> None:
    selected = st.session_state.selected_date
    view_mode = st.session_state.view_mode
    if view_mode == "month":
        st.session_state.selected_date = add_months(selected, direction)
    elif view_mode == "week":
        st.session_state.selected_date = selected + timedelta(days=7 * direction)
    else:
        st.session_state.selected_date = selected + timedelta(days=direction)


def render_month(events: list[ScheduleEvent], selected: date) -> None:
    month = selected.replace(day=1)
    st.markdown("<div class='month-grid'>", unsafe_allow_html=True)
    cols = st.columns(7, gap="small")
    for index, label in enumerate(WEEKDAY_LABELS):
        cols[index].markdown(f"<div class='month-head'>{label}</div>", unsafe_allow_html=True)
    for week in calendar.Calendar(firstweekday=0).monthdatescalendar(month.year, month.month):
        cols = st.columns(7, gap="small")
        for index, day in enumerate(week):
            day_events = events_for_day(events, day)
            label = f"{day.day}"
            if cols[index].button(label, key=f"month_day_{day.isoformat()}", use_container_width=True):
                st.session_state.selected_date = day
                st.session_state.show_day_dialog = True
                st.rerun()
            classes = ["day-box"]
            if day.month != month.month:
                classes.append("outside")
            if day == date.today():
                classes.append("today")
            if day == selected:
                classes.append("selected")
            pills = "".join(event_pill_html(event) for event in day_events[:4])
            cols[index].markdown(f"<div class='{' '.join(classes)}'>{pills}</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)


def render_week(events: list[ScheduleEvent], selected: date) -> None:
    start = week_start(selected)
    header_cols = st.columns([0.08] + [0.132] * 7)
    header_cols[0].caption("")
    for index in range(7):
        day = start + timedelta(days=index)
        if header_cols[index + 1].button(f"{WEEKDAY_LABELS[index]} {day.day}", key=f"week_day_{day.isoformat()}", use_container_width=True):
            st.session_state.selected_date = day
            st.session_state.show_day_dialog = True
            st.rerun()

    grid_parts = ["<div class='week-grid'><div>"]
    for hour in range(7, 21):
        grid_parts.append(f"<div class='time-cell'>{hour:02d}:00</div>")
    grid_parts.append("</div>")
    for index in range(7):
        day = start + timedelta(days=index)
        body = "".join(timeline_event_html(event) for event in events_for_day(events, day))
        grid_parts.append(f"<div class='week-col'>{body}</div>")
    grid_parts.append("</div>")
    st.markdown("".join(grid_parts), unsafe_allow_html=True)


def render_day(events: list[ScheduleEvent], selected: date) -> None:
    day_events = events_for_day(events, selected)
    grid_parts = ["<div class='week-grid' style='grid-template-columns:58px minmax(0,1fr);'><div>"]
    for hour in range(7, 21):
        grid_parts.append(f"<div class='time-cell'>{hour:02d}:00</div>")
    grid_parts.append("</div>")
    grid_parts.append("<div class='week-col'>")
    grid_parts.extend(timeline_event_html(event) for event in day_events)
    grid_parts.append("</div></div>")
    st.markdown("".join(grid_parts), unsafe_allow_html=True)


def event_pill_html(event: ScheduleEvent) -> str:
    highlight = " highlight" if event.id in st.session_state.highlight_event_ids else ""
    return f"<span class='event-pill{highlight}'>{escape(compact(event.title))}</span>"


def timeline_event_html(event: ScheduleEvent) -> str:
    start_hour = max(event.start_at.hour + event.start_at.minute / 60, 7)
    end_hour = max(event.end_at.hour + event.end_at.minute / 60, start_hour + 1)
    top = int((start_hour - 7) * 54)
    height = max(int((end_hour - start_hour) * 54), 42)
    highlight = " highlight" if event.id in st.session_state.highlight_event_ids else ""
    return (
        f"<div class='timeline-event{highlight}' style='top:{top}px;height:{height}px;'>"
        f"{escape(event.time_label)}<br>{escape(compact(event.title, 34))}</div>"
    )


def render_right(events: list[ScheduleEvent]) -> None:
    st.markdown("### 작업 메뉴")
    render_event_editor(events)
    render_google_tools()
    render_candidates()
    render_recommendations(events)


def render_event_editor(events: list[ScheduleEvent], prefix: str = "main") -> None:
    selected = st.session_state.selected_date
    day_events = events_for_day(events, selected)
    with st.expander(f"{selected:%Y-%m-%d} 일정/작업 입력", expanded=True):
        title = st.text_input("제목", key=f"{prefix}_manual_title")
        start_time = st.time_input("시작 시간", value=time(9, 0), key=f"{prefix}_manual_time")
        duration = st.number_input("소요 시간(분)", 15, 720, 60, 15, key=f"{prefix}_manual_duration")
        importance = st.slider("중요도", 1, 5, 3, key=f"{prefix}_manual_importance")
        description = st.text_area("설명", key=f"{prefix}_manual_description", height=80)
        if st.button("일정 등록", type="primary", use_container_width=True, key=f"{prefix}_manual_submit"):
            if not title.strip():
                st.warning("제목을 입력해 주세요.")
            else:
                start_at = datetime.combine(selected, start_time)
                create_event(
                    ScheduleEvent(
                        id=None,
                        title=title.strip(),
                        start_at=start_at,
                        end_at=start_at + timedelta(minutes=int(duration)),
                        description=description.strip(),
                        importance=int(importance),
                    )
                )
                st.rerun()

    with st.expander("AI 일정 등록", expanded=False):
        command = st.text_area("AI 명령", placeholder="다음 주 화요일 오후 2시에 회의 등록해줘.", height=80, key=f"{prefix}_ai_command")
        if st.button("AI 명령으로 등록", type="primary", use_container_width=True, key=f"{prefix}_ai_submit"):
            parsed = parser.parse(command)
            if parsed.event is None:
                st.info(parsed.message)
            else:
                create_event(parsed.event)
                st.success("일정을 등록했습니다.")
                st.rerun()

    with st.expander("선택 날짜 일정 수정/삭제", expanded=bool(day_events)):
        if not day_events:
            st.caption("선택된 날짜에 등록된 일정이 없습니다.")
        for event in day_events:
            with st.form(f"{prefix}_edit_event_{event.id}"):
                st.markdown(f"**{event.title}**")
                updated_title = st.text_input("제목", value=event.title, key=f"{prefix}_title_{event.id}")
                updated_time = st.time_input("시작 시간", value=event.start_at.time(), key=f"{prefix}_time_{event.id}")
                updated_minutes = max(int((event.end_at - event.start_at).total_seconds() // 60), 15)
                updated_duration = st.number_input("소요 시간(분)", 15, 720, updated_minutes, 15, key=f"{prefix}_duration_{event.id}")
                updated_importance = st.slider("중요도", 1, 5, event.importance, key=f"{prefix}_importance_{event.id}")
                updated_description = st.text_area("설명", value=event.description, key=f"{prefix}_description_{event.id}", height=70)
                save_col, delete_col = st.columns(2)
                save = save_col.form_submit_button("수정 저장", use_container_width=True)
                remove = delete_col.form_submit_button("삭제", use_container_width=True)
                if save:
                    start_at = datetime.combine(st.session_state.selected_date, updated_time)
                    update_event(
                        event,
                        title=updated_title.strip(),
                        start_at=start_at,
                        end_at=start_at + timedelta(minutes=int(updated_duration)),
                        description=updated_description.strip(),
                        importance=int(updated_importance),
                    )
                    st.rerun()
                if remove:
                    delete_event(event)
                    st.rerun()


def render_google_tools() -> None:
    with st.expander("Google Calendar 연동", expanded=False):
        active_user = store.get_active_user()
        st.caption(f"등록 계정: {active_user.email}" if active_user else "Google 계정을 먼저 등록하세요.")
        if st.button("현재 보기 범위 가져오기", use_container_width=True):
            import_google_events_for_current_period()
            st.rerun()
        if st.session_state.sync_message:
            st.info(st.session_state.sync_message)


def render_candidates() -> None:
    with st.expander("관심 사이트 수집 후보", expanded=False):
        candidates = store.list_candidates()
        if not candidates:
            st.caption("수집된 모집중 공고가 없습니다. 좌측에서 관심 사이트 수집을 실행하세요.")
        for candidate in candidates[:20]:
            st.markdown(f"**{candidate.title}**")
            st.caption(f"{candidate.source} · {candidate.category} · {candidate.recruitment_period}")
            st.link_button("원문 열기", candidate.url, use_container_width=True)
            if st.button("이 공고를 일정에 등록", key=f"candidate_{candidate.id}", use_container_width=True):
                event = candidate_to_event(candidate)
                create_event(event)
                store.mark_candidate_selected(int(candidate.id))
                st.success("선택한 공고를 일정에 등록했습니다.")
                st.rerun()


def render_recommendations(events: list[ScheduleEvent]) -> None:
    with st.expander("우선순위 추천", expanded=False):
        recommendations = recommend_priorities([event for event in events if event.end_at >= datetime.now()])
        if not recommendations:
            st.caption("추천할 예정 일정이 없습니다.")
        for item in recommendations[:5]:
            st.markdown(f"**{item.event.title}**")
            st.caption(f"{item.reason} · 점수 {item.score}")


def render_bottom(events: list[ScheduleEvent]) -> None:
    selected = st.session_state.selected_date
    day_events = events_for_day(events, selected)
    detail_col, chat_col = st.columns([1.05, 1], gap="large")
    with detail_col:
        st.markdown(f"#### {selected:%Y-%m-%d} 상세")
        if not day_events:
            st.caption("선택된 날짜에 일정이 없습니다.")
        for event in day_events:
            st.markdown(f"**{event.time_label} · {event.title}**")
            st.caption(f"중요도 {event.importance} · 출처 {event.source} · {event.description or '설명 없음'}")
    with chat_col:
        st.markdown("#### AI 일정 채팅")
        question = st.text_input("질문", placeholder="이번 주 면접 일정 알려줘")
        if st.button("AI에게 질문", type="primary", use_container_width=True):
            result = answer_schedule_question(question, events)
            st.session_state.chat_answer = result.answer
            st.session_state.highlight_event_ids = result.matched_event_ids
            st.rerun()
        if st.session_state.chat_answer:
            st.info(st.session_state.chat_answer)


@st.dialog("일정/작업 편집")
def day_editor_dialog(events: list[ScheduleEvent]) -> None:
    st.markdown(f"### {st.session_state.selected_date:%Y-%m-%d}")
    render_event_editor(events, prefix="dialog")
    if st.button("닫기", use_container_width=True):
        st.session_state.show_day_dialog = False
        st.rerun()


def main() -> None:
    init_state()
    inject_styles()
    run_auto_site_collection()

    all_events = store.list_events(include_past=True)

    left, center, right = st.columns([0.18, 0.57, 0.25], gap="large")
    with left:
        st.markdown("<div class='left-shell'>", unsafe_allow_html=True)
        render_left(all_events)
        st.markdown("</div>", unsafe_allow_html=True)
    with center:
        st.markdown("<div class='center-shell'>", unsafe_allow_html=True)
        render_center(all_events)
        st.markdown("<div class='bottom-shell'>", unsafe_allow_html=True)
        render_bottom(all_events)
        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    with right:
        st.markdown("<div class='right-shell'>", unsafe_allow_html=True)
        render_right(all_events)
        st.markdown("</div>", unsafe_allow_html=True)

    if st.session_state.show_day_dialog:
        day_editor_dialog(all_events)

    st.caption(
        "SQLite local-first · "
        f"DB: {settings.database_path} · "
        f"Google Calendar API: {'on' if calendar_client.enabled else 'off'} · "
        f"Gemini/OpenAI: {'on' if settings.llm_enabled else 'rule-based'}"
    )


if __name__ == "__main__":
    main()
