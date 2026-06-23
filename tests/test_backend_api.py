from __future__ import annotations

from fastapi.testclient import TestClient

from backend.app.main import app


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
