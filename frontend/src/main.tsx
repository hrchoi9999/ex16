import React, { FormEvent, useCallback, useEffect, useMemo, useRef, useState } from "react";
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

type ChatMessage = {
  id: number;
  role: "user" | "assistant";
  text: string;
};

type AiChatResponse = {
  answer: string;
  matched_event_ids: number[];
  intent: string;
  menu: string;
};

type ViewMode = "month" | "week" | "day";

type GoogleStatus = {
  enabled: boolean;
  linked: boolean;
  email: string;
  message: string;
};

type GoogleOAuthStartResponse = {
  enabled: boolean;
  success: boolean;
  message: string;
  authorization_url: string;
};

type GoogleImportResponse = {
  success: boolean;
  message: string;
  imported_count: number;
};

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";
const WEEKDAYS = ["\uC6D4", "\uD654", "\uC218", "\uBAA9", "\uAE08", "\uD1A0", "\uC77C"];
const KOREAN_FIXED_HOLIDAYS = new Set(["01-01", "03-01", "05-05", "06-06", "08-15", "10-03", "10-09", "12-25"]);
const KNOWN_PUBLIC_HOLIDAYS = new Set([
  "2026-01-01",
  "2026-02-16",
  "2026-02-17",
  "2026-02-18",
  "2026-03-02",
  "2026-05-05",
  "2026-05-25",
  "2026-06-03",
  "2026-06-06",
  "2026-08-15",
  "2026-09-24",
  "2026-09-25",
  "2026-09-26",
  "2026-10-05",
  "2026-10-09",
  "2026-12-25",
]);
const HOLIDAY_KEYWORDS = [
  "\uACF5\uD734\uC77C",
  "\uD734\uC77C",
  "\uC124\uB0A0",
  "\uCD94\uC11D",
  "\uC5B4\uB9B0\uC774\uB0A0",
  "\uBD80\uCC98\uB2D8",
  "\uD604\uCDA9\uC77C",
  "\uAD11\uBCF5\uC808",
  "\uAC1C\uCC9C\uC808",
  "\uD55C\uAE00\uB0A0",
  "\uC131\uD0C4\uC808",
  "\uC120\uAC70\uC77C",
];
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
  aiChat: "AI \uCC44\uD305",
  aiPlaceholder: "\uC608: \uC774\uBC88 \uC8FC \uBA74\uC811 \uC77C\uC815 \uC54C\uB824\uC918",
  send: "\uC804\uC1A1",
  asking: "\uD655\uC778 \uC911...",
  chatEmpty: "\uC544\uC9C1 AI \uCC44\uD305 \uB300\uD654\uAC00 \uC5C6\uC2B5\uB2C8\uB2E4. \uD558\uB2E8\uC5D0\uC11C \uC77C\uC815\uC744 \uC9C8\uBB38\uD574 \uBCF4\uC138\uC694.",
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
  googleHelp: "\uCD08\uB300\uB41C \uC0AC\uC6A9\uC790\uB9CC Google Calendar\uB97C \uC5F0\uACB0\uD560 \uC218 \uC788\uC2B5\uB2C8\uB2E4.",
  googleLinked: "\uC5F0\uB3D9\uB428",
  googleUnlinked: "\uBBF8\uC5F0\uB3D9",
  googleConnect: "Google \uACC4\uC815 \uC5F0\uB3D9",
  googleImport: "\uCE98\uB9B0\uB354 \uB2E4\uC2DC \uAC00\uC838\uC624\uAE30",
  googleDisconnect: "\uC5F0\uB3D9 \uD574\uC81C",
  googlePrivate: "\uCD08\uB300\uB41C \uC0AC\uC6A9\uC790\uB9CC \uC0AC\uC6A9\uD560 \uC218 \uC788\uC2B5\uB2C8\uB2E4.",
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

function dayLabel(date: Date): string {
  return `${date.getFullYear()}\uB144 ${`${date.getMonth() + 1}`.padStart(2, "0")}\uC6D4 ${`${date.getDate()}`.padStart(2, "0")}\uC77C`;
}

function shortDateLabel(date: Date): string {
  return `${`${date.getMonth() + 1}`.padStart(2, "0")}/${`${date.getDate()}`.padStart(2, "0")}`;
}

function addMonths(date: Date, delta: number): Date {
  return new Date(date.getFullYear(), date.getMonth() + delta, 1);
}

function addDays(date: Date, delta: number): Date {
  const next = new Date(date);
  next.setDate(date.getDate() + delta);
  return next;
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

function startOfWeek(date: Date): Date {
  const start = new Date(date.getFullYear(), date.getMonth(), date.getDate());
  const mondayBasedDay = (start.getDay() + 6) % 7;
  start.setDate(start.getDate() - mondayBasedDay);
  return start;
}

function buildWeekDays(date: Date): Date[] {
  const start = startOfWeek(date);
  return Array.from({ length: 7 }, (_, index) => addDays(start, index));
}

function isSameDay(a: Date, b: Date): boolean {
  return formatDateKey(a) === formatDateKey(b);
}

function eventsForDay(events: ScheduleEvent[], day: Date): ScheduleEvent[] {
  const holidayDates = holidayDatesFromEvents(events);
  return events
    .filter((event) => shouldShowEventOnDay(event, day, holidayDates))
    .sort((a, b) => parseDateTime(a.start_at).getTime() - parseDateTime(b.start_at).getTime());
}

function shouldShowEventOnDay(event: ScheduleEvent, day: Date, holidayDates: Set<string>): boolean {
  const dayKey = formatDateKey(day);
  const startKey = formatDateKey(parseDateTime(event.start_at));
  const endKey = formatDateKey(parseDateTime(event.end_at));
  if (dayKey < startKey || dayKey > endKey) {
    return false;
  }
  if (startKey === endKey) {
    return true;
  }
  if (isHolidayEvent(event) || isDeadlineEvent(event)) {
    return true;
  }
  return isBusinessDay(day, holidayDates);
}

function isDeadlineEvent(event: ScheduleEvent): boolean {
  return event.title.startsWith("[\uB9C8\uAC10]") || Boolean(event.source_url);
}

function isHolidayEvent(event: ScheduleEvent): boolean {
  const haystack = `${event.title} ${event.description} ${event.location} ${event.source}`.toLowerCase();
  return HOLIDAY_KEYWORDS.some((keyword) => haystack.includes(keyword.toLowerCase()));
}

function holidayDatesFromEvents(events: ScheduleEvent[]): Set<string> {
  const dates = new Set<string>();
  for (const event of events) {
    if (!isHolidayEvent(event)) {
      continue;
    }
    const current = parseDateTime(event.start_at);
    const end = parseDateTime(event.end_at);
    const day = new Date(current.getFullYear(), current.getMonth(), current.getDate());
    const last = new Date(end.getFullYear(), end.getMonth(), end.getDate());
    while (day <= last) {
      dates.add(formatDateKey(day));
      day.setDate(day.getDate() + 1);
    }
  }
  return dates;
}

function isBusinessDay(day: Date, holidayDates: Set<string>): boolean {
  return !isWeekendDate(day) && !isKnownHoliday(day, holidayDates);
}

function isWeekendDate(day: Date): boolean {
  return day.getDay() === 0 || day.getDay() === 6;
}

function isKnownHoliday(day: Date, holidayDates: Set<string>): boolean {
  const key = formatDateKey(day);
  const monthDay = key.slice(5);
  return holidayDates.has(key) || KOREAN_FIXED_HOLIDAYS.has(monthDay) || KNOWN_PUBLIC_HOLIDAYS.has(key);
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
  const [viewMode, setViewMode] = useState<ViewMode>("month");
  const [events, setEvents] = useState<ScheduleEvent[]>([]);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [collecting, setCollecting] = useState(false);
  const [chatting, setChatting] = useState(false);
  const [googleBusy, setGoogleBusy] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [activeUser, setActiveUser] = useState<ActiveUser | null>(null);
  const [googleStatus, setGoogleStatus] = useState<GoogleStatus | null>(null);
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [chatInput, setChatInput] = useState("");
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [editingEventId, setEditingEventId] = useState<number | null>(null);
  const [form, setForm] = useState<EventFormState>(() => newFormForDate(today));
  const chatEndRef = useRef<HTMLDivElement | null>(null);

  const monthDays = useMemo(() => buildMonthDays(month), [month]);
  const weekDays = useMemo(() => buildWeekDays(selectedDate), [selectedDate]);
  const viewDays = useMemo(() => {
    if (viewMode === "month") {
      return monthDays;
    }
    if (viewMode === "week") {
      return weekDays;
    }
    return [selectedDate];
  }, [monthDays, selectedDate, viewMode, weekDays]);
  const rangeStart = formatDateKey(viewDays[0]);
  const rangeEnd = formatDateKey(viewDays[viewDays.length - 1]);

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
      const [userResponse, googleResponse, candidatesResponse] = await Promise.all([
        fetch(`${API_BASE_URL}/user/active`),
        fetch(`${API_BASE_URL}/google/status`),
        fetch(`${API_BASE_URL}/candidates`),
      ]);
      if (userResponse.ok) {
        setActiveUser((await userResponse.json()) as ActiveUser | null);
      }
      if (googleResponse.ok) {
        setGoogleStatus((await googleResponse.json()) as GoogleStatus);
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

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [chatMessages, chatting]);

  const visibleEvents = events.filter((event) => {
    const startKey = formatDateKey(parseDateTime(event.start_at));
    const endKey = formatDateKey(parseDateTime(event.end_at));
    return startKey <= rangeEnd && endKey >= rangeStart;
  });
  const selectedEvents = eventsForDay(events, selectedDate);
  const miniDays = useMemo(() => buildMonthDays(month), [month]);
  const viewTitle = viewMode === "month" ? monthLabel(month) : viewMode === "week" ? `${shortDateLabel(weekDays[0])} - ${shortDateLabel(weekDays[6])}` : dayLabel(selectedDate);
  const activeViewLabel = viewMode === "month" ? TEXT.monthView : viewMode === "week" ? TEXT.weekView : TEXT.dayView;

  function changeView(nextMode: ViewMode) {
    setViewMode(nextMode);
    if (nextMode === "month") {
      setMonth(new Date(selectedDate.getFullYear(), selectedDate.getMonth(), 1));
    }
  }

  function moveView(delta: number) {
    if (viewMode === "month") {
      const nextMonth = addMonths(month, delta);
      setMonth(nextMonth);
      setSelectedDate(nextMonth);
      return;
    }
    const nextDate = addDays(selectedDate, viewMode === "week" ? delta * 7 : delta);
    setSelectedDate(nextDate);
    setMonth(new Date(nextDate.getFullYear(), nextDate.getMonth(), 1));
  }

  function selectCalendarDate(day: Date) {
    setSelectedDate(day);
    setMonth(new Date(day.getFullYear(), day.getMonth(), 1));
    setEditingEventId(null);
    setMessage("");
  }

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

  async function startGoogleConnect() {
    setGoogleBusy(true);
    setError("");
    setMessage("");
    try {
      const response = await fetch(`${API_BASE_URL}/google/oauth/start`, { method: "POST" });
      const payload = (await response.json()) as GoogleOAuthStartResponse;
      if (!response.ok || !payload.success || !payload.authorization_url) {
        throw new Error(payload.message || `API response error: ${response.status}`);
      }
      window.open(payload.authorization_url, "_blank", "noopener,noreferrer");
      setMessage("Google 로그인 화면을 열었습니다. 새 사용자만 최초 1회 권한 동의가 필요합니다.");
    } catch (caught) {
      setError((caught as Error).message);
    } finally {
      setGoogleBusy(false);
    }
  }

  async function importGoogleCalendar() {
    setGoogleBusy(true);
    setError("");
    setMessage("");
    try {
      const response = await fetch(`${API_BASE_URL}/google/import?start=${rangeStart}&end=${rangeEnd}`, { method: "POST" });
      const payload = (await response.json()) as GoogleImportResponse;
      if (!response.ok || !payload.success) {
        throw new Error(payload.message || `API response error: ${response.status}`);
      }
      setMessage(`${payload.imported_count}개 Google Calendar 일정을 가져왔습니다.`);
      await loadEvents();
      await loadSidebarData();
    } catch (caught) {
      setError((caught as Error).message);
    } finally {
      setGoogleBusy(false);
    }
  }

  async function disconnectGoogleAccount() {
    setGoogleBusy(true);
    setError("");
    setMessage("");
    try {
      const response = await fetch(`${API_BASE_URL}/google/account`, { method: "DELETE" });
      if (!response.ok) {
        throw new Error(`API response error: ${response.status}`);
      }
      setActiveUser(null);
      await loadSidebarData();
      setMessage("Google Calendar 연동을 해제했습니다.");
    } catch (caught) {
      setError((caught as Error).message);
    } finally {
      setGoogleBusy(false);
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

  async function submitChat(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const question = chatInput.trim();
    if (!question) {
      return;
    }

    const userMessage: ChatMessage = { id: Date.now(), role: "user", text: question };
    setChatMessages((current) => [...current, userMessage]);
    setChatInput("");
    setChatting(true);
    setError("");

    try {
      const response = await fetch(`${API_BASE_URL}/ai/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question }),
      });
      if (!response.ok) {
        throw new Error(`API response error: ${response.status}`);
      }
      const payload = (await response.json()) as AiChatResponse;
      setChatMessages((current) => [
        ...current,
        { id: Date.now() + 1, role: "assistant", text: payload.answer },
      ]);

      const matched = events.find((item) => item.id !== null && payload.matched_event_ids.includes(item.id));
      if (matched) {
        const matchedDate = parseDateTime(matched.start_at);
        setSelectedDate(matchedDate);
        setMonth(new Date(matchedDate.getFullYear(), matchedDate.getMonth(), 1));
      }
    } catch (caught) {
      setChatMessages((current) => [
        ...current,
        {
          id: Date.now() + 2,
          role: "assistant",
          text: `AI \uCC44\uD305 \uCC98\uB9AC\uC5D0 \uC2E4\uD328\uD588\uC2B5\uB2C8\uB2E4. ${(caught as Error).message}`,
        },
      ]);
    } finally {
      setChatting(false);
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
          <button className={viewMode === "month" ? "active" : ""} aria-label={TEXT.monthView} onClick={() => changeView("month")}>
            {"\uC6D4"}
          </button>
          <button className={viewMode === "week" ? "active" : ""} aria-label={TEXT.weekView} onClick={() => changeView("week")}>
            {"\uC8FC"}
          </button>
          <button className={viewMode === "day" ? "active" : ""} aria-label={TEXT.dayView} onClick={() => changeView("day")}>
            {"\uC77C"}
          </button>
        </nav>

        <p className="section-label">{TEXT.googleAccount}</p>
        <div className="account-card">
          <span className={`status-dot ${googleStatus?.linked || activeUser ? "online" : ""}`} />
          <div>
            <strong>{googleStatus?.linked || activeUser ? TEXT.googleLinked : TEXT.googleUnlinked}</strong>
            <p>{activeUser?.email || googleStatus?.email || TEXT.googleHelp}</p>
          </div>
        </div>
        <p className="sidebar-caption">{googleStatus?.message || TEXT.googlePrivate}</p>
        {googleStatus?.linked || activeUser ? (
          <div className="stacked-actions">
            <button className="secondary-action" disabled={googleBusy} onClick={() => void importGoogleCalendar()}>
              {googleBusy ? TEXT.loading : TEXT.googleImport}
            </button>
            <button className="secondary-action subtle" disabled={googleBusy} onClick={() => void disconnectGoogleAccount()}>
              {TEXT.googleDisconnect}
            </button>
          </div>
        ) : (
          <button className="secondary-action" disabled={googleBusy || googleStatus?.enabled === false} onClick={() => void startGoogleConnect()}>
            {googleBusy ? TEXT.loading : TEXT.googleConnect}
          </button>
        )}

        <p className="section-label">{TEXT.interestSites}</p>
        <button className="secondary-action" disabled={collecting} onClick={() => void collectCandidates()}>
          {collecting ? TEXT.collecting : TEXT.collectNow}
        </button>
        <p className="sidebar-caption">
          {candidates.length}
          {TEXT.candidates}
        </p>

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
                  onClick={() => selectCalendarDate(day)}
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
          <button aria-label="Previous period" onClick={() => moveView(-1)}>
            &lsaquo;
          </button>
          <div className="calendar-heading">
            <h1>{viewTitle}</h1>
            <p>
              {activeViewLabel} · {TEXT.eventCount} {visibleEvents.length}
              {TEXT.items}
            </p>
          </div>
          <button aria-label="Next period" onClick={() => moveView(1)}>
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

        {viewMode === "month" ? (
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
                  onClick={() => selectCalendarDate(day)}
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
        ) : viewMode === "week" ? (
          <div className="week-board">
            {weekDays.map((day) => {
              const dayEvents = eventsForDay(events, day);
              const selected = isSameDay(day, selectedDate);
              const weekend = isWeekendDate(day);
              return (
                <button
                  className={`week-column ${selected ? "selected" : ""} ${weekend ? "weekend" : ""}`}
                  key={`week-${formatDateKey(day)}`}
                  onClick={() => selectCalendarDate(day)}
                >
                  <span className="week-column-date">
                    {WEEKDAYS[(day.getDay() + 6) % 7]} {shortDateLabel(day)}
                    {isSameDay(day, today) ? ` ${TEXT.today}` : ""}
                  </span>
                  <span className="week-column-events">
                    {dayEvents.length === 0 ? (
                      <span className="week-empty">{TEXT.selectedDayEmpty}</span>
                    ) : (
                      dayEvents.map((event) => (
                        <span className={`event-line ${eventTone(event)}`} key={`${event.id ?? event.source_url}-${event.title}`}>
                          {compactTitle(event.title)}
                        </span>
                      ))
                    )}
                  </span>
                </button>
              );
            })}
          </div>
        ) : (
          <div className="day-board">
            <div className={`day-board-header ${isWeekendDate(selectedDate) ? "weekend" : ""}`}>{dayLabel(selectedDate)}</div>
            <div className="day-timeline">
              {selectedEvents.length === 0 ? (
                <p className="empty">{TEXT.selectedDayEmpty}</p>
              ) : (
                selectedEvents.map((event) => (
                  <article className={`day-timeline-event ${eventTone(event)}`} key={`day-${event.id ?? event.source_url}-${event.title}`}>
                    <span>
                      {parseDateTime(event.start_at).toLocaleTimeString("ko-KR", { hour: "2-digit", minute: "2-digit" })} -{" "}
                      {parseDateTime(event.end_at).toLocaleTimeString("ko-KR", { hour: "2-digit", minute: "2-digit" })}
                    </span>
                    <strong>{event.title}</strong>
                    {event.description ? <p>{event.description}</p> : null}
                  </article>
                ))
              )}
            </div>
          </div>
        )}
      </section>

      <aside className="task-panel">
        <h2 className="task-title">{TEXT.taskMenu}</h2>
        <section className="detail-panel">
          <h2>
            {formatDateKey(selectedDate)} {TEXT.detail}
          </h2>
          <section className="chat-thread" aria-live="polite">
            <h3>{TEXT.aiChat}</h3>
            {chatMessages.length === 0 ? (
              <p className="empty">{TEXT.chatEmpty}</p>
            ) : (
              chatMessages.map((item) => (
                <article className={`chat-message ${item.role}`} key={item.id}>
                  <strong>{item.role === "user" ? "\uC0AC\uC6A9\uC790" : "AI"}</strong>
                  <p>{item.text}</p>
                </article>
              ))
            )}
            {chatting ? (
              <article className="chat-message assistant">
                <strong>AI</strong>
                <p>{TEXT.asking}</p>
              </article>
            ) : null}
            <div ref={chatEndRef} />
          </section>
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
        <form className="chat-card" onSubmit={(event) => void submitChat(event)}>
          <label>
            <span>
              <Bot size={16} /> {TEXT.aiChat}
            </span>
            <textarea
              rows={3}
              value={chatInput}
              placeholder={TEXT.aiPlaceholder}
              onChange={(event) => setChatInput(event.target.value)}
            />
          </label>
          <button type="submit" disabled={chatting || !chatInput.trim()}>
            {chatting ? TEXT.asking : TEXT.send}
          </button>
        </form>
      </aside>
    </main>
  );
}

createRoot(document.getElementById("root") as HTMLElement).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
