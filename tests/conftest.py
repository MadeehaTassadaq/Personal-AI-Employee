"""Test configuration and fixtures for the Digital FTE API."""

import pytest
import tempfile
import shutil
import sys
from pathlib import Path
from unittest.mock import patch

from backend.models.schemas import TaskFile, VaultFolderResponse
from fastapi.testclient import TestClient


@pytest.fixture
def temp_vault():
    """Create a temporary vault directory for testing."""
    temp_dir = tempfile.mkdtemp()
    vault_path = Path(temp_dir) / "AI_Employee_Vault"
    vault_path.mkdir()

    # Create all required subdirectories
    for subdir in ["Inbox", "Needs_Action", "Pending_Approval", "Approved", "Done", "Logs", "Plans", "Reports", "Audit"]:
        (vault_path / subdir).mkdir()

    yield vault_path

    # Cleanup
    shutil.rmtree(temp_dir)


@pytest.fixture
def client(temp_vault):
    """Create a test client with mocked vault path."""
    # Temporarily set the environment variable and import app after
    with patch('os.getenv', lambda key, default=None: str(temp_vault) if key == "VAULT_PATH" else default):
        # Import the app after setting the environment
        from backend.main import app
        with TestClient(app) as c:
            yield c