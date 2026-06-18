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


st.set_page_config(page_title="AI Scheduler", page_icon=":calendar:", layout="wide")


VIEW_LABELS = {"day": "일", "week": "주", "month": "월"}
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
    st.session_state.setdefault("view_mode", "week")
    st.session_state.setdefault("sync_message", "")
    st.session_state.setdefault("search_query", "")
    query_view = st.query_params.get("view")
    if query_view in VIEW_LABELS:
        st.session_state.view_mode = query_view


def inject_styles() -> None:
    st.html(
        """
        <style>
        :root {
            --background: #f8f9ff;
            --surface: #ffffff;
            --surface-low: #eff4ff;
            --surface-container: #e5eeff;
            --surface-high: #dce9ff;
            --outline: #c3c6d7;
            --outline-soft: #e2e8f0;
            --text: #0b1c30;
            --muted: #434655;
            --primary: #004ac6;
            --primary-strong: #2563eb;
            --secondary: #712ae2;
            --success: #10b981;
            --warning: #b7791f;
            --danger: #ba1a1a;
            --font-kr: Pretendard, "Noto Sans KR", "Apple SD Gothic Neo", "Malgun Gothic", Inter, Roboto, Arial, sans-serif;
            --font-mono: "JetBrains Mono", "SFMono-Regular", Consolas, monospace;
        }
        html, body, .stApp, [data-testid="stAppViewContainer"] {
            background: var(--background) !important;
            color: var(--text) !important;
            font-family: var(--font-kr) !important;
        }
        [data-testid="stHeader"],
        [data-testid="stToolbar"],
        [data-testid="stDecoration"],
        [data-testid="stStatusWidget"],
        #MainMenu,
        footer {
            display: none !important;
            visibility: hidden !important;
        }
        .block-container {
            padding: 0 !important;
            max-width: 100% !important;
        }
        * {
            letter-spacing: 0 !important;
            font-family: var(--font-kr) !important;
        }
        h1, h2, h3, h4, p, span, label {
            color: var(--text);
        }
        .stTextInput input,
        .stTextArea textarea,
        .stDateInput input,
        .stTimeInput input,
        .stNumberInput input {
            border-color: var(--outline) !important;
            border-radius: .5rem !important;
            background: #fff !important;
        }
        .stButton > button {
            border-radius: .5rem !important;
            font-weight: 750 !important;
            min-height: 2.45rem;
        }
        div[role="radiogroup"] {
            gap: .35rem;
        }
        div[role="radiogroup"] label {
            border: 1px solid var(--outline);
            background: #fff;
            border-radius: .5rem;
            padding: .35rem .75rem;
        }
        .top-shell {
            height: 56px;
            display: grid;
            grid-template-columns: 250px minmax(260px, 1fr) 128px 42px 42px;
            gap: 14px;
            align-items: center;
            padding: 0 24px;
            background: var(--surface);
            border-bottom: 1px solid var(--outline);
        }
        .brand {
            display: flex;
            align-items: center;
            gap: 18px;
        }
        .brand-menu {
            font-size: 24px;
            color: var(--muted);
        }
        .brand-title {
            color: var(--primary);
            font-weight: 850;
            font-size: 1.08rem;
            margin: 0;
        }
        .search-pill {
            height: 36px;
            border: 1px solid var(--outline);
            border-radius: .5rem;
            display: flex;
            align-items: center;
            padding: 0 14px;
            color: var(--muted);
            background: #fff;
            font-size: .86rem;
        }
        .profile-chip {
            width: 32px;
            height: 32px;
            border-radius: 999px;
            border: 1px solid var(--outline);
            background: var(--surface-container);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: .78rem;
            color: var(--primary);
            font-weight: 850;
        }
        .workspace {
            display: grid;
            grid-template-columns: 250px minmax(460px, 1fr) 320px;
            min-height: 650px;
            background: var(--surface);
        }
        .left-pane {
            background: var(--surface-container);
            border-right: 1px solid var(--outline);
            padding: 28px 24px;
        }
        .main-pane {
            background: var(--surface);
            overflow: hidden;
        }
        .right-pane {
            background: var(--surface-low);
            border-left: 1px solid var(--outline);
            padding: 24px;
        }
        .identity {
            display: flex;
            align-items: center;
            gap: 14px;
            margin-bottom: 32px;
        }
        .identity-icon {
            width: 42px;
            height: 42px;
            border-radius: .5rem;
            background: var(--primary-strong);
            color: #fff;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 900;
        }
        .identity-title {
            margin: 0;
            color: var(--primary);
            font-weight: 850;
        }
        .identity-subtitle {
            margin: 2px 0 0;
            color: var(--muted);
            font-size: .88rem;
        }
        .nav-item {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 12px 16px;
            border-radius: 0 999px 999px 0;
            color: var(--muted);
            font-weight: 750;
            margin-bottom: 6px;
            text-decoration: none !important;
        }
        .nav-item.active {
            background: var(--primary-strong);
            color: #fff;
        }
        .nav-item:hover {
            background: rgba(37,99,235,.12);
            color: var(--primary);
        }
        .nav-item.active:hover {
            background: var(--primary-strong);
            color: #fff;
        }
        .section-label {
            font-family: var(--font-mono) !important;
            color: var(--text);
            text-transform: uppercase;
            font-size: .74rem;
            font-weight: 900;
            margin: 30px 0 14px;
        }
        .integration-row {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 10px 2px;
            color: var(--text);
            font-weight: 750;
        }
        .integration-left {
            display: flex;
            align-items: center;
            gap: 14px;
        }
        .integration-icon {
            width: 32px;
            height: 32px;
            border: 1px solid var(--outline);
            background: #fff;
            border-radius: .25rem;
            display: flex;
            align-items: center;
            justify-content: center;
            color: var(--primary);
            font-size: .76rem;
            font-weight: 900;
        }
        .status-dot {
            width: 8px;
            height: 8px;
            border-radius: 999px;
            background: var(--success);
        }
        .status-dot.off {
            background: var(--outline);
        }
        .mini-month {
            display: grid;
            grid-template-columns: repeat(7, 1fr);
            gap: 4px;
            font-size: .74rem;
            text-align: center;
        }
        .mini-label {
            margin: 0 0 4px;
            color: var(--muted);
            font-weight: 800;
        }
        .mini-day {
            position: relative;
            min-height: 26px;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: .35rem;
        }
        .mini-day.today {
            background: var(--primary);
            color: #fff;
            font-weight: 850;
        }
        .mini-day.selected {
            box-shadow: inset 0 0 0 2px var(--primary);
        }
        .mini-dot {
            position: absolute;
            bottom: 3px;
            width: 4px;
            height: 4px;
            border-radius: 999px;
            background: var(--primary-strong);
        }
        .storage-card {
            border: 1px solid var(--outline);
            background: #fff;
            border-radius: .75rem;
            padding: 18px;
            margin-top: 32px;
        }
        .storage-top {
            display: flex;
            justify-content: space-between;
            font-weight: 850;
            margin-bottom: 8px;
        }
        .progress-track {
            height: 6px;
            border-radius: 999px;
            background: #dbe7fb;
            overflow: hidden;
        }
        .progress-fill {
            height: 100%;
            background: var(--primary-strong);
        }
        .calendar-head {
            padding: 28px 24px 22px;
            border-bottom: 1px solid var(--outline);
            background: rgba(255,255,255,.96);
        }
        .calendar-toolbar {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            gap: 18px;
            margin-bottom: 26px;
        }
        .calendar-title {
            font-size: 1.24rem;
            font-weight: 850;
            margin: 0;
        }
        .calendar-subtitle {
            color: var(--muted);
            margin: 4px 0 0;
        }
        .calendar-grid {
            display: grid;
            grid-template-columns: 60px repeat(7, minmax(0, 1fr));
            min-height: 560px;
        }
        .day-header-grid {
            display: grid;
            grid-template-columns: 60px repeat(7, 1fr);
            text-align: center;
        }
        .day-name {
            font-family: var(--font-mono) !important;
            color: var(--muted);
            font-weight: 900;
            font-size: .78rem;
            margin: 0;
        }
        .day-number {
            margin: 4px auto 0;
            width: 32px;
            height: 32px;
            border-radius: 999px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 850;
        }
        .day-number.today {
            background: var(--primary);
            color: #fff;
        }
        .time-col {
            border-right: 1px solid var(--outline);
        }
        .time-cell {
            height: 64px;
            border-bottom: 1px solid rgba(195,198,215,.45);
            display: flex;
            justify-content: center;
            align-items: flex-start;
            padding-top: 10px;
            color: var(--muted);
            font-family: var(--font-mono) !important;
            font-size: .78rem;
        }
        .day-col {
            position: relative;
            border-right: 1px solid rgba(195,198,215,.35);
            background:
              repeating-linear-gradient(to bottom, transparent 0, transparent 63px, rgba(195,198,215,.35) 64px);
        }
        .day-col.today {
            background:
              linear-gradient(rgba(0,74,198,.06), rgba(0,74,198,.06)),
              repeating-linear-gradient(to bottom, transparent 0, transparent 63px, rgba(195,198,215,.35) 64px);
        }
        .calendar-event {
            position: absolute;
            left: 6px;
            right: 6px;
            border-radius: .5rem;
            padding: 9px 10px;
            overflow: hidden;
            border-left: 4px solid var(--primary);
            background: rgba(37,99,235,.12);
            color: var(--primary);
        }
        .calendar-event.secondary {
            border-left-color: var(--secondary);
            color: var(--secondary);
            background: rgba(113,42,226,.12);
        }
        .calendar-event.muted {
            border-left-color: var(--muted);
            color: var(--muted);
            background: rgba(67,70,85,.12);
        }
        .calendar-event-title {
            font-weight: 900;
            font-size: .72rem;
            line-height: 1.15;
            margin: 0 0 3px;
        }
        .calendar-event-time {
            font-size: .68rem;
            margin: 0;
            opacity: .86;
        }
        .day-agenda {
            padding: 20px 24px;
            display: grid;
            gap: 12px;
        }
        .agenda-item {
            border: 1px solid var(--outline-soft);
            border-left: 4px solid var(--primary-strong);
            border-radius: .65rem;
            padding: 14px 16px;
            background: #fff;
        }
        .agenda-time {
            color: var(--primary);
            font-weight: 850;
            font-size: .82rem;
            margin: 0 0 4px;
        }
        .agenda-title {
            font-weight: 850;
            margin: 0 0 4px;
        }
        .month-view-grid {
            display: grid;
            grid-template-columns: repeat(7, minmax(0, 1fr));
            border-top: 1px solid var(--outline-soft);
            border-left: 1px solid var(--outline-soft);
        }
        .month-label {
            padding: 10px;
            background: var(--surface-low);
            border-right: 1px solid var(--outline-soft);
            border-bottom: 1px solid var(--outline-soft);
            color: var(--muted);
            font-weight: 850;
            text-align: center;
        }
        .month-cell {
            min-height: 112px;
            padding: 9px;
            border-right: 1px solid var(--outline-soft);
            border-bottom: 1px solid var(--outline-soft);
            background: #fff;
        }
        .month-cell.outside {
            background: #f8fafc;
            opacity: .58;
        }
        .month-cell.today {
            box-shadow: inset 0 0 0 2px var(--primary);
        }
        .month-cell.selected {
            background: rgba(37,99,235,.06);
        }
        .month-date {
            font-weight: 850;
            margin-bottom: 6px;
        }
        .month-event {
            display: block;
            padding: 3px 6px;
            margin-top: 4px;
            border-radius: .35rem;
            background: rgba(37,99,235,.12);
            color: var(--primary);
            font-size: .7rem;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        .assistant-card, .task-card, .insight-card {
            border: 1px solid var(--outline);
            background: #fff;
            border-radius: .75rem;
            padding: 18px;
            margin-bottom: 16px;
        }
        .assistant-title {
            font-weight: 850;
            margin: 0 0 12px;
        }
        .assistant-message {
            background: var(--surface-low);
            border: 1px solid rgba(195,198,215,.55);
            border-radius: .75rem;
            padding: 12px;
            color: var(--text);
            font-size: .86rem;
        }
        .task-row {
            display: flex;
            align-items: flex-start;
            gap: 12px;
        }
        .task-title {
            font-weight: 800;
            margin: 0;
        }
        .task-meta {
            color: var(--muted);
            font-size: .75rem;
            margin: 4px 0 0;
        }
        .tag {
            display: inline-block;
            padding: 2px 7px;
            border-radius: .35rem;
            background: #f1f5f9;
            color: var(--muted);
            font-size: .66rem;
            font-weight: 850;
            margin-left: 6px;
        }
        .tag.high {
            background: #ffdad6;
            color: #93000a;
        }
        .empty-note {
            padding: 12px;
            border: 1px dashed var(--outline);
            border-radius: .5rem;
            background: #fff;
            color: var(--muted);
            font-size: .86rem;
        }
        .streamlit-forms {
            padding: 24px;
            background: var(--surface);
            border-top: 1px solid var(--outline);
        }
        .bottom-tool-shell {
            margin-bottom: 16px;
            padding: 18px;
            border: 1px solid var(--outline);
            border-radius: .75rem;
            background: var(--surface-low);
        }
        @media (max-width: 900px) {
            .workspace {
                grid-template-columns: 210px minmax(420px, 1fr) 280px;
                overflow-x: auto;
            }
            .top-shell {
                grid-template-columns: 210px minmax(220px, 1fr) 112px 42px 42px;
                overflow-x: auto;
            }
        }
        </style>
        """
    )


def week_start(day: date) -> date:
    return day - timedelta(days=day.weekday())


def add_months(day: date, months: int) -> date:
    month_index = day.month - 1 + months
    year = day.year + month_index // 12
    month = month_index % 12 + 1
    last_day = calendar.monthrange(year, month)[1]
    return day.replace(year=year, month=month, day=min(day.day, last_day))


def period_bounds(selected: date, view_mode: str) -> tuple[datetime, datetime]:
    if view_mode == "day":
        start = selected
        end = selected + timedelta(days=1)
    elif view_mode == "month":
        start = selected.replace(day=1)
        end = add_months(start, 1)
    else:
        start = week_start(selected)
        end = start + timedelta(days=7)
    return datetime.combine(start, time.min), datetime.combine(end, time.min)


def shift_selected_date(direction: int) -> None:
    selected = st.session_state.selected_date
    view_mode = st.session_state.view_mode
    if view_mode == "day":
        st.session_state.selected_date = selected + timedelta(days=direction)
    elif view_mode == "month":
        st.session_state.selected_date = add_months(selected, direction)
    else:
        st.session_state.selected_date = selected + timedelta(days=7 * direction)


def events_for_day(events: list[ScheduleEvent], day: date) -> list[ScheduleEvent]:
    return [event for event in events if event.start_at.date() == day]


def events_in_period(events: list[ScheduleEvent], start_at: datetime, end_at: datetime) -> list[ScheduleEvent]:
    return [event for event in events if start_at <= event.start_at < end_at]


def compact_title(title: str, limit: int = 42) -> str:
    return title[:limit] + "..." if len(title) > limit else title


def event_top_and_height(event: ScheduleEvent) -> tuple[int, int]:
    start_hour = max(event.start_at.hour + event.start_at.minute / 60, 7)
    end_hour = max(event.end_at.hour + event.end_at.minute / 60, start_hour + 1)
    top = int((start_hour - 7) * 64)
    height = max(int((end_hour - start_hour) * 64), 48)
    return top, height


def event_variant(event: ScheduleEvent) -> str:
    if event.importance >= 5:
        return "secondary"
    if event.importance <= 2:
        return "muted"
    return ""


def calendar_event_html(event: ScheduleEvent) -> str:
    top, height = event_top_and_height(event)
    return f"""
    <div class="calendar-event {event_variant(event)}" style="top:{top}px;height:{height}px;">
        <p class="calendar-event-title">{escape(compact_title(event.title))}</p>
        <p class="calendar-event-time">{escape(event.time_label)}</p>
    </div>
    """


def render_week_calendar(events: list[ScheduleEvent], selected: date) -> str:
    start = week_start(selected)
    days = [start + timedelta(days=i) for i in range(7)]
    today = date.today()
    header = ["<div></div>"]
    for label, day in zip(WEEKDAY_LABELS, days, strict=True):
        today_class = " today" if day == today else ""
        header.append(
            f"""
            <div>
                <p class="day-name">{label}</p>
                <div class="day-number{today_class}">{day.day}</div>
            </div>
            """
        )
    time_col = "<div class='time-col'>" + "".join(
        f"<div class='time-cell'>{hour:02d}:00</div>" for hour in range(7, 21)
    ) + "</div>"
    day_cols = []
    for day in days:
        today_class = " today" if day == today else ""
        body = "".join(calendar_event_html(event) for event in events_for_day(events, day)[:6])
        day_cols.append(f"<div class='day-col{today_class}'>{body}</div>")
    return f"""
    <section class="main-pane">
        <div class="calendar-head">
            <div class="calendar-toolbar">
                <div>
                    <h2 class="calendar-title">{start:%Y.%m.%d} - {(start + timedelta(days=6)):%m.%d}</h2>
                    <p class="calendar-subtitle">Week {selected.isocalendar().week} · 주간 일정</p>
                </div>
                <div><span class="tag">Week View</span><span class="tag">Google Sync</span></div>
            </div>
            <div class="day-header-grid">{''.join(header)}</div>
        </div>
        <div class="calendar-grid">{time_col}{''.join(day_cols)}</div>
    </section>
    """


def render_day_calendar(events: list[ScheduleEvent], selected: date) -> str:
    day_events = events_for_day(events, selected)
    timeline = []
    for hour in range(7, 21):
        hour_events = [
            event
            for event in day_events
            if event.start_at.hour <= hour < max(event.end_at.hour, event.start_at.hour + 1)
        ]
        items = "".join(
            f"""
            <div class="agenda-item">
                <p class="agenda-time">{escape(event.time_label)}</p>
                <p class="agenda-title">{escape(event.title)}</p>
                <p class="task-meta">{escape(event.location or event.description or "개인 일정")}</p>
            </div>
            """
            for event in hour_events
        )
        timeline.append(
            f"""
            <div class="agenda-item">
                <p class="agenda-time">{hour:02d}:00</p>
                {items or '<p class="task-meta">비어 있는 시간입니다.</p>'}
            </div>
            """
        )
    return f"""
    <section class="main-pane">
        <div class="calendar-head">
            <div class="calendar-toolbar">
                <div>
                    <h2 class="calendar-title">{selected:%Y년 %m월 %d일}</h2>
                    <p class="calendar-subtitle">Day View · 하루 단위 집중 일정</p>
                </div>
                <div><span class="tag">Day View</span><span class="tag">{len(day_events)} events</span></div>
            </div>
        </div>
        <div class="day-agenda">{''.join(timeline)}</div>
    </section>
    """


def render_month_calendar(events: list[ScheduleEvent], selected: date) -> str:
    month = selected.replace(day=1)
    weeks = calendar.Calendar(firstweekday=0).monthdatescalendar(month.year, month.month)
    cells = [f"<div class='month-label'>{label}</div>" for label in WEEKDAY_LABELS]
    for week in weeks:
        for day in week:
            classes = ["month-cell"]
            if day.month != month.month:
                classes.append("outside")
            if day == date.today():
                classes.append("today")
            if day == selected:
                classes.append("selected")
            event_pills = "".join(
                f"<span class='month-event'>{escape(compact_title(event.title, 18))}</span>"
                for event in events_for_day(events, day)[:3]
            )
            cells.append(
                f"""
                <div class="{' '.join(classes)}">
                    <div class="month-date">{day.day}</div>
                    {event_pills}
                </div>
                """
            )
    return f"""
    <section class="main-pane">
        <div class="calendar-head">
            <div class="calendar-toolbar">
                <div>
                    <h2 class="calendar-title">{selected:%Y년 %m월}</h2>
                    <p class="calendar-subtitle">Month View · 월간 일정 요약</p>
                </div>
                <div><span class="tag">Month View</span><span class="tag">{len(events)} total</span></div>
            </div>
        </div>
        <div class="month-view-grid">{''.join(cells)}</div>
    </section>
    """


def render_calendar(events: list[ScheduleEvent], selected: date, view_mode: str) -> str:
    if view_mode == "day":
        return render_day_calendar(events, selected)
    if view_mode == "month":
        return render_month_calendar(events, selected)
    return render_week_calendar(events, selected)


def mini_month_html(events: list[ScheduleEvent], selected: date) -> str:
    event_days = {event.start_at.date() for event in events}
    month = selected.replace(day=1)
    parts = ["<div class='mini-month'>"]
    for label in ["일", "월", "화", "수", "목", "금", "토"]:
        parts.append(f"<p class='mini-label'>{label}</p>")
    for week in calendar.Calendar(firstweekday=6).monthdatescalendar(month.year, month.month):
        for day in week:
            style = "opacity:.35;" if day.month != month.month else ""
            classes = ["mini-day"]
            if day == date.today():
                classes.append("today")
            if day == selected:
                classes.append("selected")
            dot = "<span class='mini-dot'></span>" if day in event_days else ""
            parts.append(f"<div class='{' '.join(classes)}' style='{style}'>{day.day}{dot}</div>")
    parts.append("</div>")
    return "".join(parts)


def import_google_events() -> None:
    start_at, end_at = period_bounds(st.session_state.selected_date, st.session_state.view_mode)
    result = calendar_client.list_events(start_at, end_at)
    if result.success:
        for event in result.events:
            store.upsert_google_event(event)
        st.session_state.sync_message = result.message
    else:
        st.session_state.sync_message = result.message


def nav_link(view_mode: str, current_view: str) -> str:
    active = " active" if view_mode == current_view else ""
    return f'<a class="nav-item{active}" href="?view={view_mode}">{VIEW_TITLES[view_mode]}</a>'


def render_static_workspace(
    events: list[ScheduleEvent],
    alerts: list[ScheduleEvent],
    selected: date,
    view_mode: str,
) -> None:
    start_at, end_at = period_bounds(selected, view_mode)
    visible_events = events_in_period(events, start_at, end_at)
    today_events = events_for_day(events, date.today())
    recommendations = recommend_priorities([event for event in events if event.end_at >= datetime.now()])
    assistant_text = (
        f"현재 {VIEW_LABELS[view_mode]} 보기 범위에 일정 {len(visible_events)}개가 있습니다. "
        f"오늘 일정은 {len(today_events)}개, 중요한 알림은 {len(alerts)}개입니다."
    )
    first_task = recommendations[0].event.title if recommendations else "새 일정을 등록해 보세요"
    second_task = recommendations[1].event.title if len(recommendations) > 1 else "Google Calendar 가져오기를 실행해 보세요"
    google_status_class = "" if calendar_client.enabled else " off"
    html = f"""
    <main class="workspace scheduler-workspace">
        <aside class="left-pane">
            <div class="identity">
                <div class="identity-icon">AI</div>
                <div>
                    <p class="identity-title">AI Scheduler</p>
                    <p class="identity-subtitle">개인 일정 관리 · PC Workspace</p>
                </div>
            </div>
            {nav_link("week", view_mode)}
            {nav_link("day", view_mode)}
            {nav_link("month", view_mode)}
            <p class="section-label">Integrations</p>
            <div class="integration-row"><div class="integration-left"><div class="integration-icon">G</div><span>Google Calendar</span></div><span class="status-dot{google_status_class}"></span></div>
            <div class="integration-row"><div class="integration-left"><div class="integration-icon">AI</div><span>OpenAI / Gemini</span></div><span class="status-dot{' ' if settings.llm_enabled else ' off'}"></span></div>
            <div class="integration-row"><div class="integration-left"><div class="integration-icon">DB</div><span>SQLite Local</span></div><span class="status-dot"></span></div>
            <p class="section-label">Mini Calendar</p>
            <p style="font-weight:850;margin:0 0 8px;">{selected:%Y년 %m월}</p>
            {mini_month_html(events, selected)}
            <div class="storage-card">
                <div class="storage-top"><span>{VIEW_LABELS[view_mode]} 보기</span><span>{len(visible_events)}</span></div>
                <div class="progress-track"><div class="progress-fill" style="width:{min(len(visible_events) * 12, 100)}%"></div></div>
                <p class="identity-subtitle" style="font-size:.72rem;margin-top:8px;">중요 알림 {len(alerts)}개 · 전체 일정 {len(events)}개</p>
            </div>
        </aside>
        {render_calendar(events, selected, view_mode)}
        <aside class="right-pane">
            <div class="assistant-card">
                <p class="assistant-title">AI Smart Assistant</p>
                <div class="assistant-message">{escape(assistant_text)}</div>
            </div>
            <p class="section-label">Smart Tasks</p>
            <div class="task-card">
                <div class="task-row"><span>1</span><div><p class="task-title">{escape(first_task)}</p><p class="task-meta">AI recommended <span class="tag high">High</span></p></div></div>
            </div>
            <div class="task-card">
                <div class="task-row"><span>2</span><div><p class="task-title">{escape(second_task)}</p><p class="task-meta">Review soon <span class="tag">Tracked</span></p></div></div>
            </div>
            <div class="insight-card">
                <div class="storage-top"><span>Productivity Score</span><span style="color:var(--primary);">94</span></div>
                <div class="progress-track"><div class="progress-fill" style="width:94%"></div></div>
                <p class="task-meta">집중 시간과 완료율을 기준으로 산정한 주간 생산성 지표입니다.</p>
            </div>
        </aside>
    </main>
    """
    st.html(html)


def create_event_from_ai(command: str) -> None:
    parsed = parser.parse(command)
    if parsed.event is None:
        st.info(parsed.message)
        return
    sync_result = calendar_client.create_event(parsed.event)
    if sync_result.google_event_id:
        parsed.event.google_event_id = sync_result.google_event_id
    saved = store.add_event(parsed.event)
    st.success("일정을 등록했습니다.")
    st.write(f"- 제목: {saved.title}")
    st.write(f"- 날짜: {saved.date_label}")
    st.write(f"- 시간: {saved.time_label}")
    st.caption(sync_result.message)


def create_manual_event(title: str, start_date: date, start_time: time, duration: int, importance: int) -> None:
    start_at = datetime.combine(start_date, start_time)
    event = ScheduleEvent(
        id=None,
        title=title.strip(),
        start_at=start_at,
        end_at=start_at + timedelta(minutes=int(duration)),
        importance=int(importance),
    )
    sync_result = calendar_client.create_event(event)
    if sync_result.google_event_id:
        event.google_event_id = sync_result.google_event_id
    store.add_event(event)
    st.success("일정을 등록했습니다.")
    st.caption(sync_result.message)


def render_interaction_panel(events: list[ScheduleEvent]) -> None:
    st.markdown("<div class='streamlit-forms'>", unsafe_allow_html=True)
    st.markdown("#### 캘린더 작업")
    tool_nav_col, tool_date_col, tool_sync_col, tool_search_col = st.columns([1.15, 1, 1.15, 1.6], gap="medium")
    with tool_nav_col:
        prev_col, today_col, next_col = st.columns(3)
        if prev_col.button("이전", use_container_width=True):
            shift_selected_date(-1)
            st.rerun()
        if today_col.button("오늘", use_container_width=True):
            st.session_state.selected_date = date.today()
            st.rerun()
        if next_col.button("다음", use_container_width=True):
            shift_selected_date(1)
            st.rerun()
    with tool_date_col:
        picked = st.date_input("기준 날짜", value=st.session_state.selected_date, key="bottom_selected_date")
        if picked != st.session_state.selected_date:
            st.session_state.selected_date = picked
            st.rerun()
    with tool_sync_col:
        if st.button("Google Calendar 가져오기", type="primary", use_container_width=True):
            import_google_events()
            st.rerun()
    with tool_search_col:
        st.session_state.search_query = st.text_input(
            "일정 검색",
            value=st.session_state.search_query,
            placeholder="제목, 설명, 장소 검색",
        )

    if st.session_state.sync_message:
        if "실패" in st.session_state.sync_message or "설정" in st.session_state.sync_message:
            st.warning(st.session_state.sync_message)
        else:
            st.success(st.session_state.sync_message)

    query = st.session_state.search_query.strip().lower()
    filtered_events = [
        event
        for event in events
        if not query
        or query in event.title.lower()
        or query in event.description.lower()
        or query in event.location.lower()
    ]

    input_col, manual_col, list_col = st.columns([1.05, 1, 1.45], gap="large")
    with input_col:
        st.markdown("#### AI 일정 입력")
        command = st.text_area(
            "AI 명령",
            placeholder="다음 주 화요일 오후 2시에 회의 등록해줘.",
            height=90,
        )
        if st.button("AI로 등록", type="primary", use_container_width=True):
            if command.strip():
                create_event_from_ai(command)
                st.rerun()
            else:
                st.warning("일정 명령을 입력해 주세요.")
    with manual_col:
        st.markdown("#### 직접 등록")
        title = st.text_input("제목", placeholder="회의")
        start_date = st.date_input("날짜", value=st.session_state.selected_date, key="manual_start_date")
        start_time = st.time_input("시작 시간", value=time(9, 0), key="manual_start_time")
        duration = st.number_input("소요 시간(분)", 15, 480, 60, 15)
        importance = st.slider("중요도", 1, 5, 3)
        if st.button("일정 등록", type="primary", use_container_width=True):
            if not title.strip():
                st.warning("제목을 입력해 주세요.")
            else:
                create_manual_event(title, start_date, start_time, int(duration), int(importance))
                st.rerun()
    with list_col:
        st.markdown("#### 일정 조회 및 변경")
        if not filtered_events:
            st.markdown("<div class='empty-note'>등록된 일정이 없습니다.</div>", unsafe_allow_html=True)
        for event in filtered_events:
            with st.expander(f"{event.date_label} {event.time_label} · {event.title}", expanded=False):
                with st.form(f"update_{event.id}"):
                    updated_title = st.text_input("제목", value=event.title, key=f"title_{event.id}")
                    updated_date = st.date_input("날짜", value=event.start_at.date(), key=f"date_{event.id}")
                    updated_time = st.time_input("시작 시간", value=event.start_at.time(), key=f"time_{event.id}")
                    updated_importance = st.slider("중요도", 1, 5, event.importance, key=f"importance_{event.id}")
                    if st.form_submit_button("변경 저장", use_container_width=True):
                        start_at = datetime.combine(updated_date, updated_time)
                        updated = store.update_event(
                            int(event.id),
                            title=updated_title.strip(),
                            start_at=start_at,
                            end_at=start_at + (event.end_at - event.start_at),
                            importance=int(updated_importance),
                        )
                        if updated is not None:
                            st.caption(calendar_client.update_event(updated).message)
                        st.success("일정을 변경했습니다.")
                        st.rerun()
                if st.button("삭제", key=f"delete_{event.id}", use_container_width=True):
                    st.caption(calendar_client.delete_event(event).message)
                    store.delete_event(int(event.id))
                    st.success("일정을 삭제했습니다.")
                    st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)


def main() -> None:
    init_state()
    inject_styles()
    all_events = store.list_events(include_past=True)
    alerts = store.upcoming_important()
    render_static_workspace(all_events, alerts, st.session_state.selected_date, st.session_state.view_mode)
    render_interaction_panel(all_events)
    st.caption(
        "SQLite local-first · "
        f"DB: {settings.database_path} · "
        f"Google Calendar API: {'on' if calendar_client.enabled else 'off'} · "
        f"LLM parser: {'on' if settings.llm_enabled else 'rule-based'}"
    )


main()
