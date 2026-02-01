"""Tests for status endpoints in the Digital FTE API."""

from fastapi.testclient import TestClient


def test_root_endpoint(client):
    """Test the root endpoint."""
    response = client.get("/")
    assert response.status_code == 200

    data = response.json()
    assert "name" in data
    assert "Digital FTE API" in data["name"]
    assert "status" in data
    assert data["status"] == "running"


def test_health_endpoint(client):
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "healthy"


def test_status_endpoint(client):
    """Test the status endpoint."""
    response = client.get("/api/status")
    assert response.status_code == 200

    data = response.json()
    assert "system" in data
    assert "watchers" in data
    assert "pending_approvals" in data
    assert "inbox_count" in data
    assert "needs_action_count" in data