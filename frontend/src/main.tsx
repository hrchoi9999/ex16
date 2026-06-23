import React, { useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import { Bot, CalendarDays, ExternalLink, RefreshCw, Search } from "lucide-react";
import "./styles.css";

type ScheduleEvent = {
  id: number | null;
  title: string;
  start_at: string;
  end_at: string;
  description: string;
  location: string;
  importance: number;
  source: string;
  source_url: string;
  sync_status: string;
};

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";
const WEEKDAYS = ["\uC6D4", "\uD654", "\uC218", "\uBAA9", "\uAE08", "\uD1A0", "\uC77C"];
const TEXT = {
  serviceName: "\uAC1C\uC778 \uC77C\uC815 \uAD00\uB9AC",
  monthView: "\uC6D4 \uBCF4\uAE30",
  weekView: "\uC8FC \uBCF4\uAE30",
  dayView: "\uC77C \uBCF4\uAE30",
  loading: "\uC77C\uC815\uC744 \uBD88\uB7EC\uC624\uB294 \uC911\uC785\uB2C8\uB2E4.",
  selectedDayEmpty: "\uC120\uD0DD\uD55C \uB0A0\uC9DC\uC5D0 \uC77C\uC815\uC774 \uC5C6\uC2B5\uB2C8\uB2E4.",
  detail: "\uC0C1\uC138",
  openUrl: "\uC6D0\uBB38 URL \uC5F4\uAE30",
  taskMenu: "\uC791\uC5C5 \uBA54\uB274",
  today: "\uC624\uB298",
  eventCount: "\uC77C\uC815",
  items: "\uAC1C",
  aiNext: "AI \uCC44\uD305 \uC5F0\uACB0\uC740 \uB2E4\uC74C sprint\uC5D0\uC11C \uC774\uC2DD\uD569\uB2C8\uB2E4.",
};

function formatDateKey(date: Date): string {
  const year = date.getFullYear();
  const month = `${date.getMonth() + 1}`.padStart(2, "0");
  const day = `${date.getDate()}`.padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function parseDateTime(value: string): Date {
  return new Date(value);
}

function monthLabel(date: Date): string {
  return `${date.getFullYear()}\uB144 ${`${date.getMonth() + 1}`.padStart(2, "0")}\uC6D4`;
}

function addMonths(date: Date, delta: number): Date {
  return new Date(date.getFullYear(), date.getMonth() + delta, 1);
}

function startOfMonthGrid(date: Date): Date {
  const first = new Date(date.getFullYear(), date.getMonth(), 1);
  const mondayBasedDay = (first.getDay() + 6) % 7;
  const start = new Date(first);
  start.setDate(first.getDate() - mondayBasedDay);
  return start;
}

function buildMonthDays(date: Date): Date[] {
  const start = startOfMonthGrid(date);
  return Array.from({ length: 42 }, (_, index) => {
    const day = new Date(start);
    day.setDate(start.getDate() + index);
    return day;
  });
}

function isSameDay(a: Date, b: Date): boolean {
  return formatDateKey(a) === formatDateKey(b);
}

function eventsForDay(events: ScheduleEvent[], day: Date): ScheduleEvent[] {
  const dayStart = new Date(day.getFullYear(), day.getMonth(), day.getDate(), 0, 0, 0);
  const dayEnd = new Date(day.getFullYear(), day.getMonth(), day.getDate(), 23, 59, 59);
  return events
    .filter((event) => parseDateTime(event.start_at) <= dayEnd && parseDateTime(event.end_at) >= dayStart)
    .sort((a, b) => parseDateTime(a.start_at).getTime() - parseDateTime(b.start_at).getTime());
}

function eventTone(event: ScheduleEvent): string {
  const isSeoul50Plus =
    event.source.includes("\uC11C\uC6B850\uD50C\uB7EC\uC2A4") ||
    event.description.includes("\uC11C\uC6B850\uD50C\uB7EC\uC2A4");
  if (isSeoul50Plus) {
    return "seoul50plus";
  }
  if (event.source_url && (event.title.startsWith("[\uB9C8\uAC10]") || event.source !== "local")) {
    return "deadline";
  }
  return "general";
}

function compactTitle(title: string): string {
  return title.length > 38 ? `${title.slice(0, 37)}...` : title;
}

function App() {
  const today = useMemo(() => new Date(), []);
  const [month, setMonth] = useState(() => new Date(today.getFullYear(), today.getMonth(), 1));
  const [selectedDate, setSelectedDate] = useState(today);
  const [events, setEvents] = useState<ScheduleEvent[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const monthDays = useMemo(() => buildMonthDays(month), [month]);
  const rangeStart = formatDateKey(monthDays[0]);
  const rangeEnd = formatDateKey(monthDays[monthDays.length - 1]);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setError("");

    fetch(`${API_BASE_URL}/events/range?start=${rangeStart}&end=${rangeEnd}`, {
      signal: controller.signal,
    })
      .then((response) => {
        if (!response.ok) {
          throw new Error(`API response error: ${response.status}`);
        }
        return response.json() as Promise<ScheduleEvent[]>;
      })
      .then(setEvents)
      .catch((caught: Error) => {
        if (caught.name !== "AbortError") {
          setError(caught.message);
        }
      })
      .finally(() => setLoading(false));

    return () => controller.abort();
  }, [rangeStart, rangeEnd]);

  const visibleEvents = events.filter((event) => {
    const start = parseDateTime(event.start_at);
    return start.getFullYear() === month.getFullYear() && start.getMonth() === month.getMonth();
  });
  const selectedEvents = eventsForDay(events, selectedDate);

  return (
    <main className="shell">
      <aside className="sidebar">
        <div className="brand-row">
          <div className="brand-mark">AI</div>
          <strong>{TEXT.serviceName}</strong>
        </div>
        <p className="section-label">Calendar View</p>
        <nav>
          <button className="active">{TEXT.monthView}</button>
          <button disabled>{TEXT.weekView}</button>
          <button disabled>{TEXT.dayView}</button>
        </nav>
        <p className="section-label">Migration</p>
        <div className="status-card">
          <CalendarDays size={18} />
          <span>React read-only calendar</span>
        </div>
      </aside>

      <section className="workspace">
        <header className="calendar-header">
          <button aria-label="Previous month" onClick={() => setMonth((current) => addMonths(current, -1))}>
            &lsaquo;
          </button>
          <div className="calendar-heading">
            <h1>{monthLabel(month)}</h1>
            <p>
              {TEXT.monthView} · {TEXT.eventCount} {visibleEvents.length}
              {TEXT.items}
            </p>
          </div>
          <button aria-label="Next month" onClick={() => setMonth((current) => addMonths(current, 1))}>
            &rsaquo;
          </button>
        </header>

        {error ? <div className="notice error">{error}</div> : null}
        {loading ? (
          <div className="notice">
            <RefreshCw size={16} /> {TEXT.loading}
          </div>
        ) : null}

        <div className="month-grid">
          {WEEKDAYS.map((weekday) => (
            <div className={`weekday ${weekday === "\uD1A0" || weekday === "\uC77C" ? "weekend" : ""}`} key={weekday}>
              {weekday}
            </div>
          ))}
          {monthDays.map((day) => {
            const dayEvents = eventsForDay(events, day);
            const inMonth = day.getMonth() === month.getMonth();
            const selected = isSameDay(day, selectedDate);
            const weekend = day.getDay() === 0 || day.getDay() === 6;
            return (
              <button
                className={`day-cell ${inMonth ? "" : "muted"} ${selected ? "selected" : ""}`}
                key={formatDateKey(day)}
                onClick={() => setSelectedDate(day)}
              >
                <span className={`day-number ${weekend ? "weekend" : ""}`}>
                  {day.getDate()}
                  {isSameDay(day, today) ? ` ${TEXT.today}` : ""}
                </span>
                <span className="day-events">
                  {dayEvents.slice(0, 4).map((event) => (
                    <span className={`event-line ${eventTone(event)}`} key={`${event.id ?? event.source_url}-${event.title}`}>
                      {compactTitle(event.title)}
                    </span>
                  ))}
                  {dayEvents.length > 4 ? (
                    <span className="more-line">
                      +{dayEvents.length - 4}
                      {TEXT.items}
                    </span>
                  ) : null}
                </span>
              </button>
            );
          })}
        </div>
      </section>

      <aside className="task-panel">
        <div className="panel-tools">
          <Search size={18} />
          <span>{TEXT.taskMenu}</span>
        </div>
        <section className="detail-panel">
          <h2>
            {formatDateKey(selectedDate)} {TEXT.detail}
          </h2>
          {selectedEvents.length === 0 ? (
            <p className="empty">{TEXT.selectedDayEmpty}</p>
          ) : (
            selectedEvents.map((event) => (
              <article className="detail-card" key={`${event.id ?? event.source_url}-${event.title}`}>
                <strong className={eventTone(event)}>{event.title}</strong>
                <p>
                  {parseDateTime(event.start_at).toLocaleTimeString("ko-KR", { hour: "2-digit", minute: "2-digit" })} ·{" "}
                  {event.source}
                </p>
                {event.description ? <p>{event.description}</p> : null}
                {event.source_url ? (
                  <a href={event.source_url} target="_blank" rel="noreferrer">
                    {TEXT.openUrl} <ExternalLink size={14} />
                  </a>
                ) : null}
              </article>
            ))
          )}
        </section>
        <div className="chat-card">
          <Bot size={18} />
          <span>{TEXT.aiNext}</span>
        </div>
      </aside>
    </main>
  );
}

createRoot(document.getElementById("root") as HTMLElement).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
