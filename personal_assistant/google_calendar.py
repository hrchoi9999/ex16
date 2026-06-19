from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
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
    code_verifier: str = ""


class GoogleCalendarClient:
    def __init__(self) -> None:
        self.enabled = settings.google_calendar_enabled

    @staticmethod
    def _redirect_uri() -> str:
        uri = settings.google_oauth_redirect_uri.strip()
        if uri in {"http://localhost:8501/", "http://127.0.0.1:8501/"}:
            return uri[:-1]
        return uri

    @staticmethod
    def _token_path() -> Path:
        configured = Path(settings.google_oauth_token_file)
        name = configured.name.lower()
        if name.startswith("client_secret_") or "apps.googleusercontent.com" in name:
            return Path("data/google_token.json")
        return configured

    @staticmethod
    def _oauth_state_path() -> Path:
        return Path("data/google_oauth_states.json")

    @classmethod
    def _remember_oauth_state(cls, state: str, code_verifier: str) -> None:
        if not state or not code_verifier:
            return
        path = cls._oauth_state_path()
        states: dict[str, dict[str, str]] = {}
        if path.exists():
            try:
                states = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                states = {}

        now = datetime.now(timezone.utc)
        fresh_states: dict[str, dict[str, str]] = {}
        for key, value in states.items():
            try:
                created_at = datetime.fromisoformat(value.get("created_at", ""))
            except ValueError:
                continue
            if now - created_at < timedelta(minutes=15):
                fresh_states[key] = value

        fresh_states[state] = {
            "code_verifier": code_verifier,
            "created_at": now.isoformat(),
        }
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(fresh_states), encoding="utf-8")

    @classmethod
    def _pop_oauth_code_verifier(cls, state: str) -> str:
        if not state:
            return ""
        path = cls._oauth_state_path()
        if not path.exists():
            return ""
        try:
            states = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return ""
        value = states.pop(state, {})
        try:
            path.write_text(json.dumps(states), encoding="utf-8")
        except OSError:
            pass
        return value.get("code_verifier", "")

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
        token_path = self._token_path()
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
    def _oauth_flow(flow_class, state: str = "", code_verifier: str = ""):
        kwargs = {}
        if state:
            kwargs["state"] = state
        if code_verifier:
            kwargs["code_verifier"] = code_verifier
        if settings.google_oauth_client_secret_file:
            flow = flow_class.from_client_secrets_file(
                settings.google_oauth_client_secret_file,
                CALENDAR_SCOPES,
                **kwargs,
            )
        else:
            redirect_uri = GoogleCalendarClient._redirect_uri()
            client_config = {
                "web": {
                    "client_id": settings.google_oauth_client_id,
                    "client_secret": settings.google_oauth_client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [redirect_uri],
                }
            }
            flow = flow_class.from_client_config(client_config, CALENDAR_SCOPES, **kwargs)
        flow.redirect_uri = GoogleCalendarClient._redirect_uri()
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
        code_verifier = flow.code_verifier or ""
        self._remember_oauth_state(state, code_verifier)
        return GoogleOAuthStartResult(
            enabled=True,
            success=True,
            message="Google 로그인 화면을 열어 Calendar 권한에 동의하세요. 동의 후 이 앱으로 자동 돌아옵니다.",
            authorization_url=authorization_url,
            state=state,
            code_verifier=code_verifier,
        )

    def finish_oauth(self, code: str, state: str = "", code_verifier: str = "") -> GoogleAccountResult:
        if not settings.google_oauth_enabled:
            return GoogleAccountResult(False, False, "Google OAuth 클라이언트 설정이 없습니다.")
        try:
            from google_auth_oauthlib.flow import Flow

            verifier = code_verifier or self._pop_oauth_code_verifier(state)
            if not verifier:
                return GoogleAccountResult(
                    True,
                    False,
                    "Google OAuth 인증 정보가 만료되었습니다. Google 로그인 링크를 새로 만든 뒤 다시 로그인하세요.",
                )
            flow = self._oauth_flow(Flow, state=state, code_verifier=verifier)
            flow.fetch_token(code=code)
            credentials = flow.credentials
            token_path = self._token_path()
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

    @staticmethod
    def _google_event_key(calendar_id: str, event_id: str, is_primary: bool = False) -> str:
        if is_primary:
            return event_id
        if calendar_id in {"", settings.google_calendar_id, "primary"}:
            return event_id
        return f"{calendar_id}::{event_id}"

    @staticmethod
    def _split_google_event_key(google_event_id: str) -> tuple[str, str]:
        if "::" in google_event_id:
            calendar_id, event_id = google_event_id.split("::", 1)
            return calendar_id, event_id
        return settings.google_calendar_id, google_event_id

    @classmethod
    def _event_from_google(cls, item: dict[str, object], calendar_id: str = "", is_primary: bool = False) -> ScheduleEvent:
        start_value = item.get("start") if isinstance(item.get("start"), dict) else {}
        end_value = item.get("end") if isinstance(item.get("end"), dict) else {}
        start_at = cls._parse_google_datetime(start_value)  # type: ignore[arg-type]
        end_at = cls._parse_google_datetime(end_value, fallback_end=True)  # type: ignore[arg-type]
        if end_at <= start_at:
            end_at = start_at + timedelta(hours=1)
        event_id = str(item.get("id") or "")
        return ScheduleEvent(
            id=None,
            title=str(item.get("summary") or "(제목 없음)"),
            start_at=start_at,
            end_at=end_at,
            description=str(item.get("description") or ""),
            location=str(item.get("location") or ""),
            importance=3,
            google_event_id=cls._google_event_key(calendar_id, event_id, is_primary),
            source="google_calendar",
            sync_status="synced",
        )

    @staticmethod
    def _calendar_entries(service) -> list[dict[str, object]]:
        try:
            response = service.calendarList().list(showHidden=False).execute()
        except Exception:
            return [{"id": settings.google_calendar_id, "summary": settings.google_calendar_id, "primary": True, "selected": True}]

        entries: list[dict[str, object]] = []
        seen: set[str] = set()
        for item in response.get("items", []):
            calendar_id = str(item.get("id") or "")
            if not calendar_id or calendar_id in seen:
                continue
            if item.get("deleted") or item.get("hidden"):
                continue
            if item.get("selected") is False and not item.get("primary"):
                continue
            entries.append(item)
            seen.add(calendar_id)

        if settings.google_calendar_id and settings.google_calendar_id not in seen:
            entries.insert(0, {"id": settings.google_calendar_id, "summary": settings.google_calendar_id, "primary": True, "selected": True})
        return entries

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
            calendar_id, event_id = self._split_google_event_key(event.google_event_id)
            self._service().events().update(
                calendarId=calendar_id,
                eventId=event_id,
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
            calendar_id, event_id = self._split_google_event_key(event.google_event_id)
            self._service().events().delete(
                calendarId=calendar_id,
                eventId=event_id,
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
            service = self._service()
            events: list[ScheduleEvent] = []
            checked_count = 0
            skipped: list[str] = []
            for calendar_entry in self._calendar_entries(service):
                calendar_id = str(calendar_entry.get("id") or settings.google_calendar_id)
                calendar_name = str(calendar_entry.get("summary") or calendar_id)
                is_primary = bool(calendar_entry.get("primary"))
                try:
                    response = (
                        service.events()
                        .list(
                            calendarId=calendar_id,
                            timeMin=start_at.replace(tzinfo=ZoneInfo(settings.app_timezone)).isoformat(),
                            timeMax=end_at.replace(tzinfo=ZoneInfo(settings.app_timezone)).isoformat(),
                            singleEvents=True,
                            orderBy="startTime",
                        )
                        .execute()
                    )
                except Exception as exc:
                    skipped.append(f"{calendar_name}: {exc}")
                    continue
                checked_count += 1
                events.extend(self._event_from_google(item, calendar_id, is_primary) for item in response.get("items", []))
            events.sort(key=lambda event: event.start_at)
            detail = f"{checked_count}개 캘린더에서 {len(events)}개 일정을 가져왔습니다."
            if skipped:
                detail += f" 일부 캘린더는 건너뜀: {' / '.join(skipped[:3])}"
            return GoogleCalendarImportResult(
                enabled=True,
                success=True,
                message=f"Google Calendar {detail}",
                events=events,
            )
        except Exception as exc:
            return GoogleCalendarImportResult(
                enabled=True,
                success=False,
                message=f"Google Calendar 일정 조회에 실패했습니다. {exc}",
                events=[],
            )
