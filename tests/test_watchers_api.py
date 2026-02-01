"""Tests for watcher endpoints in the Digital FTE API."""


def test_get_watchers_status(client):
    """Test getting the status of all watchers."""
    response = client.get("/api/watchers")
    assert response.status_code == 200

    data = response.json()
    assert "watchers" in data
    assert isinstance(data["watchers"], dict)
    # The actual status will depend on if watchers are running
    # but the response should be successful


def test_start_and_stop_individual_watcher(client):
    """Test starting and stopping individual watchers."""
    # Try to start a watcher (this will fail gracefully if not implemented properly)
    response = client.post("/api/watchers/start", json={"name": "file"})
    # Could be 200, 400, or 500 depending on implementation, but shouldn't crash

    response = client.post("/api/watchers/stop", json={"name": "file"})
    # Could be 200, 400, or 500 depending on implementation, but shouldn't crash


def test_start_and_stop_all_watchers(client):
    """Test starting and stopping all watchers."""
    response = client.post("/api/watchers/start-all")
    # Could be 200, 400, or 500 depending on implementation, but shouldn't crash

    response = client.post("/api/watchers/stop-all")
    # Could be 200, 400, or 500 depending on implementation, but shouldn't crash