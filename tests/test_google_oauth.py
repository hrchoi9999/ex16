from __future__ import annotations

from types import SimpleNamespace

import personal_assistant.google_calendar as google_calendar
from personal_assistant.google_calendar import GoogleCalendarClient


def test_oauth_start_persists_code_verifier(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(
        google_calendar,
        "settings",
        SimpleNamespace(
            google_calendar_enabled=True,
            google_oauth_enabled=True,
            google_oauth_client_secret_file="",
            google_oauth_client_id="test-client-id.apps.googleusercontent.com",
            google_oauth_client_secret="test-client-secret",
            google_oauth_redirect_uri="http://localhost:8501",
            google_oauth_token_file=str(tmp_path / "token.json"),
        ),
    )
    monkeypatch.setattr(
        GoogleCalendarClient,
        "_oauth_state_path",
        staticmethod(lambda: tmp_path / "google_oauth_states.json"),
    )

    result = GoogleCalendarClient().start_oauth()

    assert result.success
    assert result.state
    assert result.code_verifier
    assert "code_challenge=" in result.authorization_url
    assert GoogleCalendarClient._pop_oauth_code_verifier(result.state) == result.code_verifier
    assert GoogleCalendarClient._pop_oauth_code_verifier(result.state) == ""


def test_google_event_key_keeps_primary_id_and_namespaces_shared_calendar(monkeypatch) -> None:
    monkeypatch.setattr(google_calendar, "settings", SimpleNamespace(google_calendar_id="primary"))

    assert GoogleCalendarClient._google_event_key("hrchoi9999@gmail.com", "event-1", is_primary=True) == "event-1"
    assert GoogleCalendarClient._google_event_key("shared-calendar", "event-1") == "shared-calendar::event-1"
    assert GoogleCalendarClient._split_google_event_key("shared-calendar::event-1") == ("shared-calendar", "event-1")
    assert GoogleCalendarClient._split_google_event_key("event-1") == ("primary", "event-1")
