"""Status API endpoints."""

import os
import json
from pathlib import Path
from datetime import datetime

from fastapi import APIRouter, HTTPException

from ..models.schemas import StatusResponse, SystemStatus, WatcherStatus

router = APIRouter()

VAULT_PATH = Path(os.getenv("VAULT_PATH", "./vault"))
STATE_FILE = Path(__file__).parent.parent / "state.json"


def load_state() -> dict:
    """Load system state from file."""
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except json.JSONDecodeError:
            pass
    return {
        "system": "stopped",
        "watchers": {},
        "last_updated": None
    }


def save_state(state: dict) -> None:
    """Save system state to file."""
    state["last_updated"] = datetime.now().isoformat()
    STATE_FILE.write_text(json.dumps(state, indent=2))


def count_files(folder: str) -> int:
    """Count .md files in a vault folder."""
    folder_path = VAULT_PATH / folder
    if not folder_path.exists():
        return 0
    return len([f for f in folder_path.glob("*.md") if f.name != ".gitkeep"])


@router.get("", response_model=StatusResponse)
async def get_status():
    """Get current system status."""
    state = load_state()

    # Count files in each folder
    inbox_count = count_files("Inbox")
    needs_action_count = count_files("Needs_Action")
    pending_count = count_files("Pending_Approval")

    # Convert watcher statuses
    watchers = {}
    for name, status in state.get("watchers", {}).items():
        try:
            watchers[name] = WatcherStatus(status)
        except ValueError:
            watchers[name] = WatcherStatus.STOPPED

    # Determine system status
    system_status = SystemStatus.STOPPED
    if any(s == WatcherStatus.RUNNING for s in watchers.values()):
        system_status = SystemStatus.RUNNING
    if any(s == WatcherStatus.ERROR for s in watchers.values()):
        system_status = SystemStatus.ERROR

    return StatusResponse(
        system=system_status,
        watchers=watchers,
        pending_approvals=pending_count,
        inbox_count=inbox_count,
        needs_action_count=needs_action_count
    )


@router.post("/start")
async def start_system():
    """Start the Digital FTE system."""
    state = load_state()
    state["system"] = "running"
    save_state(state)
    return {"status": "started", "message": "System started"}


@router.post("/stop")
async def stop_system():
    """Stop the Digital FTE system."""
    state = load_state()
    state["system"] = "stopped"
    # Stop all watchers
    for watcher in state.get("watchers", {}):
        state["watchers"][watcher] = "stopped"
    save_state(state)
    return {"status": "stopped", "message": "System stopped"}
