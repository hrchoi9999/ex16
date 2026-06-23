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
