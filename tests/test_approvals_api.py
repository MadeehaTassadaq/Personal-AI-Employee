"""Tests for approval endpoints in the Digital FTE API."""

import json
from pathlib import Path
from datetime import datetime

import pytest
from fastapi.testclient import TestClient


def test_list_pending_approvals_empty(client, temp_vault):
    """Test listing pending approvals when none exist."""
    # Clear any files that may have been created during startup
    import shutil
    pending_approval_dir = temp_vault / "Pending_Approval"
    for file_path in pending_approval_dir.glob("*.md"):
        if file_path.name != ".gitkeep":
            file_path.unlink()

    response = client.get("/api/approvals/pending")
    assert response.status_code == 200

    data = response.json()
    assert data["folder"] == "Pending_Approval"
    assert data["count"] == 0
    assert data["files"] == []


def test_list_pending_approvals_with_items(client, temp_vault):
    """Test listing pending approvals when items exist."""
    # Create a test approval file
    pending_approval_dir = temp_vault / "Pending_Approval"
    test_file = pending_approval_dir / "test_approval.md"

    content = """---
title: Test Approval
type: email
created: "2026-02-01T10:00:00"
---
# Test Approval Task

This is a test approval task.
"""
    test_file.write_text(content)

    response = client.get("/api/approvals/pending")
    assert response.status_code == 200

    data = response.json()
    assert data["folder"] == "Pending_Approval"
    assert data["count"] == 1
    assert len(data["files"]) == 1
    assert data["files"][0]["filename"] == "test_approval.md"
    assert data["files"][0]["title"] == "Test Approval"


def test_get_specific_pending_approval(client, temp_vault):
    """Test getting details of a specific pending approval."""
    # Create a test approval file
    pending_approval_dir = temp_vault / "Pending_Approval"
    test_file = pending_approval_dir / "specific_approval.md"

    content = """---
title: Specific Approval
type: linkedin
created: "2026-02-01T11:00:00"
---
# Specific Approval Task

This is a specific approval task.
"""
    test_file.write_text(content)

    response = client.get("/api/approvals/pending/specific_approval.md")
    assert response.status_code == 200

    data = response.json()
    assert data["filename"] == "specific_approval.md"
    assert data["type"] == "linkedin"
    assert data["created"] == "2026-02-01T11:00:00"
    assert "Specific Approval Task" in data["content"]


def test_get_nonexistent_pending_approval(client, temp_vault):
    """Test getting a nonexistent pending approval."""
    response = client.get("/api/approvals/pending/nonexistent.md")
    assert response.status_code == 404


def test_approve_action_success(client, temp_vault):
    """Test successfully approving an action."""
    # Create a test approval file
    pending_approval_dir = temp_vault / "Pending_Approval"
    test_file = pending_approval_dir / "approval_test.md"

    content = """---
title: Approval Test
type: email
created: "2026-02-01T12:00:00"
---
# Approval Test Task

This is a test task for approval.
"""
    test_file.write_text(content)

    # Submit approval request
    approval_request = {
        "filename": "approval_test.md",
        "approved": True,
        "notes": "Approved for execution"
    }

    response = client.post("/api/approvals/approve", json=approval_request)
    assert response.status_code == 200

    data = response.json()
    assert data["filename"] == "approval_test.md"
    assert data["approved"] is True
    assert "Approved" in data["new_location"]
    assert data["message"] == "Action approved"

    # Verify file was moved to Approved folder
    approved_file = temp_vault / "Approved" / "approval_test.md"
    assert approved_file.exists()


def test_reject_action(client, temp_vault):
    """Test rejecting an action."""
    # Create a test approval file
    pending_approval_dir = temp_vault / "Pending_Approval"
    test_file = pending_approval_dir / "rejection_test.md"

    content = """---
title: Rejection Test
type: whatsapp
created: "2026-02-01T13:00:00"
---
# Rejection Test Task

This is a test task for rejection.
"""
    test_file.write_text(content)

    # Submit rejection request
    approval_request = {
        "filename": "rejection_test.md",
        "approved": False,
        "notes": "Rejected due to inappropriate content"
    }

    response = client.post("/api/approvals/approve", json=approval_request)
    assert response.status_code == 200

    data = response.json()
    assert data["filename"] == "rejection_test.md"
    assert data["approved"] is False
    assert "Done" in data["new_location"]
    assert data["message"] == "Action rejected"

    # Verify file was moved to Done folder
    done_file = temp_vault / "Done" / "rejection_test.md"
    assert done_file.exists()


def test_approve_nonexistent_file(client, temp_vault):
    """Test approving a nonexistent file."""
    approval_request = {
        "filename": "nonexistent.md",
        "approved": True
    }

    response = client.post("/api/approvals/approve", json=approval_request)
    assert response.status_code == 404


def test_list_approved_actions_empty(client, temp_vault):
    """Test listing approved actions when none exist."""
    response = client.get("/api/approvals/approved")
    assert response.status_code == 200

    data = response.json()
    assert data["folder"] == "Approved"
    assert data["count"] == 0
    assert data["files"] == []


def test_list_approved_actions_with_items(client, temp_vault):
    """Test listing approved actions when items exist."""
    # Create a test approved file
    approved_dir = temp_vault / "Approved"
    test_file = approved_dir / "test_approved.md"

    content = """---
title: Test Approved
type: email
approved_at: "2026-02-01T14:00:00"
---
# Test Approved Task

This is a test approved task.
"""
    test_file.write_text(content)

    response = client.get("/api/approvals/approved")
    assert response.status_code == 200

    data = response.json()
    assert data["folder"] == "Approved"
    assert data["count"] == 1
    assert len(data["files"]) == 1
    assert data["files"][0]["filename"] == "test_approved.md"
    assert data["files"][0]["title"] == "Test Approved"


def test_mark_executed_success(client, temp_vault):
    """Test marking an approved action as executed."""
    # Create a test approved file
    approved_dir = temp_vault / "Approved"
    test_file = approved_dir / "to_execute.md"

    content = """---
title: To Execute
type: email
approved_at: "2026-02-01T15:00:00"
---
# To Execute Task

This is a task to be executed.
"""
    test_file.write_text(content)

    # Mark as executed
    response = client.post("/api/approvals/execute/to_execute.md", params={"notes": "Successfully executed"})
    assert response.status_code == 200

    data = response.json()
    assert data["filename"] == "to_execute.md"
    assert data["status"] == "completed"
    assert "Done" in data["new_location"]

    # Verify file was moved to Done folder
    done_file = temp_vault / "Done" / "to_execute.md"
    assert done_file.exists()