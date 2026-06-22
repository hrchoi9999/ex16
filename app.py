from __future__ import annotations

import calendar
import re
import urllib.parse
from datetime import date, datetime, time, timedelta
from html import escape

import streamlit as st
import streamlit.components.v1 as components

from personal_assistant.ai_chat import answer_schedule_question
from personal_assistant.briefing import generate_briefing
from personal_assistant.business_days import (
    eligible_registration_days,
    holiday_dates_from_events,
    is_business_day,
    is_holiday_event,
    is_known_korean_holiday,
    is_weekend,
)
from personal_assistant.config import settings
from personal_assistant.database import ScheduleStore
from personal_assistant.execution_planner import STAGE_LABELS, generate_task_plan
from personal_assistant.google_calendar import GoogleCalendarClient
from personal_assistant.models import ExternalScheduleCandidate, ScheduleEvent, TaskPlanItem
from personal_assistant.nlp import CommandParser
from personal_assistant.priority import recommend_priorities
from personal_assistant.risk import assess_risks
from personal_assistant.site_collector import REQUESTED_SITE_SOURCES, collect_interest_sites


st.set_page_config(page_title="AI Scheduler", page_icon=":calendar:", layout="wide")

VIEW_TITLES = {"day": "일 보기", "week": "주 보기", "month": "월 보기"}
WEEKDAY_LABELS = ["월", "화", "수", "목", "금", "토", "일"]
RIGHT_MENUS = ["상세 정보", "브리핑", "실행 계획", "리스크 코치", "일정 편집", "AI 일정", "Google 연동", "관심 사이트", "우선순위"]


@st.cache_resource
def get_store() -> ScheduleStore:
    return ScheduleStore(settings.database_path)


store = get_store()
parser = CommandParser()
calendar_client = GoogleCalendarClient()


def reset_google_auth_session() -> None:
    st.session_state.google_auth_url = ""
    st.session_state.google_auth_state = ""
    st.session_state.google_code_verifier = ""


def google_auth_url_is_stale(auth_url: str) -> bool:
    if not auth_url:
        return False
    redirect_uris = urllib.parse.parse_qs(urllib.parse.urlparse(auth_url).query).get("redirect_uri", [])
    if not redirect_uris:
        return True
    return redirect_uris[0] != calendar_client._redirect_uri()


def remember_google_auth_start(result) -> None:
    st.session_state.google_auth_url = result.authorization_url
    st.session_state.google_auth_state = result.state
    st.session_state.google_code_verifier = getattr(result, "code_verifier", "")


def init_state() -> None:
    today = date.today()
    st.session_state.setdefault("selected_date", today)
    st.session_state.setdefault("view_mode", "month")
    st.session_state.setdefault("right_menu", "상세 정보")
    st.session_state.setdefault("sync_message", "")
    st.session_state.setdefault("site_message", "")
    st.session_state.setdefault("risk_message", "")
    st.session_state.setdefault("briefing_message", "")
    st.session_state.setdefault("chat_history", [])
    st.session_state.setdefault("highlight_event_ids", [])
    st.session_state.setdefault("show_day_dialog", False)
    st.session_state.setdefault("last_site_collection_at", None)
    st.session_state.setdefault("google_auth_url", "")
    st.session_state.setdefault("google_auth_state", "")
    st.session_state.setdefault("google_code_verifier", "")
    if google_auth_url_is_stale(st.session_state.google_auth_url):
        reset_google_auth_session()

    query_view = st.query_params.get("view")
    query_date = st.query_params.get("date")
    query_dialog = st.query_params.get("dialog")
    query_menu = st.query_params.get("menu")
    if query_view in VIEW_TITLES:
        st.session_state.view_mode = query_view
    if query_menu in RIGHT_MENUS:
        st.session_state.right_menu = query_menu
    if query_date:
        try:
            st.session_state.selected_date = date.fromisoformat(query_date)
        except ValueError:
            pass
    if query_dialog == "1":
        st.session_state.show_day_dialog = True
        st.session_state.right_menu = "일정 편집"
    else:
        st.session_state.show_day_dialog = False


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

    result = calendar_client.finish_oauth(
        code=code,
        state=state,
        code_verifier=st.session_state.google_code_verifier,
    )
    if result.success:
        store.register_user(email=result.email or "google-user", display_name=result.display_name)
        reset_google_auth_session()
        import_google_events_for_current_period()
    else:
        reset_google_auth_session()
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
            font-size: 20px;
            font-weight: 900;
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
        .mini-cell.non-working {
            color: #dc2626;
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
            display: flex;
            align-items: flex-start;
            padding: 22px 24px 14px;
        }
        .calendar-title-group {
            display: inline-flex;
            align-items: flex-start;
            gap: 10px;
        }
        .calendar-heading {
            min-width: 150px;
        }
        .calendar-title {
            margin: 0;
            font-size: 24px;
            font-weight: 760;
        }
        .calendar-subtitle {
            margin: 6px 0 0;
            color: var(--muted);
            font-size: .9rem;
        }
        .nav-square {
            display: flex;
            width: 36px;
            height: 36px;
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
        div[class*="st-key-nav_prev"] button,
        div[class*="st-key-nav_next"] button {
            width: 36px !important;
            min-width: 36px !important;
            height: 36px !important;
            min-height: 36px !important;
            padding: 0 !important;
            border: 1px solid var(--line) !important;
            border-radius: 8px !important;
            background: #fff !important;
            color: var(--text) !important;
            font-size: 1.35rem !important;
            font-weight: 900 !important;
            line-height: 1 !important;
        }
        div[class*="st-key-nav_prev"] button:hover,
        div[class*="st-key-nav_next"] button:hover {
            border-color: var(--primary) !important;
            color: var(--primary) !important;
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
        .month-head.non-working {
            color: #dc2626;
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
        div[class*="st-key-month_day_"] button {
            background: transparent !important;
            border: 0 !important;
            box-shadow: none !important;
            color: var(--text) !important;
            align-items: flex-start !important;
            display: flex !important;
            justify-content: flex-start !important;
            min-height: 100% !important;
            padding: 8px !important;
            text-align: left !important;
            font-size: .82rem !important;
            font-weight: 520 !important;
        }
        div[class*="st-key-week_day_"] button {
            background: transparent !important;
            border: 0 !important;
            box-shadow: none !important;
            color: var(--text) !important;
            justify-content: flex-start !important;
            min-height: 18px !important;
            padding: 0 !important;
            text-align: left !important;
            font-size: .82rem !important;
            font-weight: 520 !important;
        }
        div[class*="st-key-month_day_"] {
            position: absolute !important;
            inset: 0 !important;
            z-index: 4 !important;
        }
        div[class*="st-key-month_day_"] div[data-testid="stButton"] {
            height: 100% !important;
            width: 100% !important;
        }
        div[class*="st-key-month_day_"] button {
            height: 100% !important;
            width: 100% !important;
        }
        div[class*="st-key-month_day_"] div[data-testid="stButton"],
        div[class*="st-key-month_day_"] div[data-testid="stButton"] > button,
        div[class*="st-key-month_day_"] button > div,
        div[class*="st-key-month_day_"] div[data-testid="stMarkdownContainer"] {
            justify-content: flex-start !important;
            text-align: left !important;
            width: 100% !important;
        }
        div[class*="st-key-month_day_"] button p,
        div[class*="st-key-month_day_"] button span {
            width: 100% !important;
            text-align: left !important;
        }
        div[class*="st-key-month_day_"] button:hover,
        div[class*="st-key-week_day_"] button:hover {
            background: transparent !important;
            color: var(--primary) !important;
            border: 0 !important;
        }
        div[class*="st-key-month_day_"] button:disabled {
            background: transparent !important;
            border: 0 !important;
            color: var(--muted) !important;
            opacity: .45 !important;
        }
        div[class*="st-key-month_cell_"] {
            min-height: 112px !important;
            padding: 8px !important;
            border-right: 1px solid var(--line-soft) !important;
            border-bottom: 1px solid var(--line-soft) !important;
            border-radius: 0 !important;
            background: #fff !important;
            overflow: hidden !important;
            position: relative !important;
        }
        div[class*="st-key-month_cell_"] div[data-testid="stMarkdownContainer"] {
            pointer-events: none !important;
            position: relative !important;
            z-index: 6 !important;
        }
        .month-cell-date-space {
            height: 24px;
            pointer-events: none;
        }
        div[class*="st-key-month_cell_outside_"] {
            background: #f8fafc !important;
            opacity: .58 !important;
        }
        div[class*="st-key-month_cell_selected_"] {
            box-shadow: inset 0 0 0 2px var(--primary) !important;
            background: #eef5ff !important;
        }
        .event-pill {
            display: block;
            margin-top: 5px;
            padding: 0;
            border-radius: 0;
            background: transparent;
            color: #4b5563;
            font-size: .66rem;
            font-weight: 600;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        .event-pill.highlight {
            animation: blink-event 1s ease-in-out infinite;
            color: #7a4b00;
        }
        .event-pill.deadline {
            color: #b91c1c;
            border: 0;
            font-weight: 700;
        }
        .event-pill.deadline.highlight {
            color: #991b1b;
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
            border-left: 0;
            background: transparent;
            color: #4b5563;
            border-radius: 0;
            padding: 0 4px;
            overflow: hidden;
            font-size: .76rem;
            font-weight: 650;
        }
        .timeline-event.highlight {
            animation: blink-event 1s ease-in-out infinite;
        }
        .timeline-event.deadline {
            color: #7f1d1d;
            font-weight: 800;
        }
        .timeline-event.deadline.highlight {
            color: #991b1b;
        }
        .right-title {
            margin: 0 0 12px;
            font-size: 20px !important;
            line-height: 1.15 !important;
            font-weight: 900;
        }
        .panel-section-title {
            margin: 0 0 14px;
            color: var(--text);
            font-size: 20px !important;
            line-height: 1.15 !important;
            font-weight: 850;
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
        .risk-badge {
            display: inline-flex;
            align-items: center;
            border-radius: 999px;
            padding: 3px 8px;
            font-size: .72rem;
            font-weight: 850;
            margin-left: 6px;
        }
        .risk-badge.safe {
            background: #dcfce7;
            color: #166534;
        }
        .risk-badge.caution {
            background: #fef3c7;
            color: #92400e;
        }
        .risk-badge.danger {
            background: #fee2e2;
            color: #991b1b;
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


def should_show_event_on_day(event: ScheduleEvent, day: date, holiday_dates: set[date]) -> bool:
    if not event.start_at.date() <= day <= event.end_at.date():
        return False
    if event.start_at.date() == event.end_at.date():
        return True
    if is_holiday_event(event) or event.title.startswith("[마감]") or bool(event.source_url):
        return True
    return is_business_day(day, holiday_dates)


def events_for_day(events: list[ScheduleEvent], day: date, holiday_dates: set[date] | None = None) -> list[ScheduleEvent]:
    dates = holiday_dates if holiday_dates is not None else holiday_dates_from_events(events)
    return [event for event in events if should_show_event_on_day(event, day, dates)]


def events_in_period(events: list[ScheduleEvent], start_at: datetime, end_at: datetime) -> list[ScheduleEvent]:
    return [event for event in events if start_at <= event.start_at < end_at]


def compact(text: str, limit: int = 22) -> str:
    return text[:limit] + "..." if len(text) > limit else text


def calendar_href(target_date: date, view_mode: str, dialog: bool = False) -> str:
    params = {
        "view": view_mode,
        "date": target_date.isoformat(),
        "menu": "일정 편집" if dialog else st.session_state.get("right_menu", "상세 정보"),
    }
    if dialog:
        params["dialog"] = "1"
    return f"?{urllib.parse.urlencode(params)}"


def select_calendar_day(target_date: date, view_mode: str, has_events: bool) -> None:
    st.session_state.selected_date = target_date
    st.session_state.view_mode = view_mode
    st.query_params["view"] = view_mode
    st.query_params["date"] = target_date.isoformat()
    if has_events:
        st.session_state.show_day_dialog = False
        st.session_state.right_menu = "상세 정보"
        st.query_params["menu"] = "상세 정보"
        if "dialog" in st.query_params:
            del st.query_params["dialog"]
    else:
        st.session_state.show_day_dialog = True
        st.session_state.right_menu = "일정 편집"
        st.query_params["menu"] = "일정 편집"
        st.query_params["dialog"] = "1"


def navigate_calendar(target_date: date, view_mode: str) -> None:
    st.session_state.selected_date = target_date
    st.session_state.view_mode = view_mode
    st.session_state.show_day_dialog = False
    st.query_params["view"] = view_mode
    st.query_params["date"] = target_date.isoformat()
    st.query_params["menu"] = st.session_state.get("right_menu", "상세 정보")
    if "dialog" in st.query_params:
        del st.query_params["dialog"]


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
    import_google_events_for_range(start_at, end_at, "현재 보기 범위")


def import_google_events_for_wide_period() -> None:
    selected = st.session_state.selected_date
    start_at = datetime(selected.year - 1, 1, 1)
    end_at = datetime(selected.year + 2, 1, 1)
    import_google_events_for_range(start_at, end_at, f"{selected.year - 1}~{selected.year + 1}년")


def import_google_events_for_range(start_at: datetime, end_at: datetime, label: str) -> None:
    result = calendar_client.list_events(start_at, end_at)
    if result.success:
        for event in result.events:
            store.upsert_google_event(event)
        st.session_state.sync_message = (
            f"{label}({start_at:%Y-%m-%d}~{end_at:%Y-%m-%d})에서 "
            f"{len(result.events)}개 일정을 가져와 저장/갱신했습니다. "
            "가져온 일정이 현재 달에 없으면 좌우 꺾쇠로 해당 월로 이동하세요."
        )
    else:
        st.session_state.sync_message = f"{label}({start_at:%Y-%m-%d}~{end_at:%Y-%m-%d}) 조회 실패: {result.message}"


def create_event(event: ScheduleEvent) -> ScheduleEvent:
    sync = calendar_client.create_event(event)
    if sync.google_event_id:
        event.google_event_id = sync.google_event_id
        event.sync_status = "synced"
        if not event.source_url and event.source == "local":
            event.source = "google_calendar"
    saved = store.add_event(event)
    st.session_state.sync_message = sync.message
    return saved


def create_events_for_registration_period(
    title: str,
    start_day: date,
    end_day: date,
    start_time: time,
    end_time: time,
    description: str,
    importance: int,
    existing_events: list[ScheduleEvent],
) -> list[ScheduleEvent]:
    holiday_dates = holiday_dates_from_events(existing_events)
    registration_days = eligible_registration_days(start_day, end_day, holiday_dates)
    saved_events: list[ScheduleEvent] = []
    for registration_day in registration_days:
        saved_events.append(
            create_event(
                ScheduleEvent(
                    id=None,
                    title=title,
                    start_at=datetime.combine(registration_day, start_time),
                    end_at=datetime.combine(registration_day, end_time),
                    description=description,
                    importance=importance,
                )
            )
        )
    return saved_events


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


def scan_and_store_risks(events: list[ScheduleEvent]) -> None:
    task_plan_by_event = {
        int(event.id): store.list_task_plan(int(event.id))
        for event in events
        if event.id is not None
    }
    assessments = assess_risks(events, task_plan_by_event)
    for assessment in assessments:
        store.upsert_risk_assessment(assessment)
    danger_count = sum(1 for assessment in assessments if assessment.risk_level == "danger")
    caution_count = sum(1 for assessment in assessments if assessment.risk_level == "caution")
    st.session_state.risk_message = f"{len(assessments)}개 일정을 스캔했습니다. 위험 {danger_count}개, 주의 {caution_count}개입니다."


def create_and_store_briefing(events: list[ScheduleEvent], scope: str) -> None:
    selected = st.session_state.selected_date
    if scope == "week":
        start = week_start(selected)
        end = start + timedelta(days=7)
        scope_key = f"week:{start.isoformat()}"
        scope_label = f"{start:%Y-%m-%d}~{(end - timedelta(days=1)):%Y-%m-%d}"
    else:
        start = selected
        end = selected + timedelta(days=1)
        scope_key = f"day:{selected.isoformat()}"
        scope_label = f"{selected:%Y-%m-%d}"

    scoped_events = [
        event
        for event in events
        if event.id is not None and start <= event.start_at.date() < end
    ]
    scan_and_store_risks(events)
    risk_by_event = {assessment.event_id: assessment for assessment in store.list_risk_assessments()}
    task_plan_by_event = {
        int(event.id): store.list_task_plan(int(event.id))
        for event in scoped_events
        if event.id is not None
    }
    snapshot = generate_briefing(
        scope_key=scope_key,
        scope_label=scope_label,
        events=scoped_events,
        task_plan_by_event=task_plan_by_event,
        risk_by_event=risk_by_event,
    )
    saved = store.upsert_briefing_snapshot(snapshot)
    st.session_state.briefing_message = f"{saved.scope_label} 브리핑을 생성했습니다."


def briefing_scope_key(scope: str) -> str:
    selected = st.session_state.selected_date
    if scope == "week":
        return f"week:{week_start(selected).isoformat()}"
    return f"day:{selected.isoformat()}"


def parse_period(period: str) -> tuple[date, date]:
    matches = re.findall(r"(20\d{2})[.년/-]\s*(\d{1,2})[.월/-]\s*(\d{1,2})", period)
    if matches:
        first = date(*map(int, matches[0]))
        last = date(*map(int, matches[-1]))
        return first, max(first, last)
    return date.today(), date.today()


def candidate_to_event(candidate: ExternalScheduleCandidate) -> ScheduleEvent:
    start_day, end_day = parse_period(candidate.recruitment_period)
    deadline = end_day
    return ScheduleEvent(
        id=None,
        title=f"[마감] {candidate.title}",
        start_at=datetime.combine(deadline, time(9, 0)),
        end_at=datetime.combine(deadline, time(18, 0)),
        description=f"{candidate.source} {candidate.category}\n마감일: {deadline:%Y-%m-%d}\n모집기간: {candidate.recruitment_period}\nURL: {candidate.url}",
        location=candidate.source,
        importance=4,
        source=candidate.source,
        source_url=candidate.url,
        sync_status="local",
    )


def save_candidate_deadline_event(candidate: ExternalScheduleCandidate) -> ScheduleEvent:
    event = candidate_to_event(candidate)
    existing_events = store.list_events(include_past=True)
    existing = next((item for item in existing_events if item.source_url == candidate.url), None)
    if existing is None:
        return store.add_event(event)
    updated = store.update_event(
        int(existing.id),
        title=event.title,
        start_at=event.start_at,
        end_at=event.end_at,
        description=event.description,
        location=event.location,
        importance=event.importance,
        source=event.source,
        source_url=event.source_url,
        sync_status="local",
    )
    return updated if updated is not None else existing


def mini_calendar_html(events: list[ScheduleEvent]) -> str:
    selected = st.session_state.selected_date
    month = selected.replace(day=1)
    holiday_dates = holiday_dates_from_events(events)
    parts = [f"<p style='font-weight:900;margin:0 0 8px;'>{selected:%Y년 %m월}</p>", "<div class='mini-grid'>"]
    for label in ["일", "월", "화", "수", "목", "금", "토"]:
        parts.append(f"<div class='mini-cell' style='font-weight:900'>{label}</div>")
    for week in calendar.Calendar(firstweekday=6).monthdatescalendar(month.year, month.month):
        for day in week:
            classes = ["mini-cell"]
            if is_weekend(day) or is_known_korean_holiday(day, holiday_dates):
                classes.append("non-working")
            if day == date.today():
                classes.append("today")
            if day == selected:
                classes.append("selected")
            suffix = "•" if events_for_day(events, day, holiday_dates) else ""
            opacity = "opacity:.35;" if day.month != month.month else ""
            parts.append(f"<div class='{' '.join(classes)}' style='{opacity}'>{day.day}{suffix}</div>")
    parts.append("</div>")
    return "".join(parts)


def non_working_day_style(days: list[date], events: list[ScheduleEvent]) -> str:
    holiday_dates = holiday_dates_from_events(events)
    selectors: list[str] = []
    for day in days:
        if is_weekend(day) or is_known_korean_holiday(day, holiday_dates):
            key = day.isoformat()
            selectors.extend(
                [
                    f'div[class*="st-key-month_day_{key}"] button',
                    f'div[class*="st-key-month_day_{key}"] button p',
                    f'div[class*="st-key-month_day_{key}"] button span',
                    f'div[class*="st-key-week_day_{key}"] button',
                    f'div[class*="st-key-week_day_{key}"] button p',
                    f'div[class*="st-key-week_day_{key}"] button span',
                ]
            )
    if not selectors:
        return ""
    return f"<style>{', '.join(selectors)} {{ color: #dc2626 !important; }}</style>"


def render_left(events: list[ScheduleEvent]) -> None:
    st.html('<span class="layout-anchor"></span>')
    st.markdown(
        """
        <div class="brand">
            <div class="brand-icon">AI</div>
            <div>
                <span class="brand-title" style="display:block;font-size:20px !important;line-height:1.1 !important;font-weight:900 !important;color:#2563eb !important;">개인 일정 관리</span>
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
            remember_google_auth_start(result)
    if st.button("Google 로그인 링크 새로 만들기", use_container_width=True):
        result = calendar_client.start_oauth(login_hint=google_email.strip())
        if result.success:
            remember_google_auth_start(result)
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
    nav_prev, nav_title, nav_next, _spacer = st.columns([0.05, 0.18, 0.05, 0.72], gap="small")
    nav_prev.button(
        "‹",
        key=f"nav_prev_{view_mode}_{selected.isoformat()}",
        on_click=navigate_calendar,
        args=(previous_date, view_mode),
    )
    nav_title.markdown(
        f"""
        <div class="calendar-heading">
            <span class="calendar-title" style="display:block;font-size:24px !important;line-height:1.12 !important;font-weight:760 !important;color:#0f172a !important;">{escape(title)}</span>
            <p class="calendar-subtitle">{VIEW_TITLES[view_mode]} · 일정 {len(visible_events)}개</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    nav_next.button(
        "›",
        key=f"nav_next_{view_mode}_{selected.isoformat()}",
        on_click=navigate_calendar,
        args=(next_date, view_mode),
    )
    if view_mode == "month":
        render_month(events, selected)
    elif view_mode == "week":
        render_week(events, selected)
    else:
        render_day(events, selected)


def render_month(events: list[ScheduleEvent], selected: date) -> None:
    month = selected.replace(day=1)
    month_weeks = calendar.Calendar(firstweekday=0).monthdatescalendar(month.year, month.month)
    visible_days = [day for week in month_weeks for day in week if day.month == month.month]
    holiday_dates = holiday_dates_from_events(events)
    st.markdown(non_working_day_style(visible_days, events), unsafe_allow_html=True)
    head_cols = st.columns(7, gap=None)
    for index, (col, label) in enumerate(zip(head_cols, WEEKDAY_LABELS)):
        class_name = "month-head non-working" if index >= 5 else "month-head"
        col.markdown(f"<div class='{class_name}'>{label}</div>", unsafe_allow_html=True)
    for week in month_weeks:
        cols = st.columns(7, gap=None)
        for col, day in zip(cols, week):
            day_events = events_for_day(events, day, holiday_dates)
            cell_state = "selected" if day == selected else ("outside" if day.month != month.month else "normal")
            label = f"{day.day}"
            with col.container(height=112, border=False, key=f"month_cell_{cell_state}_{day.isoformat()}"):
                st.button(
                    label,
                    key=f"month_day_{day.isoformat()}",
                    type="secondary",
                    use_container_width=True,
                    disabled=day.month != month.month,
                    on_click=select_calendar_day,
                    args=(day, "month", bool(day_events)),
                )
                if day.month != month.month:
                    st.caption(" ")
                else:
                    st.markdown("<div class='month-cell-date-space'></div>", unsafe_allow_html=True)
                    for event in day_events[:4]:
                        st.markdown(event_pill_html(event), unsafe_allow_html=True)


def render_week(events: list[ScheduleEvent], selected: date) -> None:
    start = week_start(selected)
    week_days = [start + timedelta(days=index) for index in range(7)]
    holiday_dates = holiday_dates_from_events(events)
    st.markdown(non_working_day_style(week_days, events), unsafe_allow_html=True)
    header_cols = st.columns([0.5, 1, 1, 1, 1, 1, 1, 1], gap="small")
    header_cols[0].markdown("<div class='week-head-link' style='background:#fff;border-left:0;'>&nbsp;</div>", unsafe_allow_html=True)
    for index, day in enumerate(week_days):
        header_cols[index + 1].button(
            f"{WEEKDAY_LABELS[index]} {day.day}",
            key=f"week_day_{day.isoformat()}",
            type="primary" if day == selected else "secondary",
            use_container_width=True,
            on_click=select_calendar_day,
            args=(day, "week", bool(events_for_day(events, day, holiday_dates))),
        )

    grid_parts = ["<div class='week-grid'><div>"]
    for hour in range(7, 21):
        grid_parts.append(f"<div class='time-cell'>{hour:02d}:00</div>")
    grid_parts.append("</div>")
    for day in week_days:
        body = "".join(timeline_event_html(event) for event in events_for_day(events, day, holiday_dates))
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


def is_deadline_event(event: ScheduleEvent) -> bool:
    return bool(event.source_url and (event.title.startswith("[마감]") or event.source in REQUESTED_SITE_SOURCES))


def event_visual_classes(event: ScheduleEvent) -> str:
    classes: list[str] = []
    if event.id in st.session_state.highlight_event_ids:
        classes.append("highlight")
    if is_deadline_event(event):
        classes.append("deadline")
    return f" {' '.join(classes)}" if classes else ""


def event_pill_html(event: ScheduleEvent) -> str:
    return f"<span class='event-pill{event_visual_classes(event)}'>{escape(compact(event.title))}</span>"


def timeline_event_html(event: ScheduleEvent) -> str:
    start_hour = max(event.start_at.hour + event.start_at.minute / 60, 7)
    end_hour = max(event.end_at.hour + event.end_at.minute / 60, start_hour + 1)
    top = int((start_hour - 7) * 54)
    height = max(int((end_hour - start_hour) * 54), 42)
    return (
        f"<div class='timeline-event{event_visual_classes(event)}' style='top:{top}px;height:{height}px;'>"
        f"{escape(event.time_label)}<br>{escape(compact(event.title, 34))}</div>"
    )


def render_right(events: list[ScheduleEvent]) -> None:
    st.markdown(
        "<div class='right-title' style='font-size:20px !important;line-height:1.15 !important;'>작업 메뉴</div>",
        unsafe_allow_html=True,
    )
    menu = st.radio(
        "메뉴 선택",
        RIGHT_MENUS,
        index=RIGHT_MENUS.index(st.session_state.right_menu),
        horizontal=True,
        label_visibility="collapsed",
    )
    st.session_state.right_menu = menu
    if menu != "일정 편집" and st.session_state.show_day_dialog:
        st.session_state.show_day_dialog = False
        if "dialog" in st.query_params:
            del st.query_params["dialog"]
    if st.query_params.get("menu") != menu:
        st.query_params["menu"] = menu
    with st.container(height=560, border=True):
        render_right_content(events, menu)
    render_ai_chat_input(events)


def render_right_content(events: list[ScheduleEvent], menu: str) -> None:
    if menu == "상세 정보":
        render_selected_detail(events)
        render_chat_history()
    elif menu == "브리핑":
        render_context_briefing(events)
    elif menu == "실행 계획":
        render_execution_planner(events)
    elif menu == "리스크 코치":
        render_risk_coach(events)
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
    st.markdown(
        f"<div class='panel-section-title' style='font-size:20px !important;line-height:1.15 !important;'>{selected:%Y-%m-%d} 상세</div>",
        unsafe_allow_html=True,
    )
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
        if event.source_url:
            st.link_button("원문 URL 열기", event.source_url, use_container_width=True)
        if event.id is not None and st.button("실행 계획 생성/보기", key=f"detail_plan_{event.id}", use_container_width=True):
            existing = store.list_task_plan(int(event.id))
            if not existing:
                store.replace_task_plan(int(event.id), generate_task_plan(event))
            st.session_state.right_menu = "실행 계획"
            st.rerun()
    st.divider()
    render_event_editor(events, prefix="detail")


def render_execution_planner(events: list[ScheduleEvent]) -> None:
    selected = st.session_state.selected_date
    day_events = events_for_day(events, selected)
    st.markdown(f"<h3 class='panel-section-title'>{selected:%Y-%m-%d} 실행 계획</h3>", unsafe_allow_html=True)
    if not day_events:
        st.caption("선택된 날짜에 실행 계획을 만들 일정이 없습니다.")
        return

    event_options = {int(event.id): event for event in day_events if event.id is not None}
    option_ids = list(event_options)
    default_id = st.session_state.get("execution_plan_event_id")
    if default_id not in event_options:
        default_id = option_ids[0]
    selected_event_id = st.selectbox(
        "계획을 만들 일정",
        option_ids,
        index=option_ids.index(default_id),
        format_func=lambda event_id: event_options[event_id].title,
    )
    st.session_state.execution_plan_event_id = selected_event_id
    event = event_options[int(selected_event_id)]

    generate_col, clear_col = st.columns(2)
    if generate_col.button("AI 실행 계획 생성", type="primary", use_container_width=True):
        items = store.replace_task_plan(int(event.id), generate_task_plan(event))
        st.success(f"{len(items)}개 실행 항목을 생성했습니다.")
        st.rerun()
    if clear_col.button("계획 삭제", use_container_width=True):
        store.delete_task_plan(int(event.id))
        st.rerun()

    items = store.list_task_plan(int(event.id))
    if not items:
        st.info("아직 실행 계획이 없습니다. `AI 실행 계획 생성`을 눌러 오늘/이번주/마감전 작업으로 분해하세요.")
        return

    completed = sum(1 for item in items if item.completed)
    st.caption(f"진행률 {completed}/{len(items)} · 원 일정: {event.date_label} {event.time_label}")
    tabs = st.tabs([STAGE_LABELS[stage] for stage in STAGE_LABELS])
    for tab, stage in zip(tabs, STAGE_LABELS):
        with tab:
            stage_items = [item for item in items if item.stage == stage]
            if not stage_items:
                st.caption("해당 단계의 작업이 없습니다.")
                continue
            for item in stage_items:
                render_task_plan_item(event, item, events)


def render_task_plan_item(event: ScheduleEvent, item: TaskPlanItem, events: list[ScheduleEvent]) -> None:
    with st.container(border=True):
        checked = st.checkbox(
            item.title,
            value=item.completed,
            key=f"task_plan_done_{item.id}",
        )
        if checked != item.completed and item.id is not None:
            store.update_task_plan_item(int(item.id), completed=checked)
            st.rerun()
        st.caption(f"기한 {item.due_date:%Y-%m-%d} · 예상 {item.estimated_minutes}분 · 생성 {item.source}")
        already_exists = any(
            existing.source == "task_plan"
            and existing.start_at.date() == item.due_date
            and existing.title == f"[작업] {item.title}"
            for existing in events
        )
        if already_exists:
            st.caption("이미 캘린더 일정으로 반영됨")
        elif st.button("캘린더 일정으로 반영", key=f"task_plan_event_{item.id}", use_container_width=True):
            start_at = datetime.combine(item.due_date, time(9, 0))
            create_event(
                ScheduleEvent(
                    id=None,
                    title=f"[작업] {item.title}",
                    start_at=start_at,
                    end_at=start_at + timedelta(minutes=item.estimated_minutes),
                    description=f"실행 계획 항목\n원 일정: {event.title}\n원 일정일: {event.date_label}",
                    importance=max(event.importance, 3),
                    source="task_plan",
                    sync_status="local",
                )
            )
            st.rerun()


def render_risk_coach(events: list[ScheduleEvent]) -> None:
    st.markdown("<h3 class='panel-section-title'>마감 리스크 코치</h3>", unsafe_allow_html=True)
    if st.button("리스크 다시 스캔", type="primary", use_container_width=True):
        scan_and_store_risks(events)
        st.rerun()
    if st.session_state.risk_message:
        st.info(st.session_state.risk_message)

    assessments = store.list_risk_assessments()
    event_by_id = {int(event.id): event for event in events if event.id is not None and event.end_at >= datetime.now()}
    visible = [assessment for assessment in assessments if assessment.event_id in event_by_id]
    if not visible:
        st.caption("저장된 리스크 분석 결과가 없습니다. `리스크 다시 스캔`을 실행하세요.")
        return

    selected = st.session_state.selected_date
    selected_day = [assessment for assessment in visible if event_by_id[assessment.event_id].start_at.date() == selected]
    high_risk = [assessment for assessment in visible if assessment.risk_level in {"danger", "caution"}]

    st.caption(f"선택일 리스크 {len(selected_day)}개 · 전체 주의/위험 {len(high_risk)}개")
    for assessment in (selected_day or high_risk or visible)[:10]:
        render_risk_card(event_by_id[assessment.event_id], assessment, events)


def render_risk_card(event: ScheduleEvent, assessment, events: list[ScheduleEvent]) -> None:
    badge = (
        f"<span class='risk-badge {assessment.risk_level}'>{assessment.level_label} {assessment.risk_score}</span>"
    )
    with st.container(border=True):
        st.markdown(
            f"**{escape(event.date_label)} {escape(event.time_label)} · {escape(event.title)}** {badge}",
            unsafe_allow_html=True,
        )
        st.caption(f"다음 행동: {assessment.next_action}")
        for factor in assessment.risk_factors[:4]:
            st.markdown(f"- {factor}")
        action_col, plan_col = st.columns(2)
        if action_col.button("해당 날짜 보기", key=f"risk_detail_{event.id}", use_container_width=True):
            st.session_state.selected_date = event.start_at.date()
            st.session_state.right_menu = "상세 정보"
            st.rerun()
        if plan_col.button("실행 계획 생성", key=f"risk_plan_{event.id}", use_container_width=True):
            if event.id is not None:
                existing = store.list_task_plan(int(event.id))
                if not existing:
                    store.replace_task_plan(int(event.id), generate_task_plan(event))
                st.session_state.selected_date = event.start_at.date()
                st.session_state.right_menu = "실행 계획"
                st.rerun()


def render_context_briefing(events: list[ScheduleEvent]) -> None:
    st.markdown("<h3 class='panel-section-title'>맥락 기반 일정 브리핑</h3>", unsafe_allow_html=True)
    scope = st.radio(
        "브리핑 범위",
        ["day", "week"],
        format_func=lambda value: "선택일" if value == "day" else "이번 주",
        horizontal=True,
        label_visibility="collapsed",
    )
    if st.button("브리핑 생성/갱신", type="primary", use_container_width=True):
        create_and_store_briefing(events, scope)
        st.rerun()
    if st.session_state.briefing_message:
        st.info(st.session_state.briefing_message)

    snapshot = store.get_briefing_snapshot(briefing_scope_key(scope))
    if snapshot is None:
        st.caption("아직 생성된 브리핑이 없습니다. `브리핑 생성/갱신`을 실행하세요.")
        recent = store.list_briefing_snapshots()[:3]
        if recent:
            st.caption("최근 브리핑")
            for item in recent:
                st.markdown(f"- {item.scope_label} · {item.generated_at}")
        return

    st.markdown(f"**{snapshot.scope_label} 브리핑**")
    st.caption(f"생성 시각 {snapshot.generated_at}")
    st.info(snapshot.summary)
    st.markdown("**핵심 포인트**")
    for highlight in snapshot.highlights:
        st.markdown(f"- {highlight}")

    event_by_id = {int(event.id): event for event in events if event.id is not None}
    related_events = [event_by_id[event_id] for event_id in snapshot.related_event_ids if event_id in event_by_id]
    if related_events:
        st.markdown("**관련 일정**")
        for event in related_events[:6]:
            risk = store.get_risk_assessment(int(event.id)) if event.id is not None else None
            risk_text = f" · {risk.level_label} {risk.risk_score}" if risk else ""
            st.caption(f"{event.date_label} {event.time_label} · {event.title}{risk_text}")
            if event.source_url:
                st.link_button("원문 URL 열기", event.source_url, key=f"brief_link_{event.id}", use_container_width=True)

    action_col, risk_col = st.columns(2)
    if action_col.button("실행 계획으로 이동", use_container_width=True):
        st.session_state.right_menu = "실행 계획"
        st.rerun()
    if risk_col.button("리스크 코치로 이동", use_container_width=True):
        st.session_state.right_menu = "리스크 코치"
        st.rerun()


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
    st.markdown(
        f"<h3 class='panel-section-title'>{selected:%Y-%m-%d} 일정/작업 입력</h3>",
        unsafe_allow_html=True,
    )
    with st.form(f"{prefix}_create_form", clear_on_submit=True):
        title = st.text_input("제목", key=f"{prefix}_manual_title")
        date_col1, date_col2 = st.columns(2)
        start_day = date_col1.date_input("시작일", value=selected, key=f"{prefix}_manual_start_date")
        end_day = date_col2.date_input("종료일", value=selected, key=f"{prefix}_manual_end_date")
        time_col1, time_col2 = st.columns(2)
        start_time = time_col1.time_input("시작 시간", value=time(9, 0), key=f"{prefix}_manual_start_time")
        end_time = time_col2.time_input("종료 시간", value=time(10, 0), key=f"{prefix}_manual_end_time")
        importance = st.slider("중요도", 1, 5, 3, key=f"{prefix}_manual_importance")
        description = st.text_area("설명", key=f"{prefix}_manual_description", height=80)
        submitted = st.form_submit_button("일정 등록", type="primary", use_container_width=True)
        if submitted:
            if not title.strip():
                st.warning("제목을 입력해 주세요.")
            elif end_day < start_day:
                st.warning("종료일은 시작일과 같거나 이후여야 합니다.")
            elif end_time <= start_time:
                st.warning("종료 시간은 시작 시간보다 이후여야 합니다.")
            else:
                saved_events = create_events_for_registration_period(
                    title=title.strip(),
                    start_day=start_day,
                    end_day=end_day,
                    start_time=start_time,
                    end_time=end_time,
                    description=description.strip(),
                    importance=int(importance),
                    existing_events=events,
                )
                total_days = (end_day - start_day).days + 1
                skipped_days = max(total_days - len(saved_events), 0)
                if not saved_events:
                    st.warning("등록 가능한 업무일이 없습니다. 토요일, 일요일은 등록 대상에서 제외됩니다.")
                else:
                    st.session_state.sync_message = (
                        f"{len(saved_events)}개 업무일 일정으로 등록했습니다. "
                        f"토요일/일요일/공휴일 {skipped_days}일은 제외했습니다."
                    )
                    st.rerun()

    st.markdown("### 선택 날짜 일정 수정/삭제")
    if not day_events:
        st.caption("선택된 날짜에 등록된 일정이 없습니다.")
    for event in day_events:
        with st.form(f"{prefix}_edit_event_{event.id}"):
            st.markdown(f"**{event.title}**")
            updated_title = st.text_input("제목", value=event.title, key=f"{prefix}_title_{event.id}")
            edit_date_col1, edit_date_col2 = st.columns(2)
            updated_start_day = edit_date_col1.date_input(
                "시작일",
                value=event.start_at.date(),
                key=f"{prefix}_start_date_{event.id}",
            )
            updated_end_day = edit_date_col2.date_input(
                "종료일",
                value=event.end_at.date(),
                key=f"{prefix}_end_date_{event.id}",
            )
            edit_time_col1, edit_time_col2 = st.columns(2)
            updated_start_time = edit_time_col1.time_input(
                "시작 시간",
                value=event.start_at.time(),
                key=f"{prefix}_start_time_{event.id}",
            )
            updated_end_time = edit_time_col2.time_input(
                "종료 시간",
                value=event.end_at.time(),
                key=f"{prefix}_end_time_{event.id}",
            )
            updated_importance = st.slider("중요도", 1, 5, event.importance, key=f"{prefix}_importance_{event.id}")
            updated_description = st.text_area("설명", value=event.description, key=f"{prefix}_description_{event.id}", height=70)
            save_col, delete_col = st.columns(2)
            save = save_col.form_submit_button("수정 저장", use_container_width=True)
            remove = delete_col.form_submit_button("삭제", use_container_width=True)
            if save:
                start_at = datetime.combine(updated_start_day, updated_start_time)
                end_at = datetime.combine(updated_end_day, updated_end_time)
                if not updated_title.strip():
                    st.warning("제목을 입력해 주세요.")
                elif end_at <= start_at:
                    st.warning("종료일/시간은 시작일/시간보다 이후여야 합니다.")
                else:
                    update_event(
                        event,
                        title=updated_title.strip(),
                        start_at=start_at,
                        end_at=end_at,
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
                remember_google_auth_start(result)
            st.session_state.sync_message = result.message
            st.rerun()
        if st.session_state.google_auth_url:
            st.link_button("Google 로그인 화면 열기", st.session_state.google_auth_url, use_container_width=True)
    if st.button("현재 보기 범위 가져오기", use_container_width=True):
        import_google_events_for_current_period()
        st.rerun()
    if st.button("선택 연도 ±1년 가져오기", use_container_width=True):
        import_google_events_for_wide_period()
        st.rerun()
    st.caption("현재 보기 범위에 일정이 없더라도 다른 달/연도에 있는 Google 일정은 넓은 범위 가져오기로 추가할 수 있습니다.")
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
5. Authorized redirect URI에 `http://localhost:8501`를 추가합니다.
6. 발급된 Client ID와 Client Secret을 `C:\\AI_Agent\\.chatgptkey.env`에 저장합니다.
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
    st.markdown("#### `Google에서 확인하지 않은 앱` 화면이 나올 때")
    st.markdown(
        """
- 개발/테스트 중이면 Google Cloud Console의 OAuth consent screen에서 현재 Gmail 계정이 테스트 사용자로 등록되어 있어야 합니다.
- 테스트 사용자로 등록된 계정이라면 경고 화면에서 `고급`을 누른 뒤 `AI Scheduler(으)로 이동` 또는 `안전하지 않음` 표시가 붙은 계속 진행 링크를 선택합니다.
- 실제 외부 사용자에게 배포하려면 OAuth 앱 브랜드, 도메인, 개인정보처리방침, Calendar 데이터 접근 범위를 Google 검증 절차에 제출해야 합니다.
        """
    )


def render_candidates() -> None:
    st.markdown("### 관심 사이트 수집 후보")
    candidates = [candidate for candidate in store.list_candidates() if candidate.source in REQUESTED_SITE_SOURCES]
    if not candidates:
        st.caption("수집된 모집중 공고가 없습니다. 좌측에서 관심 사이트 수집을 실행하세요.")
        return
    if st.button("전체 후보를 마감일 일정으로 등록", use_container_width=True):
        for candidate in candidates:
            save_candidate_deadline_event(candidate)
            if candidate.id is not None:
                store.mark_candidate_selected(int(candidate.id))
        st.success(f"{len(candidates)}개 후보를 마감일 기준 일정으로 등록/갱신했습니다.")
        st.rerun()
    for candidate in candidates[:20]:
        st.markdown(f"**{candidate.title}**")
        st.caption(f"{candidate.source} · {candidate.category} · {candidate.recruitment_period}")
        st.link_button("원문 열기", candidate.url, use_container_width=True)
        if st.button("마감일 기준 일정 등록", key=f"candidate_{candidate.id}", use_container_width=True):
            save_candidate_deadline_event(candidate)
            if candidate.id is not None:
                store.mark_candidate_selected(int(candidate.id))
            st.success("선택한 공고를 마감일 기준 일정으로 등록했습니다.")
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
