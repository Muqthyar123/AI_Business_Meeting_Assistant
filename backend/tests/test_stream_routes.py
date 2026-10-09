"""Unit and integration tests for real-time live stream endpoints."""

import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_publish_live_speech_segment(client):
    """Test publishing a speech segment via HTTP POST."""
    payload = {
        "text": "Elena reviewed the quarterly sprint deliverables.",
        "timestamp": "14:30:00",
        "mode": "meeting",
        "segment_id": 1,
    }
    response = client.post("/api/stream/publish", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "broadcasted"
    assert "active_clients" in data


def test_publish_empty_segment_raises_400(client):
    """Test publishing an empty segment raises a 400 Bad Request."""
    payload = {
        "text": "   ",
        "mode": "meeting",
    }
    response = client.post("/api/stream/publish", json=payload)
    assert response.status_code == 400
    assert "cannot be empty" in response.json()["detail"].lower()


def test_get_stream_history(client):
    """Test retrieving recent stream history."""
    # First publish a segment
    client.post(
        "/api/stream/publish",
        json={"text": "Historical test segment", "mode": "meeting"},
    )

    response = client.get("/api/stream/history")
    assert response.status_code == 200
    data = response.json()
    assert "history" in data
    assert "active_clients" in data
    assert any(item.get("text") == "Historical test segment" for item in data["history"])


def test_websocket_stream_ping_and_speech():
    """Test WebSocket connection, ping, and speech broadcast."""
    with TestClient(app) as test_client:
        with test_client.websocket_connect("/api/stream/ws") as websocket:
            # 1. Test ping
            websocket.send_json({"type": "ping"})
            data = websocket.receive_json()
            assert data["type"] == "pong"

            # 2. Test speech segment broadcast
            websocket.send_json({
                "type": "speech_segment",
                "text": "Live meeting test via websocket",
                "mode": "meeting",
                "timestamp": "15:00:00",
            })
            broadcasted = websocket.receive_json()
            assert broadcasted["type"] == "speech_segment"
            assert broadcasted["text"] == "Live meeting test via websocket"
            assert broadcasted["mode"] == "meeting"
