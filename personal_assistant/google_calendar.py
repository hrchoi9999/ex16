from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from .config import settings
from .models import ScheduleEvent


@dataclass
class GoogleCalendarSyncResult:
    enabled: bool
    success: bool
    message: str
    google_event_id: str | None = None


@dataclass
class GoogleCalendarImportResult:
    enabled: bool
    success: bool
    message: str
    events: list[ScheduleEvent]


class GoogleCalendarClient:
    def __init__(self) -> None:
        self.enabled = settings.google_calendar_enabled

    def _service(self):
        from google.oauth2 import service_account
        from googleapiclient.discovery import build

        credentials = service_account.Credentials.from_service_account_file(
            settings.google_service_account_file,
            scopes=["https://www.googleapis.com/auth/calendar"],
        )
        return build("calendar", "v3", credentials=credentials)

    @staticmethod
    def _google_body(event: ScheduleEvent) -> dict[str, object]:
        return {
            "summary": event.title,
            "description": event.description,
            "location": event.location,
            "start": {"dateTime": event.start_at.isoformat(), "timeZone": settings.app_timezone},
            "end": {"dateTime": event.end_at.isoformat(), "timeZone": settings.app_timezone},
        }

    @staticmethod
    def _parse_google_datetime(value: dict[str, str], fallback_end: bool = False) -> datetime:
        if "dateTime" in value:
            raw = value["dateTime"].replace("Z", "+00:00")
            return datetime.fromisoformat(raw).replace(tzinfo=None)
        if "date" in value:
            parsed = datetime.combine(date.fromisoformat(value["date"]), time.min)
            if fallback_end:
                return parsed - timedelta(seconds=1)
            return parsed
        return datetime.now()

    @classmethod
    def _event_from_google(cls, item: dict[str, object]) -> ScheduleEvent:
        start_value = item.get("start") if isinstance(item.get("start"), dict) else {}
        end_value = item.get("end") if isinstance(item.get("end"), dict) else {}
        start_at = cls._parse_google_datetime(start_value)  # type: ignore[arg-type]
        end_at = cls._parse_google_datetime(end_value, fallback_end=True)  # type: ignore[arg-type]
        if end_at <= start_at:
            end_at = start_at + timedelta(hours=1)
        return ScheduleEvent(
            id=None,
            title=str(item.get("summary") or "(제목 없음)"),
            start_at=start_at,
            end_at=end_at,
            description=str(item.get("description") or ""),
            location=str(item.get("location") or ""),
            importance=3,
            google_event_id=str(item.get("id") or ""),
        )

    def create_event(self, event: ScheduleEvent) -> GoogleCalendarSyncResult:
        if not self.enabled:
            return GoogleCalendarSyncResult(False, False, "Google Calendar 설정이 없어 로컬에만 저장했습니다.")
        try:
            created = (
                self._service()
                .events()
                .insert(calendarId=settings.google_calendar_id, body=self._google_body(event))
                .execute()
            )
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
                message=f"Google Calendar 등록은 실패했고 로컬에는 저장했습니다. {exc}",
            )

    def update_event(self, event: ScheduleEvent) -> GoogleCalendarSyncResult:
        if not self.enabled:
            return GoogleCalendarSyncResult(False, False, "Google Calendar 설정이 없어 로컬만 변경했습니다.")
        if not event.google_event_id:
            return GoogleCalendarSyncResult(True, False, "Google Calendar 이벤트 ID가 없어 로컬만 변경했습니다.")
        try:
            self._service().events().update(
                calendarId=settings.google_calendar_id,
                eventId=event.google_event_id,
                body=self._google_body(event),
            ).execute()
            return GoogleCalendarSyncResult(
                enabled=True,
                success=True,
                message="Google Calendar 일정도 변경했습니다.",
                google_event_id=event.google_event_id,
            )
        except Exception as exc:
            return GoogleCalendarSyncResult(
                enabled=True,
                success=False,
                message=f"Google Calendar 변경은 실패했고 로컬은 변경했습니다. {exc}",
                google_event_id=event.google_event_id,
            )

    def delete_event(self, event: ScheduleEvent) -> GoogleCalendarSyncResult:
        if not self.enabled:
            return GoogleCalendarSyncResult(False, False, "Google Calendar 설정이 없어 로컬만 삭제했습니다.")
        if not event.google_event_id:
            return GoogleCalendarSyncResult(True, False, "Google Calendar 이벤트 ID가 없어 로컬만 삭제했습니다.")
        try:
            self._service().events().delete(
                calendarId=settings.google_calendar_id,
                eventId=event.google_event_id,
            ).execute()
            return GoogleCalendarSyncResult(
                enabled=True,
                success=True,
                message="Google Calendar 일정도 삭제했습니다.",
                google_event_id=event.google_event_id,
            )
        except Exception as exc:
            return GoogleCalendarSyncResult(
                enabled=True,
                success=False,
                message=f"Google Calendar 삭제는 실패했고 로컬은 삭제했습니다. {exc}",
                google_event_id=event.google_event_id,
            )

    def list_events(self, start_at: datetime, end_at: datetime) -> GoogleCalendarImportResult:
        if not self.enabled:
            return GoogleCalendarImportResult(
                enabled=False,
                success=False,
                message="Google Calendar 설정이 없습니다. .env에 GOOGLE_SERVICE_ACCOUNT_FILE과 GOOGLE_CALENDAR_ID를 설정해 주세요.",
                events=[],
            )
        try:
            response = (
                self._service()
                .events()
                .list(
                    calendarId=settings.google_calendar_id,
                    timeMin=start_at.replace(tzinfo=ZoneInfo(settings.app_timezone)).isoformat(),
                    timeMax=end_at.replace(tzinfo=ZoneInfo(settings.app_timezone)).isoformat(),
                    singleEvents=True,
                    orderBy="startTime",
                )
                .execute()
            )
            events = [self._event_from_google(item) for item in response.get("items", [])]
            return GoogleCalendarImportResult(
                enabled=True,
                success=True,
                message=f"Google Calendar에서 {len(events)}개 일정을 가져왔습니다.",
                events=events,
            )
        except Exception as exc:
            return GoogleCalendarImportResult(
                enabled=True,
                success=False,
                message=f"Google Calendar 일정 조회에 실패했습니다. {exc}",
                events=[],
            )
