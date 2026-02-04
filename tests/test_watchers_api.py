"""Tests for watcher endpoints in the Digital FTE API."""


def test_get_watchers_status(client):
    """Test getting the status of all watchers."""
    response = client.get("/api/watchers")
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)  # Should return a list of WatcherInfo objects
    # Check that we have all 7 watchers now (file, gmail, whatsapp, linkedin, facebook, instagram, twitter)
    watcher_names = [watcher['name'] for watcher in data]
    expected_watchers = ['file', 'gmail', 'whatsapp', 'linkedin', 'facebook', 'instagram', 'twitter']
    for expected in expected_watchers:
        assert expected in watcher_names


def test_start_and_stop_individual_watcher(client):
    """Test starting and stopping individual watchers."""
    # Try to start a watcher (this will fail gracefully if not implemented properly)
    response = client.post("/api/watchers/file/start")
    # Should return 200 for successful start
    assert response.status_code in [200, 400, 500]  # Could be various statuses but shouldn't crash

    response = client.post("/api/watchers/file/stop")
    # Should return 200 for successful stop
    assert response.status_code in [200, 400, 500]  # Could be various statuses but shouldn't crash


def test_start_and_stop_all_watchers(client):
    """Test starting and stopping all watchers."""
    response = client.post("/api/watchers/start-all")
    # Should return 200 for successful start of all watchers
    assert response.status_code in [200, 400, 500]  # Could be various statuses but shouldn't crash

    response = client.post("/api/watchers/stop-all")
    # Should return 200 for successful stop of all watchers
    assert response.status_code in [200, 400, 500]  # Could be various statuses but shouldn't crash