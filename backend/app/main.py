from __future__ import annotations

from datetime import date, datetime, time

from fastapi import FastAPI, HTTPException, Response, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, Field, model_validator

from personal_assistant.ai_chat import answer_schedule_question
from personal_assistant.ai_router import route_ai_command
from personal_assistant.config import settings
from personal_assistant.database import ScheduleStore
from personal_assistant.google_calendar import GoogleCalendarClient
from personal_assistant.models import ExternalScheduleCandidate, ScheduleEvent
from personal_assistant.site_collector import REQUESTED_SITE_SOURCES, collect_interest_sites


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
google_client = GoogleCalendarClient()


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


class UserResponse(BaseModel):
    id: int | None
    email: str
    display_name: str
    provider: str
    linked_at: str
    auto_sync: bool


class CandidateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int | None
    source: str
    category: str
    title: str
    recruitment_period: str
    url: str
    status: str
    collected_at: str
    selected: bool


class CollectionResponse(BaseModel):
    success: bool
    message: str
    saved_count: int
    candidates: list[CandidateResponse]


class GoogleStatusResponse(BaseModel):
    enabled: bool
    linked: bool
    email: str
    message: str


class GoogleOAuthStartResponse(BaseModel):
    enabled: bool
    success: bool
    message: str
    authorization_url: str


class GoogleActionResponse(BaseModel):
    success: bool
    message: str


class GoogleImportResponse(BaseModel):
    success: bool
    message: str
    imported_count: int


class AiChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=1000)


class AiChatResponse(BaseModel):
    answer: str
    matched_event_ids: list[int]
    intent: str
    menu: str


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


@app.get("/user/active", response_model=UserResponse | None)
def active_user() -> UserResponse | None:
    user = store.get_active_user()
    return UserResponse.model_validate(user, from_attributes=True) if user else None


@app.get("/google/status", response_model=GoogleStatusResponse)
def google_status() -> GoogleStatusResponse:
    user = store.get_active_user()
    token_exists = GoogleCalendarClient._token_path().exists()
    linked = bool(user or token_exists)
    email = user.email if user else settings.google_registered_email or ("google-user" if token_exists else "")
    if linked:
        message = "Google Calendar가 연결되어 있습니다. 기존 OAuth 토큰을 재사용합니다."
    elif google_client.enabled:
        message = "초대된 사용자는 Google 계정 연동을 한 번 진행하면 됩니다."
    else:
        message = "Google Calendar OAuth 설정이 아직 없습니다."
    return GoogleStatusResponse(enabled=google_client.enabled, linked=linked, email=email, message=message)


@app.post("/google/oauth/start", response_model=GoogleOAuthStartResponse)
def start_google_oauth() -> GoogleOAuthStartResponse:
    result = google_client.start_oauth(settings.google_registered_email)
    return GoogleOAuthStartResponse(
        enabled=result.enabled,
        success=result.success,
        message=result.message,
        authorization_url=result.authorization_url,
    )


@app.post("/google/import", response_model=GoogleImportResponse)
def import_google_events(start: date, end: date) -> GoogleImportResponse:
    start_at = datetime.combine(start, time.min)
    end_at = datetime.combine(end, time.max)
    result = google_client.list_events(start_at, end_at)
    if not result.success:
        return GoogleImportResponse(success=False, message=result.message, imported_count=0)

    imported_count = 0
    for event in result.events:
        store.upsert_google_event(event)
        imported_count += 1

    email = settings.google_registered_email or "google-user"
    store.register_user(email, email.split("@")[0], "google")

    return GoogleImportResponse(success=True, message=result.message, imported_count=imported_count)


@app.delete("/google/account", response_model=GoogleActionResponse)
def disconnect_google_account() -> GoogleActionResponse:
    token_path = GoogleCalendarClient._token_path()
    if token_path.exists():
        token_path.unlink()
    store.clear_users()
    return GoogleActionResponse(success=True, message="Google Calendar 연동을 해제했습니다. 다시 사용하려면 Google 계정 연동을 진행하세요.")


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


@app.get("/candidates", response_model=list[CandidateResponse])
def list_candidates() -> list[CandidateResponse]:
    candidates = [candidate for candidate in store.list_candidates() if candidate.source in REQUESTED_SITE_SOURCES]
    return [CandidateResponse.model_validate(candidate) for candidate in candidates]


@app.post("/candidates/collect", response_model=CollectionResponse)
def collect_candidates() -> CollectionResponse:
    result = collect_interest_sites()
    if result.candidates:
        store.delete_candidates_by_sources(REQUESTED_SITE_SOURCES)
    saved_candidates: list[ExternalScheduleCandidate] = []
    for candidate in result.candidates:
        saved_candidates.append(store.upsert_candidate(candidate))
    return CollectionResponse(
        success=result.success,
        message=result.message,
        saved_count=len(saved_candidates),
        candidates=[CandidateResponse.model_validate(candidate) for candidate in saved_candidates],
    )


@app.post("/ai/chat", response_model=AiChatResponse)
def ai_chat(payload: AiChatRequest) -> AiChatResponse:
    route = route_ai_command(payload.question)
    events = store.list_events(include_past=True)

    if route.intent == "query":
        result = answer_schedule_question(payload.question, events)
        return AiChatResponse(
            answer=result.answer,
            matched_event_ids=result.matched_event_ids,
            intent=route.intent,
            menu=route.menu,
        )

    if route.intent == "collect_sites":
        collection = collect_candidates()
        return AiChatResponse(
            answer=f"관심 사이트 수집을 실행했습니다.\n{collection.message}",
            matched_event_ids=[],
            intent=route.intent,
            menu=route.menu,
        )

    if route.intent == "collect_and_register_sites":
        collection = collect_candidates()
        return AiChatResponse(
            answer=(
                "관심 사이트 후보 수집까지 완료했습니다. "
                "마감일 기준 캘린더 등록은 후보 확인 UI 이식 sprint에서 연결하겠습니다.\n"
                f"{collection.message}"
            ),
            matched_event_ids=[],
            intent=route.intent,
            menu=route.menu,
        )

    if route.intent in {"create_event", "edit_help", "delete_help"}:
        return AiChatResponse(
            answer="일정 등록, 수정, 삭제는 현재 우측 일정 편집 폼에서 처리할 수 있습니다. 질문한 날짜를 선택한 뒤 폼을 사용해 주세요.",
            matched_event_ids=[],
            intent=route.intent,
            menu=route.menu,
        )

    result = answer_schedule_question(payload.question, events)
    return AiChatResponse(
        answer=result.answer,
        matched_event_ids=result.matched_event_ids,
        intent=route.intent,
        menu=route.menu,
    )


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
