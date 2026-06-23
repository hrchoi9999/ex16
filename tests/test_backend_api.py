from __future__ import annotations

from fastapi.testclient import TestClient

import backend.app.main as backend_main
from backend.app.main import app
from personal_assistant.ai_chat import AiChatResult
from personal_assistant.models import AppUser, ExternalScheduleCandidate
from personal_assistant.site_collector import CollectionResult


def test_health_endpoint() -> None:
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "ai-scheduler-api"}


def test_events_endpoint_returns_list() -> None:
    client = TestClient(app)

    response = client.get("/events")

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_events_range_endpoint_returns_list() -> None:
    client = TestClient(app)

    response = client.get("/events/range?start=2026-06-01&end=2026-06-30")

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_left_sidebar_support_endpoints(monkeypatch) -> None:
    client = TestClient(app)
    collected: list[ExternalScheduleCandidate] = []

    class FakeStore:
        def get_active_user(self) -> AppUser:
            return AppUser(id=1, email="tester@example.com", display_name="Tester", linked_at="2026-06-23T12:30:00")

        def list_candidates(self) -> list[ExternalScheduleCandidate]:
            return collected

        def delete_candidates_by_sources(self, sources: tuple[str, ...]) -> None:
            collected.clear()

        def upsert_candidate(self, candidate: ExternalScheduleCandidate) -> ExternalScheduleCandidate:
            saved = ExternalScheduleCandidate(
                id=1,
                source=candidate.source,
                category=candidate.category,
                title=candidate.title,
                recruitment_period=candidate.recruitment_period,
                url=candidate.url,
                status=candidate.status,
                collected_at=candidate.collected_at,
                selected=candidate.selected,
            )
            collected.append(saved)
            return saved

    monkeypatch.setattr(backend_main, "store", FakeStore())

    active_user_response = client.get("/user/active")
    assert active_user_response.status_code == 200

    candidates_response = client.get("/candidates")
    assert candidates_response.status_code == 200
    assert isinstance(candidates_response.json(), list)

    def fake_collect_interest_sites() -> CollectionResult:
        return CollectionResult(
            True,
            "1 candidate collected",
            [
                ExternalScheduleCandidate(
                    id=None,
                    source="K-Startup",
                    category="모집공고",
                    title="React migration candidate",
                    recruitment_period="마감일자 2026-06-30",
                    url="https://example.com/kstartup",
                    status="모집중",
                    collected_at="2026-06-23T12:30:00",
                )
            ],
        )

    monkeypatch.setattr(backend_main, "collect_interest_sites", fake_collect_interest_sites)
    collect_response = client.post("/candidates/collect")

    assert collect_response.status_code == 200
    payload = collect_response.json()
    assert payload["success"] is True
    assert payload["saved_count"] == 1
    assert payload["candidates"][0]["title"] == "React migration candidate"


def test_event_crud_endpoints() -> None:
    client = TestClient(app)

    create_response = client.post(
        "/events",
        json={
            "title": "Sprint API test event",
            "start_at": "2026-06-23T09:00:00",
            "end_at": "2026-06-23T10:00:00",
            "description": "created by backend test",
            "location": "test room",
            "importance": 4,
        },
    )
    assert create_response.status_code == 201
    created = create_response.json()
    event_id = created["id"]
    assert created["title"] == "Sprint API test event"
    assert created["source"] == "local"

    update_response = client.put(
        f"/events/{event_id}",
        json={
            "title": "Sprint API test event updated",
            "end_at": "2026-06-23T11:00:00",
            "importance": 5,
        },
    )
    assert update_response.status_code == 200
    updated = update_response.json()
    assert updated["title"] == "Sprint API test event updated"
    assert updated["importance"] == 5

    delete_response = client.delete(f"/events/{event_id}")
    assert delete_response.status_code == 204

    missing_delete_response = client.delete(f"/events/{event_id}")
    assert missing_delete_response.status_code == 404


def test_ai_chat_endpoint(monkeypatch) -> None:
    client = TestClient(app)

    def fake_answer_schedule_question(question, events) -> AiChatResult:
        return AiChatResult(answer=f"answer for {question}", matched_event_ids=[1])

    monkeypatch.setattr(backend_main, "answer_schedule_question", fake_answer_schedule_question)

    response = client.post("/ai/chat", json={"question": "이번 주 일정 알려줘"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["answer"] == "answer for 이번 주 일정 알려줘"
    assert payload["matched_event_ids"] == [1]
    assert payload["intent"] == "query"
