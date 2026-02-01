"""Tests for vault endpoints in the Digital FTE API."""

from pathlib import Path


def test_list_inbox_folder(client, temp_vault):
    """Test listing files in the Inbox folder."""
    response = client.get("/api/vault/folder/Inbox")
    assert response.status_code == 200

    data = response.json()
    assert data["folder"] == "Inbox"
    assert data["count"] == 0
    assert data["files"] == []


def test_list_needs_action_folder(client, temp_vault):
    """Test listing files in the Needs_Action folder."""
    response = client.get("/api/vault/folder/Needs_Action")
    assert response.status_code == 200

    data = response.json()
    assert data["folder"] == "Needs_Action"
    assert data["count"] == 0
    assert data["files"] == []


def test_list_pending_approval_folder(client, temp_vault):
    """Test listing files in the Pending_Approval folder."""
    response = client.get("/api/vault/folder/Pending_Approval")
    assert response.status_code == 200

    data = response.json()
    assert data["folder"] == "Pending_Approval"
    assert data["count"] == 0
    assert data["files"] == []


def test_list_approved_folder(client, temp_vault):
    """Test listing files in the Approved folder."""
    response = client.get("/api/vault/folder/Approved")
    assert response.status_code == 200

    data = response.json()
    assert data["folder"] == "Approved"
    assert data["count"] == 0
    assert data["files"] == []


def test_list_done_folder(client, temp_vault):
    """Test listing files in the Done folder."""
    response = client.get("/api/vault/folder/Done")
    assert response.status_code == 200

    data = response.json()
    assert data["folder"] == "Done"
    assert data["count"] == 0
    assert data["files"] == []


def test_add_file_to_inbox(client, temp_vault):
    """Test adding a file to the Inbox folder."""
    # Create a test file in the inbox
    inbox_dir = temp_vault / "Inbox"
    test_file = inbox_dir / "test_task.md"

    content = """---
title: Test Task
status: new
priority: medium
---
# Test Task

This is a test task in the inbox.
"""
    test_file.write_text(content)

    response = client.get("/api/vault/folder/Inbox")
    assert response.status_code == 200

    data = response.json()
    assert data["folder"] == "Inbox"
    assert data["count"] == 1
    assert len(data["files"]) == 1
    assert data["files"][0]["filename"] == "test_task.md"
    assert data["files"][0]["title"] == "Test Task"


def test_get_file_content(client, temp_vault):
    """Test getting the content of a specific file."""
    # Create a test file
    inbox_dir = temp_vault / "Inbox"
    test_file = inbox_dir / "content_test.md"

    content = """---
title: Content Test
status: new
---
# Content Test File

This file is for content testing.
"""
    test_file.write_text(content)

    response = client.get("/api/vault/file/Inbox/content_test.md")
    assert response.status_code == 200

    data = response.json()
    assert data["filename"] == "content_test.md"
    assert data["folder"] == "Inbox"
    assert "Content Test" in data["frontmatter"]["title"]
    assert "# Content Test File" in data["body"]