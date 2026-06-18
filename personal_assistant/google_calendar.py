from __future__ import annotations

from dataclasses import dataclass

from .config import settings
from .models import ScheduleEvent


@dataclass
class GoogleCalendarSyncResult:
    enabled: bool
    success: bool
    message: str
    google_event_id: str | None = None


class GoogleCalendarClient:
    def __init__(self) -> None:
        self.enabled = settings.google_calendar_enabled

    def create_event(self, event: ScheduleEvent) -> GoogleCalendarSyncResult:
        if not self.enabled:
            return GoogleCalendarSyncResult(False, False, "Google Calendar 설정이 없어 로컬에만 저장했습니다.")
        try:
            from google.oauth2 import service_account
            from googleapiclient.discovery import build

            credentials = service_account.Credentials.from_service_account_file(
                settings.google_service_account_file,
                scopes=["https://www.googleapis.com/auth/calendar"],
            )
            service = build("calendar", "v3", credentials=credentials)
            body = {
                "summary": event.title,
                "description": event.description,
                "location": event.location,
                "start": {"dateTime": event.start_at.isoformat(), "timeZone": settings.app_timezone},
                "end": {"dateTime": event.end_at.isoformat(), "timeZone": settings.app_timezone},
            }
            created = service.events().insert(calendarId=settings.google_calendar_id, body=body).execute()
            return GoogleCalendarSyncResult(
                enabled=True,
                success=True,
                message="Google Calendar에도 일정을 등록했습니다.",
                google_event_id=created.get("id"),
            )
        except Exception as exc:
            return GoogleCalendarSyncResult(
                enabled=True,
                success=False,
                message=f"Google Calendar 등록은 실패했고 로컬에는 저장했습니다: {exc}",
            )

