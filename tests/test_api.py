import os
from datetime import date

os.environ["DATABASE_URL"] = "sqlite:///./test_crowd.db"
os.environ["API_TOKEN"] = "test-token"

from fastapi.testclient import TestClient
from backend.app.main import app


def test_event_is_idempotent_and_never_negative():
    with TestClient(app) as client:
        first = client.post("/api/events", headers={"Authorization": "Bearer test-token"}, json={"event_type": "exit", "source_event_id": "x"})
        second = client.post("/api/events", headers={"Authorization": "Bearer test-token"}, json={"event_type": "exit", "source_event_id": "x"})
        assert first.status_code == 200
        assert first.json()["occupancy"] == 0
        assert second.json()["duplicate"] is True


def test_manual_record_requires_auth():
    with TestClient(app) as client:
        response = client.post("/api/history/manual", json={"observation_date": str(date.today()), "hour": 10, "people_present": 42})
        assert response.status_code == 401
