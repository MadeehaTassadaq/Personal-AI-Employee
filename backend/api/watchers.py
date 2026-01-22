"""Watcher control API endpoints."""

import os
import json
from pathlib import Path
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException

from ..models.schemas import WatcherInfo, WatcherResponse, WatcherStatus

router = APIRouter()

VAULT_PATH = Path(os.getenv("VAULT_PATH", "./vault"))
STATE_FILE = Path(__file__).parent.parent / "state.json"

# Available watchers
AVAILABLE_WATCHERS = ["file", "gmail", "whatsapp", "linkedin"]


def load_state() -> dict:
    """Load system state from file."""
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except json.JSONDecodeError:
            pass
    return {"system": "stopped", "watchers": {}, "last_updated": None}


def save_state(state: dict) -> None:
    """Save system state to file."""
    state["last_updated"] = datetime.now().isoformat()
    STATE_FILE.write_text(json.dumps(state, indent=2))


def get_watcher_events_today(watcher_name: str) -> int:
    """Count events from a watcher today."""
    log_file = VAULT_PATH / "Logs" / f"{datetime.now().strftime('%Y-%m-%d')}.json"
    if not log_file.exists():
        return 0

    try:
        logs = json.loads(log_file.read_text())
        return sum(1 for log in logs if log.get("watcher", "").lower() == watcher_name.lower())
    except (json.JSONDecodeError, KeyError):
        return 0


@router.get("")
async def list_watchers() -> list[WatcherInfo]:
    """List all available watchers and their status."""
    state = load_state()
    watchers = []

    for name in AVAILABLE_WATCHERS:
        status_str = state.get("watchers", {}).get(name, "stopped")
        try:
            status = WatcherStatus(status_str)
        except ValueError:
            status = WatcherStatus.STOPPED

        watchers.append(WatcherInfo(
            name=name,
            status=status,
            events_today=get_watcher_events_today(name)
        ))

    return watchers


@router.get("/{name}")
async def get_watcher(name: str) -> WatcherInfo:
    """Get a specific watcher's status."""
    if name not in AVAILABLE_WATCHERS:
        raise HTTPException(status_code=404, detail=f"Watcher '{name}' not found")

    state = load_state()
    status_str = state.get("watchers", {}).get(name, "stopped")

    try:
        status = WatcherStatus(status_str)
    except ValueError:
        status = WatcherStatus.STOPPED

    return WatcherInfo(
        name=name,
        status=status,
        events_today=get_watcher_events_today(name)
    )


@router.post("/{name}/start")
async def start_watcher(name: str) -> WatcherResponse:
    """Start a watcher."""
    if name not in AVAILABLE_WATCHERS:
        raise HTTPException(status_code=404, detail=f"Watcher '{name}' not found")

    state = load_state()

    if "watchers" not in state:
        state["watchers"] = {}

    state["watchers"][name] = "running"
    state["system"] = "running"
    save_state(state)

    return WatcherResponse(
        name=name,
        status=WatcherStatus.RUNNING,
        message=f"Watcher '{name}' started"
    )


@router.post("/{name}/stop")
async def stop_watcher(name: str) -> WatcherResponse:
    """Stop a watcher."""
    if name not in AVAILABLE_WATCHERS:
        raise HTTPException(status_code=404, detail=f"Watcher '{name}' not found")

    state = load_state()

    if "watchers" not in state:
        state["watchers"] = {}

    state["watchers"][name] = "stopped"

    # Check if any watchers still running
    if not any(v == "running" for v in state.get("watchers", {}).values()):
        state["system"] = "stopped"

    save_state(state)

    return WatcherResponse(
        name=name,
        status=WatcherStatus.STOPPED,
        message=f"Watcher '{name}' stopped"
    )


@router.post("/start-all")
async def start_all_watchers() -> dict:
    """Start all watchers."""
    state = load_state()

    if "watchers" not in state:
        state["watchers"] = {}

    for name in AVAILABLE_WATCHERS:
        state["watchers"][name] = "running"

    state["system"] = "running"
    save_state(state)

    return {
        "message": "All watchers started",
        "watchers": state["watchers"]
    }


@router.post("/stop-all")
async def stop_all_watchers() -> dict:
    """Stop all watchers."""
    state = load_state()

    if "watchers" not in state:
        state["watchers"] = {}

    for name in AVAILABLE_WATCHERS:
        state["watchers"][name] = "stopped"

    state["system"] = "stopped"
    save_state(state)

    return {
        "message": "All watchers stopped",
        "watchers": state["watchers"]
    }
