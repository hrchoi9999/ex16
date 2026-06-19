from __future__ import annotations

import calendar
import re
from datetime import date, datetime, time, timedelta
from html import escape

import streamlit as st
import streamlit.components.v1 as components

from personal_assistant.ai_chat import answer_schedule_question
from personal_assistant.config import settings
from personal_assistant.database import ScheduleStore
from personal_assistant.google_calendar import GoogleCalendarClient
from personal_assistant.models import ExternalScheduleCandidate, ScheduleEvent
from personal_assistant.nlp import CommandParser
from personal_assistant.priority import recommend_priorities
from personal_assistant.site_collector import REQUESTED_SITE_SOURCES, collect_interest_sites


st.set_page_config(page_title="AI Scheduler", page_icon=":calendar:", layout="wide")

VIEW_TITLES = {"day": "일 보기", "week": "주 보기", "month": "월 보기"}
WEEKDAY_LABELS = ["월", "화", "수", "목", "금", "토", "일"]
RIGHT_MENUS = ["상세 정보", "일정 편집", "AI 일정", "Google 연동", "관심 사이트", "우선순위"]


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
    st.session_state.setdefault("right_menu", "상세 정보")
    st.session_state.setdefault("sync_message", "")
    st.session_state.setdefault("site_message", "")
    st.session_state.setdefault("chat_history", [])
    st.session_state.setdefault("highlight_event_ids", [])
    st.session_state.setdefault("show_day_dialog", False)
    st.session_state.setdefault("last_site_collection_at", None)
    st.session_state.setdefault("google_auth_url", "")
    st.session_state.setdefault("google_auth_state", "")

    query_view = st.query_params.get("view")
    query_date = st.query_params.get("date")
    query_dialog = st.query_params.get("dialog")
    if query_view in VIEW_TITLES:
        st.session_state.view_mode = query_view
    if query_date:
        try:
            st.session_state.selected_date = date.fromisoformat(query_date)
        except ValueError:
            pass
    if query_dialog == "1":
        st.session_state.show_day_dialog = True
        st.session_state.right_menu = "일정 편집"


def handle_google_oauth_callback() -> None:
    error = st.query_params.get("error")
    code = st.query_params.get("code")
    state = st.query_params.get("state") or st.session_state.google_auth_state
    if error:
        st.session_state.sync_message = f"Google 로그인이 취소되었거나 실패했습니다. {error}"
        st.session_state.right_menu = "Google 연동"
        st.query_params.clear()
        st.rerun()
    if not code:
        return

    result = calendar_client.finish_oauth(code=code, state=state)
    if result.success:
        store.register_user(email=result.email or "google-user", display_name=result.display_name)
        st.session_state.google_auth_url = ""
        st.session_state.google_auth_state = ""
        import_google_events_for_current_period()
    st.session_state.sync_message = result.message
    st.session_state.right_menu = "Google 연동"
    st.query_params.clear()
    st.rerun()


def inject_styles() -> None:
    st.html(
        """
        <style>
        :root {
            --bg: #f8f9fa;
            --pane: #ffffff;
            --side: #eaf1ff;
            --right: #f3f6fd;
            --line: #d6dbe8;
            --line-soft: #e8ecf4;
            --text: #0f172a;
            --muted: #596275;
            --primary: #2563eb;
            --primary-soft: rgba(37,99,235,.12);
            --amber-soft: #fff3bf;
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
            max-width: none !important;
            width: 100vw !important;
            min-width: 1320px !important;
        }
        [data-testid="stAppViewContainer"], [data-testid="stMain"] {
            overflow-x: auto !important;
        }
        [data-testid="stMain"] {
            justify-content: flex-start !important;
            align-items: stretch !important;
        }
        [data-testid="stHorizontalBlock"]:has(.layout-anchor) {
            display: flex !important;
            flex-direction: row !important;
            flex-wrap: nowrap !important;
            gap: 0 !important;
            align-items: stretch !important;
            width: 100% !important;
            min-width: 1320px !important;
        }
        [data-testid="stHorizontalBlock"]:has(.layout-anchor) > [data-testid="stColumn"]:nth-child(1) {
            flex: 0 0 auto !important;
            width: 260px !important;
            min-width: 260px !important;
            max-width: 420px !important;
            box-sizing: border-box !important;
            background: var(--side) !important;
            border-right: 1px solid var(--line) !important;
            padding: 24px 22px !important;
            resize: horizontal !important;
            overflow: auto !important;
            position: relative !important;
        }
        [data-testid="stHorizontalBlock"]:has(.layout-anchor) > [data-testid="stColumn"]:nth-child(2) {
            flex: 1 1 auto !important;
            width: auto !important;
            min-width: 640px !important;
            box-sizing: border-box !important;
            background: var(--pane) !important;
            border-right: 1px solid var(--line) !important;
            resize: horizontal !important;
            overflow: auto !important;
            position: relative !important;
        }
        [data-testid="stHorizontalBlock"]:has(.layout-anchor) > [data-testid="stColumn"]:nth-child(3) {
            flex: 0 0 auto !important;
            width: 500px !important;
            min-width: 390px !important;
            max-width: 680px !important;
            box-sizing: border-box !important;
            background: var(--right) !important;
            padding: 18px 20px !important;
            resize: horizontal !important;
            overflow: auto !important;
            position: relative !important;
        }
        [data-testid="stHorizontalBlock"]:has(.layout-anchor) > [data-testid="stColumn"]:nth-child(1)::after,
        [data-testid="stHorizontalBlock"]:has(.layout-anchor) > [data-testid="stColumn"]:nth-child(2)::after {
            content: "";
            position: absolute;
            top: 0;
            right: -3px;
            width: 6px;
            height: 100%;
            cursor: ew-resize;
            background: transparent;
            z-index: 20;
        }
        [data-testid="stHorizontalBlock"]:has(.layout-anchor) > [data-testid="stColumn"]:nth-child(1):hover::after,
        [data-testid="stHorizontalBlock"]:has(.layout-anchor) > [data-testid="stColumn"]:nth-child(2):hover::after {
            background: rgba(37, 99, 235, .10);
        }
        * {
            letter-spacing: 0 !important;
            font-family: var(--font) !important;
        }
        .layout-anchor {
            display: none;
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
            color: #fff;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 900;
        }
        .brand-title {
            margin: 0;
            color: var(--primary);
            font-size: 1.05rem;
            font-weight: 900;
        }
        .brand-subtitle {
            margin: 2px 0 0;
            color: var(--muted);
            font-size: .82rem;
        }
        .section-label {
            color: var(--text);
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
        .calendar-nav {
            display: grid;
            grid-template-columns: 46px minmax(0, 1fr) 46px;
            gap: 12px;
            align-items: center;
            padding: 22px 24px 14px;
        }
        .calendar-title {
            margin: 0;
            font-size: 1.22rem;
            font-weight: 760;
        }
        .calendar-subtitle {
            margin: 6px 0 0;
            color: var(--muted);
            font-size: .9rem;
        }
        .nav-square {
            display: flex;
            height: 38px;
            align-items: center;
            justify-content: center;
            border: 1px solid var(--line);
            border-radius: 8px;
            color: var(--text) !important;
            text-decoration: none !important;
            background: #fff;
            font-size: 1.35rem;
            font-weight: 900;
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
            font-size: .82rem;
            font-weight: 560;
            text-align: center;
            padding: 10px;
            border-right: 1px solid var(--line-soft);
            border-bottom: 1px solid var(--line-soft);
        }
        .day-link {
            display: block;
            min-height: 112px;
            padding: 8px;
            border-right: 1px solid var(--line-soft);
            border-bottom: 1px solid var(--line-soft);
            background: #fff;
            color: var(--text) !important;
            text-decoration: none !important;
            overflow: hidden;
            font-size: .86rem;
        }
        .day-link:hover, .day-link.selected {
            background: #eef5ff;
        }
        .day-link.outside {
            background: #f8fafc;
            opacity: .58;
        }
        .day-link.today {
            box-shadow: inset 0 0 0 2px var(--primary);
        }
        .day-number-text {
            display: block;
            font-size: .82rem;
            font-weight: 520;
            margin-bottom: 6px;
        }
        .event-pill {
            display: block;
            margin-top: 5px;
            padding: 4px 6px;
            border-radius: 6px;
            background: var(--primary-soft);
            color: var(--primary);
            font-size: .66rem;
            font-weight: 500;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        .event-pill.highlight {
            animation: blink-event 1s ease-in-out infinite;
            background: var(--amber-soft);
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
        .week-head-link {
            display: block;
            padding: 10px 8px;
            text-align: center;
            color: var(--text) !important;
            text-decoration: none !important;
            font-weight: 900;
            background: #f2f5fb;
            border-left: 1px solid var(--line-soft);
            border-bottom: 1px solid var(--line-soft);
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
            background: var(--primary-soft);
            color: var(--text);
            border-radius: 8px;
            padding: 7px 8px;
            overflow: hidden;
            font-size: .76rem;
            font-weight: 800;
        }
        .timeline-event.highlight {
            animation: blink-event 1s ease-in-out infinite;
            background: var(--amber-soft);
        }
        .right-title {
            margin: 0 0 12px;
            font-size: 1.35rem;
            font-weight: 900;
        }
        .right-content {
            height: 560px;
            overflow-y: auto;
            padding: 14px;
            border: 1px solid var(--line);
            border-radius: 10px;
            background: #fff;
        }
        .right-chat {
            margin-top: 14px;
            padding: 12px;
            border: 1px solid var(--line);
            border-radius: 10px;
            background: #fff;
        }
        .right-chat-title {
            margin: 0 0 8px;
            font-weight: 900;
            font-size: .92rem;
        }
        .info-card {
            border: 1px solid var(--line-soft);
            border-radius: 10px;
            padding: 12px;
            margin-bottom: 10px;
            background: #fff;
        }
        .info-card-title {
            margin: 0 0 6px;
            font-weight: 900;
        }
        .muted {
            color: var(--muted);
            font-size: .84rem;
        }
        .small-note {
            color: var(--muted);
            font-size: .78rem;
        }
        .stButton > button {
            border-radius: 8px !important;
            font-weight: 800 !important;
        }
        div[role="radiogroup"] {
            gap: .35rem !important;
        }
        div[role="radiogroup"] label {
            min-height: 2.25rem !important;
            padding: .25rem .45rem !important;
            border: 1px solid var(--line) !important;
            border-radius: 8px !important;
            background: #fff !important;
        }
        [data-testid="stDialog"] [data-testid="stVerticalBlock"] {
            gap: .7rem !important;
        }
        [data-testid="stDialog"] h1,
        [data-testid="stDialog"] h2,
        [data-testid="stDialog"] h3 {
            line-height: 1.25 !important;
        }
        @media (max-width: 1100px) {
            .block-container {
                min-width: 1320px !important;
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


def calendar_href(target_date: date, view_mode: str, dialog: bool = False) -> str:
    suffix = "&dialog=1" if dialog else ""
    return f"?view={view_mode}&date={target_date.isoformat()}{suffix}"


def shifted_date(selected: date, view_mode: str, direction: int) -> date:
    if view_mode == "month":
        return add_months(selected, direction)
    if view_mode == "week":
        return selected + timedelta(days=7 * direction)
    return selected + timedelta(days=direction)


def run_auto_site_collection() -> None:
    last = st.session_state.last_site_collection_at
    due = last is None or datetime.now() - last >= timedelta(hours=settings.site_collection_interval_hours)
    if not due:
        return
    result = collect_interest_sites()
    if result.success:
        store.delete_candidates_by_sources(REQUESTED_SITE_SOURCES)
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


def parse_period(period: str) -> tuple[date, date]:
    matches = re.findall(r"(20\d{2})[.년/-]\s*(\d{1,2})[.월/-]\s*(\d{1,2})", period)
    if matches:
        first = date(*map(int, matches[0]))
        last = date(*map(int, matches[-1]))
        return first, max(first, last)
    return date.today(), date.today()


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


def render_left(events: list[ScheduleEvent]) -> None:
    st.html('<span class="layout-anchor"></span>')
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
            st.query_params.clear()
            st.rerun()

    st.markdown("<p class='section-label'>Google Account</p>", unsafe_allow_html=True)
    active_user = store.get_active_user()
    st.caption(active_user.email if active_user else "Google 로그인으로 캘린더를 연결하세요.")
    google_email = st.text_input("표시 이메일", value=settings.google_registered_email, placeholder="name@gmail.com")
    if calendar_client.enabled and not st.session_state.google_auth_url:
        result = calendar_client.start_oauth(login_hint=google_email.strip())
        if result.success:
            st.session_state.google_auth_url = result.authorization_url
            st.session_state.google_auth_state = result.state
    if st.button("Google 로그인 링크 새로 만들기", use_container_width=True):
        result = calendar_client.start_oauth(login_hint=google_email.strip())
        if result.success:
            st.session_state.google_auth_url = result.authorization_url
            st.session_state.google_auth_state = result.state
        st.session_state.sync_message = result.message
        st.session_state.right_menu = "Google 연동"
        st.rerun()
    if st.session_state.google_auth_url:
        st.link_button("Google 로그인 화면 열기", st.session_state.google_auth_url, use_container_width=True)

    st.markdown("<p class='section-label'>Interest Sites</p>", unsafe_allow_html=True)
    if st.button("관심 사이트 지금 수집", use_container_width=True):
        result = collect_interest_sites()
        if result.success:
            store.delete_candidates_by_sources(REQUESTED_SITE_SOURCES)
        for candidate in result.candidates:
            store.upsert_candidate(candidate)
        st.session_state.last_site_collection_at = datetime.now()
        st.session_state.site_message = result.message
        st.session_state.right_menu = "관심 사이트"
        st.rerun()
    st.caption(st.session_state.site_message or "서버 시작 후 1회, 이후 3시간마다 자동 수집합니다.")

    st.markdown("<p class='section-label'>Mini Calendar</p>", unsafe_allow_html=True)
    st.markdown(mini_calendar_html(events), unsafe_allow_html=True)


def inject_resizer_component() -> None:
    components.html(
        """
        <script>
        (() => {
          const doc = window.parent.document;
          const storage = window.parent.localStorage;
          const clamp = (value, min, max) => Math.max(min, Math.min(max, value));

          function findLayout() {
            return [...doc.querySelectorAll('[data-testid="stHorizontalBlock"]')]
              .find((block) => block.querySelector('.layout-anchor'));
          }

          function setup() {
            const block = findLayout();
            if (!block || block.dataset.aiSchedulerResizable === '1') return;
            const cols = [...block.querySelectorAll(':scope > [data-testid="stColumn"]')];
            if (cols.length < 3) return;

            block.dataset.aiSchedulerResizable = '1';
            block.style.position = 'relative';

            let leftWidth = Number(storage.getItem('aiScheduler.leftWidth') || 260);
            let rightWidth = Number(storage.getItem('aiScheduler.rightWidth') || 500);

            const leftHandle = doc.createElement('div');
            const rightHandle = doc.createElement('div');
            leftHandle.className = 'ai-scheduler-resizer ai-scheduler-resizer-left';
            rightHandle.className = 'ai-scheduler-resizer ai-scheduler-resizer-right';
            block.append(leftHandle, rightHandle);

            const style = doc.createElement('style');
            style.textContent = `
              .ai-scheduler-resizer {
                position: absolute;
                top: 0;
                width: 10px;
                height: 100%;
                z-index: 9999;
                cursor: ew-resize;
                background: transparent;
                transform: translateX(-5px);
              }
              .ai-scheduler-resizer:hover,
              .ai-scheduler-resizer.dragging {
                background: rgba(37, 99, 235, .16);
              }
            `;
            doc.head.appendChild(style);

            function apply() {
              leftWidth = clamp(leftWidth, 220, 420);
              rightWidth = clamp(rightWidth, 360, 720);
              cols[0].style.setProperty('flex', `0 0 ${leftWidth}px`, 'important');
              cols[0].style.setProperty('width', `${leftWidth}px`, 'important');
              cols[1].style.setProperty('flex', '1 1 auto', 'important');
              cols[1].style.setProperty('min-width', '520px', 'important');
              cols[2].style.setProperty('flex', `0 0 ${rightWidth}px`, 'important');
              cols[2].style.setProperty('width', `${rightWidth}px`, 'important');
              positionHandles();
              storage.setItem('aiScheduler.leftWidth', String(leftWidth));
              storage.setItem('aiScheduler.rightWidth', String(rightWidth));
            }

            function positionHandles() {
              const blockRect = block.getBoundingClientRect();
              const leftRect = cols[1].getBoundingClientRect();
              const rightRect = cols[2].getBoundingClientRect();
              leftHandle.style.left = `${leftRect.left - blockRect.left}px`;
              rightHandle.style.left = `${rightRect.left - blockRect.left}px`;
              rightHandle.style.right = '';
            }

            function totalColumnWidth() {
              return cols.reduce((sum, col) => sum + col.getBoundingClientRect().width, 0);
            }

            function drag(handle, side) {
              handle.addEventListener('pointerdown', (event) => {
                event.preventDefault();
                handle.classList.add('dragging');
                const rect = block.getBoundingClientRect();
                const totalWidth = totalColumnWidth();
                const move = (moveEvent) => {
                  if (side === 'left') {
                    leftWidth = moveEvent.clientX - rect.left;
                  } else {
                    rightWidth = totalWidth - (moveEvent.clientX - rect.left);
                  }
                  apply();
                };
                const up = () => {
                  handle.classList.remove('dragging');
                  doc.removeEventListener('pointermove', move);
                  doc.removeEventListener('pointerup', up);
                };
                doc.addEventListener('pointermove', move);
                doc.addEventListener('pointerup', up);
              });
            }

            drag(leftHandle, 'left');
            drag(rightHandle, 'right');
            apply();
          }

          setup();
          const observer = new MutationObserver(setup);
          observer.observe(doc.body, { childList: true, subtree: true });
          setTimeout(setup, 500);
          setTimeout(setup, 1500);
        })();
        </script>
        """,
        height=0,
        width=0,
    )


def render_center(events: list[ScheduleEvent]) -> None:
    selected = st.session_state.selected_date
    view_mode = st.session_state.view_mode
    start_at, end_at = period_bounds(selected, view_mode)
    visible_events = events_in_period(events, start_at, end_at)
    title = (
        f"{selected:%Y년 %m월}"
        if view_mode == "month"
        else (
            f"{week_start(selected):%Y.%m.%d} - {(week_start(selected) + timedelta(days=6)):%m.%d}"
            if view_mode == "week"
            else f"{selected:%Y년 %m월 %d일}"
        )
    )
    previous_date = shifted_date(selected, view_mode, -1)
    next_date = shifted_date(selected, view_mode, 1)
    st.markdown(
        f"""
        <div class="calendar-nav">
            <a class="nav-square" href="{calendar_href(previous_date, view_mode)}">‹</a>
            <div>
                <h2 class="calendar-title">{escape(title)}</h2>
                <p class="calendar-subtitle">{VIEW_TITLES[view_mode]} · 일정 {len(visible_events)}개</p>
            </div>
            <a class="nav-square" href="{calendar_href(next_date, view_mode)}">›</a>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if view_mode == "month":
        render_month(events, selected)
    elif view_mode == "week":
        render_week(events, selected)
    else:
        render_day(events, selected)


def render_month(events: list[ScheduleEvent], selected: date) -> None:
    month = selected.replace(day=1)
    parts = ["<div class='month-grid'>"]
    for label in WEEKDAY_LABELS:
        parts.append(f"<div class='month-head'>{label}</div>")
    for week in calendar.Calendar(firstweekday=0).monthdatescalendar(month.year, month.month):
        for day in week:
            day_events = events_for_day(events, day)
            classes = ["day-link"]
            if day.month != month.month:
                classes.append("outside")
            if day == date.today():
                classes.append("today")
            if day == selected:
                classes.append("selected")
            pills = "".join(event_pill_html(event) for event in day_events[:4])
            parts.append(
                f"<a class=\"{' '.join(classes)}\" href=\"{calendar_href(day, 'month', dialog=True)}\">"
                f"<span class=\"day-number-text\">{day.day}</span>{pills}</a>"
            )
    parts.append("</div>")
    st.html("".join(parts))


def render_week(events: list[ScheduleEvent], selected: date) -> None:
    start = week_start(selected)
    head_parts = ["<div class='week-grid'><div class='week-head-link' style='background:#fff;border-left:0;'></div>"]
    for index in range(7):
        day = start + timedelta(days=index)
        head_parts.append(
            f'<a class="week-head-link" href="{calendar_href(day, "week", dialog=True)}">{WEEKDAY_LABELS[index]} {day.day}</a>'
        )
    head_parts.append("</div>")
    st.html("".join(head_parts))

    grid_parts = ["<div class='week-grid'><div>"]
    for hour in range(7, 21):
        grid_parts.append(f"<div class='time-cell'>{hour:02d}:00</div>")
    grid_parts.append("</div>")
    for index in range(7):
        day = start + timedelta(days=index)
        body = "".join(timeline_event_html(event) for event in events_for_day(events, day))
        grid_parts.append(f"<div class='week-col'>{body}</div>")
    grid_parts.append("</div>")
    st.html("".join(grid_parts))


def render_day(events: list[ScheduleEvent], selected: date) -> None:
    day_events = events_for_day(events, selected)
    grid_parts = ["<div class='week-grid' style='grid-template-columns:58px minmax(0,1fr);'><div>"]
    for hour in range(7, 21):
        grid_parts.append(f"<div class='time-cell'>{hour:02d}:00</div>")
    grid_parts.append("</div><div class='week-col'>")
    grid_parts.extend(timeline_event_html(event) for event in day_events)
    grid_parts.append("</div></div>")
    st.html("".join(grid_parts))


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
    st.markdown("<h2 class='right-title'>작업 메뉴</h2>", unsafe_allow_html=True)
    menu = st.radio(
        "메뉴 선택",
        RIGHT_MENUS,
        index=RIGHT_MENUS.index(st.session_state.right_menu),
        horizontal=True,
        label_visibility="collapsed",
        key="right_menu_radio",
    )
    st.session_state.right_menu = menu
    with st.container(height=560, border=True):
        render_right_content(events, menu)
    render_ai_chat_input(events)


def render_right_content(events: list[ScheduleEvent], menu: str) -> None:
    if menu == "상세 정보":
        render_selected_detail(events)
        render_chat_history()
    elif menu == "일정 편집":
        render_event_editor(events)
    elif menu == "AI 일정":
        render_ai_event_creator()
        render_chat_history()
    elif menu == "Google 연동":
        render_google_tools()
    elif menu == "관심 사이트":
        render_candidates()
    elif menu == "우선순위":
        render_recommendations(events)


def render_selected_detail(events: list[ScheduleEvent]) -> None:
    selected = st.session_state.selected_date
    day_events = events_for_day(events, selected)
    st.markdown(f"### {selected:%Y-%m-%d} 상세")
    if not day_events:
        st.caption("선택된 날짜에 일정이 없습니다.")
        return
    for event in day_events:
        st.markdown(
            f"""
            <div class="info-card">
                <p class="info-card-title">{escape(event.time_label)} · {escape(event.title)}</p>
                <p class="muted">중요도 {event.importance} · 출처 {escape(event.source)}</p>
                <p class="muted">{escape(event.description or '설명 없음')}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_chat_history() -> None:
    if not st.session_state.chat_history:
        st.caption("AI 채팅 대화가 아직 없습니다.")
        return
    st.markdown("### AI 채팅 기록")
    for item in st.session_state.chat_history[-8:]:
        st.markdown(f"**사용자**: {item['question']}")
        st.info(item["answer"])


def render_event_editor(events: list[ScheduleEvent], prefix: str = "main") -> None:
    selected = st.session_state.selected_date
    day_events = events_for_day(events, selected)
    st.markdown(f"### {selected:%Y-%m-%d} 일정/작업 입력")
    with st.form(f"{prefix}_create_form", clear_on_submit=True):
        title = st.text_input("제목", key=f"{prefix}_manual_title")
        start_time = st.time_input("시작 시간", value=time(9, 0), key=f"{prefix}_manual_time")
        duration = st.number_input("소요 시간(분)", 15, 720, 60, 15, key=f"{prefix}_manual_duration")
        importance = st.slider("중요도", 1, 5, 3, key=f"{prefix}_manual_importance")
        description = st.text_area("설명", key=f"{prefix}_manual_description", height=80)
        submitted = st.form_submit_button("일정 등록", type="primary", use_container_width=True)
        if submitted:
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

    st.markdown("### 선택 날짜 일정 수정/삭제")
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


def render_ai_event_creator() -> None:
    st.markdown("### AI 일정 등록")
    command = st.text_area("AI 명령", placeholder="다음 주 화요일 오후 2시에 회의 등록해줘.", height=90)
    if st.button("AI 명령으로 등록", type="primary", use_container_width=True):
        parsed = parser.parse(command)
        if parsed.event is None:
            st.info(parsed.message)
        else:
            create_event(parsed.event)
            st.success("일정을 등록했습니다.")
            st.rerun()


def render_google_tools() -> None:
    st.markdown("### Google Calendar 연동")
    active_user = store.get_active_user()
    st.caption(f"연결 계정: {active_user.email}" if active_user else "좌측의 Google 로그인 열기로 계정을 연결하세요.")
    if not calendar_client.enabled:
        st.warning(
            "Gmail 로그인 연동은 가능합니다. 다만 현재 앱에 Google OAuth 클라이언트 설정이 없어 로그인 URL을 만들 수 없습니다. "
            "운영자가 Google Cloud에서 Calendar API를 켜고 OAuth 클라이언트 ID/Secret 및 redirect URI를 설정해야 합니다."
        )
        render_google_admin_setup()
    else:
        if st.button("Google 로그인 URL 생성", use_container_width=True):
            result = calendar_client.start_oauth(settings.google_registered_email)
            if result.success:
                st.session_state.google_auth_url = result.authorization_url
                st.session_state.google_auth_state = result.state
            st.session_state.sync_message = result.message
            st.rerun()
        if st.session_state.google_auth_url:
            st.link_button("Google 로그인 화면 열기", st.session_state.google_auth_url, use_container_width=True)
    if st.button("현재 보기 범위 가져오기", use_container_width=True):
        import_google_events_for_current_period()
        st.rerun()
    if st.session_state.sync_message:
        st.info(st.session_state.sync_message)


def render_google_admin_setup() -> None:
    st.markdown("#### 관리자 설정 순서")
    st.markdown(
        """
1. Google Cloud Console에서 새 프로젝트를 만들거나 기존 프로젝트를 선택합니다.
2. API Library에서 **Google Calendar API**를 검색해 활성화합니다.
3. OAuth consent screen에서 앱 이름, 관리자 이메일, 테스트 사용자 Gmail을 등록합니다.
4. Credentials에서 **OAuth Client ID**를 만들고 유형은 **Web application**으로 선택합니다.
5. Authorized redirect URI에 `http://localhost:8501/`를 추가합니다.
6. 발급된 Client ID와 Client Secret을 `C:\\AI_Agent\\ex16\\.env`에 저장합니다.
7. Streamlit 앱을 재시작한 뒤 `Google 로그인 열기`를 다시 누릅니다.
        """
    )
    st.code(
        "\n".join(
            [
                "GOOGLE_CALENDAR_ID=primary",
                "GOOGLE_OAUTH_CLIENT_ID=발급받은_CLIENT_ID",
                "GOOGLE_OAUTH_CLIENT_SECRET=발급받은_CLIENT_SECRET",
                "GOOGLE_OAUTH_REDIRECT_URI=http://localhost:8501",
                "GOOGLE_OAUTH_TOKEN_FILE=data/google_token.json",
            ]
        ),
        language="dotenv",
    )
    st.markdown("#### 사용자 처리")
    st.markdown(
        """
- 사용자는 키를 입력하지 않습니다.
- 사용자는 앱의 `Google 로그인 열기` 버튼을 누르고 Gmail로 로그인합니다.
- Google Calendar 권한 동의 후 앱으로 돌아오면 현재 보기 범위의 일정을 가져옵니다.
        """
    )


def render_candidates() -> None:
    st.markdown("### 관심 사이트 수집 후보")
    candidates = [candidate for candidate in store.list_candidates() if candidate.source in REQUESTED_SITE_SOURCES]
    if not candidates:
        st.caption("수집된 모집중 공고가 없습니다. 좌측에서 관심 사이트 수집을 실행하세요.")
        return
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
    st.markdown("### 우선순위 추천")
    recommendations = recommend_priorities([event for event in events if event.end_at >= datetime.now()])
    if not recommendations:
        st.caption("추천할 예정 일정이 없습니다.")
        return
    for item in recommendations[:8]:
        st.markdown(f"**{item.event.title}**")
        st.caption(f"{item.reason} · 점수 {item.score}")


def render_ai_chat_input(events: list[ScheduleEvent]) -> None:
    with st.container(border=True):
        st.markdown("**AI 채팅**")
        chat_col, send_col = st.columns([0.78, 0.22], gap="small")
        question = chat_col.text_input("AI 채팅 입력", placeholder="이번 주 면접 일정 알려줘", label_visibility="collapsed")
        if send_col.button("전송", type="primary", use_container_width=True):
            result = answer_schedule_question(question, events)
            st.session_state.highlight_event_ids = result.matched_event_ids
            st.session_state.chat_history.append({"question": question, "answer": result.answer})
            st.session_state.right_menu = "상세 정보"
            st.rerun()


@st.dialog("일정/작업 편집")
def day_editor_dialog(events: list[ScheduleEvent]) -> None:
    st.markdown(f"### {st.session_state.selected_date:%Y-%m-%d}")
    render_event_editor(events, prefix="dialog")
    if st.button("닫기", use_container_width=True):
        st.session_state.show_day_dialog = False
        st.query_params.clear()
        st.rerun()


def main() -> None:
    init_state()
    inject_styles()
    handle_google_oauth_callback()
    run_auto_site_collection()

    all_events = store.list_events(include_past=True)
    left, center, right = st.columns([0.2, 0.48, 0.32], gap="small")
    with left:
        render_left(all_events)
    with center:
        render_center(all_events)
    with right:
        render_right(all_events)

    inject_resizer_component()

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
