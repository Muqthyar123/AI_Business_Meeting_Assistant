"""Tests for FastAPI health check and root endpoints."""

from unittest.mock import patch
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_root_endpoint():
    """Verify root endpoint returns API metadata and documentation links."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "AI Business Meeting Assistant"
    assert "version" in data
    assert data["docs"] == "/docs"
    assert data["health"] == "/api/health"


def test_health_endpoint_healthy():
    """Verify health endpoint response when MongoDB is connected."""
    with patch("app.main.ping_database", return_value=True):
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["api_status"] == "running"
        assert data["database_status"] == "connected"
        assert "version" in data
        assert "timestamp" in data
        # Ensure no sensitive credentials or URIs are present
        assert "mongodb://" not in str(data)
        assert "password" not in str(data)


def test_health_endpoint_degraded_when_db_down():
    """Verify health endpoint response and 503 status when MongoDB is disconnected."""
    with patch("app.main.ping_database", return_value=False):
        response = client.get("/api/health")
        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "degraded"
        assert data["api_status"] == "running"
        assert data["database_status"] == "disconnected"
        assert "version" in data
        # Ensure no sensitive info leaked
        assert "mongodb://" not in str(data)
