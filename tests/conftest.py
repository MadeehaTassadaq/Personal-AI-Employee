"""Test configuration and fixtures for the Digital FTE API."""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch

from backend.main import app
from backend.models.schemas import TaskFile, VaultFolderResponse
from fastapi.testclient import TestClient


@pytest.fixture
def temp_vault():
    """Create a temporary vault directory for testing."""
    temp_dir = tempfile.mkdtemp()
    vault_path = Path(temp_dir) / "AI_Employee_Vault"
    vault_path.mkdir()

    # Create all required subdirectories
    for subdir in ["Inbox", "Needs_Action", "Pending_Approval", "Approved", "Done", "Logs", "Plans"]:
        (vault_path / subdir).mkdir()

    # Mock the VAULT_PATH environment variable
    with patch("os.getenv", lambda key, default=None: str(vault_path) if key == "VAULT_PATH" else default):
        yield vault_path

        # Cleanup
        shutil.rmtree(temp_dir)


@pytest.fixture
def client(temp_vault):
    """Create a test client with mocked vault path."""
    with TestClient(app) as c:
        yield c