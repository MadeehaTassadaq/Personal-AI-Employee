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
    approved_count = count_files("Approved")

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

    # Note: Dashboard updates are handled by the scheduler separately
    # to avoid excessive file writes on every status check

    return StatusResponse(
        system=system_status,
        watchers=watchers,
        pending_approvals=pending_count,
        inbox_count=inbox_count,
        needs_action_count=needs_action_count,
        approved_count=approved_count
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


@router.get("/credentials")
async def check_credentials():
    """Check which platforms have properly configured credentials."""
    credentials_dir = Path("./credentials")

    return {
        "dry_run": os.getenv("DRY_RUN", "true").lower() == "true",
        "platforms": {
            "facebook": {
                "configured": bool(os.getenv("FACEBOOK_PAGE_ACCESS_TOKEN") and os.getenv("FACEBOOK_PAGE_ID")),
                "required_env_vars": ["FACEBOOK_PAGE_ACCESS_TOKEN", "FACEBOOK_PAGE_ID"]
            },
            "linkedin": {
                "configured": bool(os.getenv("LINKEDIN_ACCESS_TOKEN")),
                "required_env_vars": ["LINKEDIN_ACCESS_TOKEN"]
            },
            "instagram": {
                "configured": bool(os.getenv("INSTAGRAM_ACCESS_TOKEN") and os.getenv("INSTAGRAM_BUSINESS_ACCOUNT_ID")),
                "required_env_vars": ["INSTAGRAM_ACCESS_TOKEN", "INSTAGRAM_BUSINESS_ACCOUNT_ID"]
            },
            "twitter": {
                "configured": bool(
                    os.getenv("TWITTER_API_KEY") and
                    os.getenv("TWITTER_API_SECRET") and
                    os.getenv("TWITTER_ACCESS_TOKEN") and
                    os.getenv("TWITTER_ACCESS_TOKEN_SECRET")
                ),
                "required_env_vars": [
                    "TWITTER_API_KEY",
                    "TWITTER_API_SECRET",
                    "TWITTER_ACCESS_TOKEN",
                    "TWITTER_ACCESS_TOKEN_SECRET"
                ]
            },
            "whatsapp": {
                "configured": (credentials_dir / "whatsapp_session").exists(),
                "required_files": ["./credentials/whatsapp_session"],
                "note": "Run WhatsApp MCP server once and scan QR code to establish session"
            },
            "gmail": {
                "configured": (credentials_dir / "gmail_token.json").exists(),
                "required_files": ["./credentials/gmail_token.json"],
                "note": "Run Gmail OAuth flow to generate token file"
            },
            "calendar": {
                "configured": (credentials_dir / "calendar_token.json").exists(),
                "required_files": ["./credentials/calendar_token.json"],
                "note": "Run Calendar OAuth flow to generate token file"
            }
        },
        "approved_folder": {
            "path": str(VAULT_PATH / "Approved"),
            "file_count": count_files("Approved"),
            "files_awaiting_execution": count_files("Approved")
        }
    }
