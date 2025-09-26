import pytest
from fastapi.testclient import TestClient
from src.core.api_server import app
from src.core.security import api_key_auth

@pytest.fixture
def client():
    return TestClient(app)

def test_receive_log(client, monkeypatch):
    # Mock auth dependency
    monkeypatch.setattr("src.core.api_server.api_key_auth", lambda: True)
    response = client.post("/logs", json={"level": "info", "message": "test", "source": "app"})
    assert response.status_code == 200
    assert response.json() == {"status": "enqueued"}

def test_receive_log_unauthorized(client):
    response = client.post("/logs", json={"level": "info", "message": "test", "source": "app"})
    assert response.status_code == 403

def test_replay_logs(client, monkeypatch):
    # Mock auth and DB (placeholder; integrate with fixtures for DB)
    monkeypatch.setattr("src.core.api_server.api_key_auth", lambda: True)
    response = client.get("/replay/test_id")
    assert response.status_code == 200
    assert "logs" in response.json() or "error" in response.json() 