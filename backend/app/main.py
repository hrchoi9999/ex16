from __future__ import annotations

from datetime import date, datetime, time

from fastapi import FastAPI, HTTPException, Response, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, Field, model_validator

from personal_assistant.config import settings
from personal_assistant.database import ScheduleStore
from personal_assistant.models import ScheduleEvent


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


class EventCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    start_at: datetime
    end_at: datetime
    description: str = ""
    location: str = ""
    importance: int = Field(default=3, ge=1, le=5)

    @model_validator(mode="after")
    def validate_time_range(self) -> "EventCreateRequest":
        if self.end_at <= self.start_at:
            raise ValueError("end_at must be later than start_at")
        return self


class EventUpdateRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    start_at: datetime | None = None
    end_at: datetime | None = None
    description: str | None = None
    location: str | None = None
    importance: int | None = Field(default=None, ge=1, le=5)

    @model_validator(mode="after")
    def validate_time_range(self) -> "EventUpdateRequest":
        if self.start_at is not None and self.end_at is not None and self.end_at <= self.start_at:
            raise ValueError("end_at must be later than start_at")
        return self


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


@app.post("/events", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
def create_event(payload: EventCreateRequest) -> EventResponse:
    event = store.add_event(
        ScheduleEvent(
            id=None,
            title=payload.title.strip(),
            start_at=payload.start_at,
            end_at=payload.end_at,
            description=payload.description.strip(),
            location=payload.location.strip(),
            importance=payload.importance,
            source="local",
            sync_status="local",
        )
    )
    return EventResponse.model_validate(event)


@app.put("/events/{event_id}", response_model=EventResponse)
def update_event(event_id: int, payload: EventUpdateRequest) -> EventResponse:
    existing = store.get_event(event_id)
    if existing is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")

    start_at = payload.start_at if payload.start_at is not None else existing.start_at
    end_at = payload.end_at if payload.end_at is not None else existing.end_at
    if end_at <= start_at:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="end_at must be later than start_at")

    updated = store.update_event(
        event_id,
        title=payload.title.strip() if payload.title is not None else None,
        start_at=payload.start_at,
        end_at=payload.end_at,
        description=payload.description.strip() if payload.description is not None else None,
        location=payload.location.strip() if payload.location is not None else None,
        importance=payload.importance,
        sync_status="pending_sync" if existing.source == "google_calendar" else existing.sync_status,
    )
    if updated is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    return EventResponse.model_validate(updated)


@app.delete("/events/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_event(event_id: int) -> Response:
    if store.get_event(event_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    store.delete_event(event_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
