from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from .config import settings
from .models import ScheduleEvent


CALENDAR_SCOPES = ["https://www.googleapis.com/auth/calendar"]


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


@dataclass
class GoogleAccountResult:
    enabled: bool
    success: bool
    message: str
    email: str = ""
    display_name: str = ""


class GoogleCalendarClient:
    def __init__(self) -> None:
        self.enabled = settings.google_calendar_enabled

    def _service(self):
        from googleapiclient.discovery import build

        if settings.google_oauth_enabled:
            credentials = self._oauth_credentials()
            return build("calendar", "v3", credentials=credentials)

        from google.oauth2 import service_account

        credentials = service_account.Credentials.from_service_account_file(
            settings.google_service_account_file,
            scopes=CALENDAR_SCOPES,
        )
        return build("calendar", "v3", credentials=credentials)

    def _oauth_credentials(self):
        token_path = Path(settings.google_oauth_token_file)
        credentials = None
        if token_path.exists():
            from google.oauth2.credentials import Credentials

            credentials = Credentials.from_authorized_user_file(str(token_path), CALENDAR_SCOPES)

        if credentials and credentials.valid:
            return credentials

        if credentials and credentials.expired and credentials.refresh_token:
            from google.auth.transport.requests import Request

            credentials.refresh(Request())
        else:
            try:
                from google_auth_oauthlib.flow import InstalledAppFlow
            except ImportError as exc:
                raise RuntimeError(
                    "Google OAuth를 사용하려면 google-auth-oauthlib 패키지가 필요합니다."
                ) from exc

            flow = self._installed_app_flow(InstalledAppFlow)
            credentials = flow.run_local_server(port=0)

        token_path.parent.mkdir(parents=True, exist_ok=True)
        token_path.write_text(credentials.to_json(), encoding="utf-8")
        return credentials

    @staticmethod
    def _installed_app_flow(flow_class):
        if settings.google_oauth_client_secret_file:
            return flow_class.from_client_secrets_file(
                settings.google_oauth_client_secret_file,
                CALENDAR_SCOPES,
            )
        client_config = {
            "installed": {
                "client_id": settings.google_oauth_client_id,
                "client_secret": settings.google_oauth_client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": ["http://localhost"],
            }
        }
        return flow_class.from_client_config(client_config, CALENDAR_SCOPES)

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
            return datetime.fromisoformat(raw).astimezone(ZoneInfo(settings.app_timezone)).replace(tzinfo=None)
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
            source="google_calendar",
            sync_status="synced",
        )

    def register_account(self) -> GoogleAccountResult:
        if not self.enabled:
            return GoogleAccountResult(
                enabled=False,
                success=False,
                message=(
                    "Google Calendar OAuth 앱 설정이 아직 없습니다. 사용자가 키를 입력하는 것이 아니라, "
                    "서비스 운영자가 한 번만 GOOGLE_OAUTH_CLIENT_ID/SECRET 또는 client_secret 파일을 서버에 설정해야 합니다."
                ),
            )

        if settings.google_registered_email:
            return GoogleAccountResult(
                enabled=True,
                success=True,
                message="환경 변수에 등록된 Google 계정을 사용합니다.",
                email=settings.google_registered_email,
                display_name=settings.google_registered_email.split("@")[0],
            )

        if settings.google_oauth_client_secret_file:
            try:
                self._oauth_credentials()
                return GoogleAccountResult(
                    enabled=True,
                    success=True,
                    message="Google 로그인과 Calendar 권한 동의가 완료되었습니다. 현재 보기 범위의 일정을 가져옵니다.",
                    email="google-user",
                    display_name="Google User",
                )
            except Exception as exc:
                return GoogleAccountResult(True, False, f"Google 로그인 인증에 실패했습니다. {exc}")

        return GoogleAccountResult(
            enabled=True,
            success=True,
            message="서비스 계정 방식으로 Google Calendar 연동이 활성화되었습니다.",
            email="service-account",
            display_name="Google Service Account",
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
            created = self.create_event(event)
            if created.google_event_id:
                return created
            return GoogleCalendarSyncResult(True, False, "Google Calendar event id가 없어 로컬만 변경했습니다.")
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
            return GoogleCalendarSyncResult(True, False, "Google Calendar event id가 없어 로컬만 삭제했습니다.")
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
                message="Google Calendar 설정이 없습니다. .env에 Google Calendar 인증 정보를 설정하세요.",
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
