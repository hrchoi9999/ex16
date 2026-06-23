import React, { FormEvent, useCallback, useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import { Bot, ExternalLink, Pencil, RefreshCw, Trash2 } from "lucide-react";
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

type ActiveUser = {
  id: number | null;
  email: string;
  display_name: string;
  provider: string;
  linked_at: string;
  auto_sync: boolean;
};

type Candidate = {
  id: number | null;
  source: string;
  category: string;
  title: string;
  recruitment_period: string;
  url: string;
  status: string;
  collected_at: string;
  selected: boolean;
};

type EventFormState = {
  title: string;
  start_at: string;
  end_at: string;
  description: string;
  location: string;
  importance: number;
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
  createTitle: "\uC120\uD0DD \uB0A0\uC9DC \uC77C\uC815 \uB4F1\uB85D",
  editTitle: "\uC77C\uC815 \uC218\uC815",
  title: "\uC81C\uBAA9",
  startAt: "\uC2DC\uC791",
  endAt: "\uC885\uB8CC",
  location: "\uC7A5\uC18C",
  importance: "\uC911\uC694\uB3C4",
  description: "\uC124\uBA85",
  save: "\uC77C\uC815 \uB4F1\uB85D",
  update: "\uC218\uC815 \uC800\uC7A5",
  cancel: "\uCDE8\uC18C",
  edit: "\uC218\uC815",
  delete: "\uC0AD\uC81C",
  googleAccount: "Google Account",
  googleHelp: "Google \uB85C\uADF8\uC778\uC73C\uB85C \uCE98\uB9B0\uB354\uB97C \uC5F0\uACB0\uD558\uC138\uC694.",
  googleLinked: "\uC5F0\uACB0\uB428",
  googleNext: "Google OAuth \uC791\uC5C5\uC740 \uB2E4\uC74C sprint\uC5D0\uC11C \uC774\uC2DD\uD569\uB2C8\uB2E4.",
  interestSites: "Interest Sites",
  collectNow: "\uAD00\uC2EC \uC0AC\uC774\uD2B8 \uC9C0\uAE08 \uC218\uC9D1",
  collecting: "\uC218\uC9D1 \uC911...",
  candidates: "\uC218\uC9D1 \uD6C4\uBCF4",
  noCandidates: "\uC218\uC9D1\uB41C \uD6C4\uBCF4\uAC00 \uC5C6\uC2B5\uB2C8\uB2E4.",
  miniCalendar: "Mini Calendar",
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

function toDateTimeLocalValue(date: Date): string {
  const year = date.getFullYear();
  const month = `${date.getMonth() + 1}`.padStart(2, "0");
  const day = `${date.getDate()}`.padStart(2, "0");
  const hour = `${date.getHours()}`.padStart(2, "0");
  const minute = `${date.getMinutes()}`.padStart(2, "0");
  return `${year}-${month}-${day}T${hour}:${minute}`;
}

function newFormForDate(date: Date): EventFormState {
  const start = new Date(date.getFullYear(), date.getMonth(), date.getDate(), 9, 0, 0);
  const end = new Date(date.getFullYear(), date.getMonth(), date.getDate(), 10, 0, 0);
  return {
    title: "",
    start_at: toDateTimeLocalValue(start),
    end_at: toDateTimeLocalValue(end),
    description: "",
    location: "",
    importance: 3,
  };
}

function formFromEvent(event: ScheduleEvent): EventFormState {
  return {
    title: event.title,
    start_at: toDateTimeLocalValue(parseDateTime(event.start_at)),
    end_at: toDateTimeLocalValue(parseDateTime(event.end_at)),
    description: event.description,
    location: event.location,
    importance: event.importance,
  };
}

function apiDateTime(value: string): string {
  return value.length === 16 ? `${value}:00` : value;
}

function App() {
  const today = useMemo(() => new Date(), []);
  const [month, setMonth] = useState(() => new Date(today.getFullYear(), today.getMonth(), 1));
  const [selectedDate, setSelectedDate] = useState(today);
  const [events, setEvents] = useState<ScheduleEvent[]>([]);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [collecting, setCollecting] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [activeUser, setActiveUser] = useState<ActiveUser | null>(null);
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [editingEventId, setEditingEventId] = useState<number | null>(null);
  const [form, setForm] = useState<EventFormState>(() => newFormForDate(today));

  const monthDays = useMemo(() => buildMonthDays(month), [month]);
  const rangeStart = formatDateKey(monthDays[0]);
  const rangeEnd = formatDateKey(monthDays[monthDays.length - 1]);

  const loadEvents = useCallback(
    async (signal?: AbortSignal) => {
      setLoading(true);
      setError("");
      try {
        const response = await fetch(`${API_BASE_URL}/events/range?start=${rangeStart}&end=${rangeEnd}`, { signal });
        if (!response.ok) {
          throw new Error(`API response error: ${response.status}`);
        }
        const payload = (await response.json()) as ScheduleEvent[];
        setEvents(payload);
      } catch (caught) {
        const errorObject = caught as Error;
        if (errorObject.name !== "AbortError") {
          setError(errorObject.message);
        }
      } finally {
        setLoading(false);
      }
    },
    [rangeEnd, rangeStart],
  );

  const loadSidebarData = useCallback(async () => {
    try {
      const [userResponse, candidatesResponse] = await Promise.all([
        fetch(`${API_BASE_URL}/user/active`),
        fetch(`${API_BASE_URL}/candidates`),
      ]);
      if (userResponse.ok) {
        setActiveUser((await userResponse.json()) as ActiveUser | null);
      }
      if (candidatesResponse.ok) {
        setCandidates((await candidatesResponse.json()) as Candidate[]);
      }
    } catch (caught) {
      setError((caught as Error).message);
    }
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    void loadEvents(controller.signal);
    return () => controller.abort();
  }, [loadEvents]);

  useEffect(() => {
    void loadSidebarData();
  }, [loadSidebarData]);

  useEffect(() => {
    if (editingEventId === null) {
      setForm(newFormForDate(selectedDate));
    }
  }, [editingEventId, selectedDate]);

  const visibleEvents = events.filter((event) => {
    const start = parseDateTime(event.start_at);
    return start.getFullYear() === month.getFullYear() && start.getMonth() === month.getMonth();
  });
  const selectedEvents = eventsForDay(events, selectedDate);
  const miniDays = useMemo(() => buildMonthDays(month), [month]);

  async function collectCandidates() {
    setCollecting(true);
    setError("");
    setMessage("");
    try {
      const response = await fetch(`${API_BASE_URL}/candidates/collect`, { method: "POST" });
      if (!response.ok) {
        throw new Error(`API response error: ${response.status}`);
      }
      const payload = (await response.json()) as { message: string; candidates: Candidate[] };
      setCandidates(payload.candidates);
      setMessage(payload.message);
    } catch (caught) {
      setError((caught as Error).message);
    } finally {
      setCollecting(false);
    }
  }

  async function submitForm(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSaving(true);
    setError("");
    setMessage("");

    const payload = {
      title: form.title.trim(),
      start_at: apiDateTime(form.start_at),
      end_at: apiDateTime(form.end_at),
      description: form.description.trim(),
      location: form.location.trim(),
      importance: Number(form.importance),
    };

    try {
      const response = await fetch(`${API_BASE_URL}/events${editingEventId === null ? "" : `/${editingEventId}`}`, {
        method: editingEventId === null ? "POST" : "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!response.ok) {
        throw new Error(`API response error: ${response.status}`);
      }
      const saved = (await response.json()) as ScheduleEvent;
      const savedDate = parseDateTime(saved.start_at);
      setSelectedDate(savedDate);
      setMonth(new Date(savedDate.getFullYear(), savedDate.getMonth(), 1));
      setEditingEventId(null);
      setForm(newFormForDate(savedDate));
      setMessage(editingEventId === null ? "\uC77C\uC815\uC744 \uB4F1\uB85D\uD588\uC2B5\uB2C8\uB2E4." : "\uC77C\uC815\uC744 \uC218\uC815\uD588\uC2B5\uB2C8\uB2E4.");
      await loadEvents();
    } catch (caught) {
      setError((caught as Error).message);
    } finally {
      setSaving(false);
    }
  }

  async function deleteEvent(eventId: number) {
    setSaving(true);
    setError("");
    setMessage("");
    try {
      const response = await fetch(`${API_BASE_URL}/events/${eventId}`, { method: "DELETE" });
      if (!response.ok) {
        throw new Error(`API response error: ${response.status}`);
      }
      if (editingEventId === eventId) {
        setEditingEventId(null);
        setForm(newFormForDate(selectedDate));
      }
      setMessage("\uC77C\uC815\uC744 \uC0AD\uC81C\uD588\uC2B5\uB2C8\uB2E4.");
      await loadEvents();
    } catch (caught) {
      setError((caught as Error).message);
    } finally {
      setSaving(false);
    }
  }

  function startEditing(event: ScheduleEvent) {
    if (event.id === null) {
      return;
    }
    setEditingEventId(event.id);
    setForm(formFromEvent(event));
    setMessage("");
  }

  function cancelEditing() {
    setEditingEventId(null);
    setForm(newFormForDate(selectedDate));
  }

  return (
    <main className="shell">
      <aside className="sidebar">
        <div className="brand-row">
          <div className="brand-mark">AI</div>
          <strong>{TEXT.serviceName}</strong>
        </div>
        <p className="section-label">Calendar View</p>
        <nav className="view-switcher" aria-label="Calendar view selector">
          <button className="active" aria-label={TEXT.monthView}>
            {"\uC6D4"}
          </button>
          <button disabled aria-label={TEXT.weekView}>
            {"\uC8FC"}
          </button>
          <button disabled aria-label={TEXT.dayView}>
            {"\uC77C"}
          </button>
        </nav>

        <p className="section-label">{TEXT.googleAccount}</p>
        <div className="account-card">
          <span className={`status-dot ${activeUser ? "online" : ""}`} />
          <div>
            <strong>{activeUser?.email ?? "google-user"}</strong>
            <p>{activeUser ? TEXT.googleLinked : TEXT.googleHelp}</p>
          </div>
        </div>
        <button className="secondary-action" disabled>
          {TEXT.googleNext}
        </button>

        <p className="section-label">{TEXT.interestSites}</p>
        <button className="secondary-action" disabled={collecting} onClick={() => void collectCandidates()}>
          {collecting ? TEXT.collecting : TEXT.collectNow}
        </button>
        <p className="sidebar-caption">
          {candidates.length}
          {TEXT.candidates}
        </p>
        <div className="candidate-preview">
          {candidates.length === 0 ? (
            <span>{TEXT.noCandidates}</span>
          ) : (
            candidates.slice(0, 3).map((candidate) => (
              <a href={candidate.url} key={`${candidate.id ?? candidate.url}-${candidate.title}`} target="_blank" rel="noreferrer">
                {compactTitle(candidate.title)}
              </a>
            ))
          )}
        </div>

        <p className="section-label">{TEXT.miniCalendar}</p>
        <div className="mini-calendar">
          <strong>{monthLabel(month)}</strong>
          <div className="mini-weekdays">
            {WEEKDAYS.map((weekday) => (
              <span className={weekday === "\uD1A0" || weekday === "\uC77C" ? "weekend" : ""} key={weekday}>
                {weekday}
              </span>
            ))}
          </div>
          <div className="mini-grid">
            {miniDays.map((day) => {
              const inMonth = day.getMonth() === month.getMonth();
              const selected = isSameDay(day, selectedDate);
              const hasEvent = eventsForDay(events, day).length > 0;
              const weekend = day.getDay() === 0 || day.getDay() === 6;
              return (
                <button
                  className={`${inMonth ? "" : "muted"} ${selected ? "selected" : ""} ${hasEvent ? "has-event" : ""} ${weekend ? "weekend" : ""}`}
                  key={`mini-${formatDateKey(day)}`}
                  onClick={() => {
                    setSelectedDate(day);
                    setMonth(new Date(day.getFullYear(), day.getMonth(), 1));
                    setEditingEventId(null);
                    setMessage("");
                  }}
                >
                  {day.getDate()}
                </button>
              );
            })}
          </div>
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
        {message ? <div className="notice success">{message}</div> : null}
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
                onClick={() => {
                  setSelectedDate(day);
                  setEditingEventId(null);
                  setMessage("");
                }}
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
        <h2 className="task-title">{TEXT.taskMenu}</h2>
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
                <div className="card-actions">
                  {event.source_url ? (
                    <a href={event.source_url} target="_blank" rel="noreferrer">
                      {TEXT.openUrl} <ExternalLink size={14} />
                    </a>
                  ) : null}
                  {event.id !== null ? (
                    <>
                      <button type="button" onClick={() => startEditing(event)}>
                        <Pencil size={14} /> {TEXT.edit}
                      </button>
                      <button type="button" className="danger-button" onClick={() => void deleteEvent(event.id as number)}>
                        <Trash2 size={14} /> {TEXT.delete}
                      </button>
                    </>
                  ) : null}
                </div>
              </article>
            ))
          )}

          <form className="event-form" onSubmit={(event) => void submitForm(event)}>
            <h3>{editingEventId === null ? TEXT.createTitle : TEXT.editTitle}</h3>
            <label>
              {TEXT.title}
              <input
                required
                value={form.title}
                onChange={(event) => setForm((current) => ({ ...current, title: event.target.value }))}
              />
            </label>
            <label>
              {TEXT.startAt}
              <input
                required
                type="datetime-local"
                value={form.start_at}
                onChange={(event) => setForm((current) => ({ ...current, start_at: event.target.value }))}
              />
            </label>
            <label>
              {TEXT.endAt}
              <input
                required
                type="datetime-local"
                value={form.end_at}
                onChange={(event) => setForm((current) => ({ ...current, end_at: event.target.value }))}
              />
            </label>
            <label>
              {TEXT.location}
              <input
                value={form.location}
                onChange={(event) => setForm((current) => ({ ...current, location: event.target.value }))}
              />
            </label>
            <label>
              {TEXT.importance}
              <input
                min={1}
                max={5}
                type="number"
                value={form.importance}
                onChange={(event) => setForm((current) => ({ ...current, importance: Number(event.target.value) }))}
              />
            </label>
            <label>
              {TEXT.description}
              <textarea
                rows={3}
                value={form.description}
                onChange={(event) => setForm((current) => ({ ...current, description: event.target.value }))}
              />
            </label>
            <div className="form-actions">
              <button type="submit" disabled={saving}>
                {editingEventId === null ? TEXT.save : TEXT.update}
              </button>
              {editingEventId !== null ? (
                <button type="button" disabled={saving} onClick={cancelEditing}>
                  {TEXT.cancel}
                </button>
              ) : null}
            </div>
          </form>
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
