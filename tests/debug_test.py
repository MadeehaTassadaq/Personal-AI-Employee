"""Debug test to see what's in the Pending_Approval directory."""

import json
from pathlib import Path
from datetime import datetime

import pytest
from fastapi.testclient import TestClient


def test_debug_pending_approvals(client, temp_vault):
    """Debug test to see what's in the Pending_Approval directory."""
    pending_approval_dir = temp_vault / "Pending_Approval"

    # Print what files exist before API call
    print(f"Files in Pending_Approval before API call: {[str(f) for f in pending_approval_dir.glob('*')]}")

    response = client.get("/api/approvals/pending")
    print(f"Response status: {response.status_code}")
    print(f"Response data: {response.json()}")

    # Print what files exist after API call
    print(f"Files in Pending_Approval after API call: {[str(f) for f in pending_approval_dir.glob('*')]}")

    assert response.status_code == 200