from __future__ import annotations

from datetime import date, datetime, time

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict

from personal_assistant.config import settings
from personal_assistant.database import ScheduleStore


app = FastAPI(title="AI Scheduler API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
store = ScheduleStore(settings.database_path)


class HealthResponse(BaseModel):
    status: str
    service: str


class EventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int | None
    title: str
    start_at: datetime
    end_at: datetime
    description: str
    location: str
    importance: int
    source: str
    source_url: str
    sync_status: str


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", service="ai-scheduler-api")


@app.get("/events", response_model=list[EventResponse])
def list_events(include_past: bool = True) -> list[EventResponse]:
    return [EventResponse.model_validate(event) for event in store.list_events(include_past=include_past)]


@app.get("/events/today", response_model=list[EventResponse])
def today_events() -> list[EventResponse]:
    today = date.today()
    start_at = datetime.combine(today, time.min)
    end_at = datetime.combine(today, time.max)
    events = [
        event
        for event in store.list_events(include_past=True)
        if event.start_at <= end_at and event.end_at >= start_at
    ]
    return [EventResponse.model_validate(event) for event in events]


@app.get("/events/range", response_model=list[EventResponse])
def events_in_range(start: date, end: date) -> list[EventResponse]:
    start_at = datetime.combine(start, time.min)
    end_at = datetime.combine(end, time.max)
    events = [
        event
        for event in store.list_events(include_past=True)
        if event.start_at <= end_at and event.end_at >= start_at
    ]
    return [EventResponse.model_validate(event) for event in events]
