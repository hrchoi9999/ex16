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


@dataclass
class GoogleOAuthStartResult:
    enabled: bool
    success: bool
    message: str
    authorization_url: str = ""
    state: str = ""


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
            raise RuntimeError("Google 로그인이 필요합니다. 앱 화면에서 Google 로그인 URL을 먼저 여세요.")

        token_path.parent.mkdir(parents=True, exist_ok=True)
        token_path.write_text(credentials.to_json(), encoding="utf-8")
        return credentials

    @staticmethod
    def _oauth_flow(flow_class):
        if settings.google_oauth_client_secret_file:
            flow = flow_class.from_client_secrets_file(
                settings.google_oauth_client_secret_file,
                CALENDAR_SCOPES,
            )
        else:
            client_config = {
                "web": {
                    "client_id": settings.google_oauth_client_id,
                    "client_secret": settings.google_oauth_client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [settings.google_oauth_redirect_uri],
                }
            }
            flow = flow_class.from_client_config(client_config, CALENDAR_SCOPES)
        flow.redirect_uri = settings.google_oauth_redirect_uri
        return flow

    def start_oauth(self, login_hint: str = "") -> GoogleOAuthStartResult:
        if not settings.google_oauth_enabled:
            return GoogleOAuthStartResult(
                enabled=False,
                success=False,
                message=(
                    "Google 로그인 URL을 만들 수 없습니다. 서비스 운영자가 Google Cloud에서 OAuth 클라이언트를 만들고 "
                    "GOOGLE_OAUTH_CLIENT_ID/SECRET 또는 GOOGLE_OAUTH_CLIENT_SECRET_FILE을 설정해야 합니다."
                ),
            )
        try:
            from google_auth_oauthlib.flow import Flow
        except ImportError as exc:
            return GoogleOAuthStartResult(
                enabled=True,
                success=False,
                message=f"Google OAuth 패키지가 설치되어 있지 않습니다. google-auth-oauthlib 설치가 필요합니다. {exc}",
            )

        flow = self._oauth_flow(Flow)
        kwargs = {
            "access_type": "offline",
            "include_granted_scopes": "true",
            "prompt": "consent",
        }
        if login_hint:
            kwargs["login_hint"] = login_hint
        authorization_url, state = flow.authorization_url(**kwargs)
        return GoogleOAuthStartResult(
            enabled=True,
            success=True,
            message="Google 로그인 화면을 열어 Calendar 권한에 동의하세요. 동의 후 이 앱으로 자동 돌아옵니다.",
            authorization_url=authorization_url,
            state=state,
        )

    def finish_oauth(self, code: str, state: str = "") -> GoogleAccountResult:
        if not settings.google_oauth_enabled:
            return GoogleAccountResult(False, False, "Google OAuth 클라이언트 설정이 없습니다.")
        try:
            from google_auth_oauthlib.flow import Flow

            flow = self._oauth_flow(Flow)
            if state:
                flow.oauth2session.state = state
            flow.fetch_token(code=code)
            credentials = flow.credentials
            token_path = Path(settings.google_oauth_token_file)
            token_path.parent.mkdir(parents=True, exist_ok=True)
            token_path.write_text(credentials.to_json(), encoding="utf-8")
            return GoogleAccountResult(
                enabled=True,
                success=True,
                message="Google 로그인과 Calendar 권한 동의가 완료되었습니다.",
                email=settings.google_registered_email or "google-user",
                display_name=(settings.google_registered_email.split("@")[0] if settings.google_registered_email else "Google User"),
            )
        except Exception as exc:
            return GoogleAccountResult(True, False, f"Google OAuth 콜백 처리에 실패했습니다. {exc}")

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

        if settings.google_oauth_enabled:
            try:
                start = self.start_oauth()
                return GoogleAccountResult(start.enabled, start.success, start.message, email="google-user", display_name="Google User")
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
