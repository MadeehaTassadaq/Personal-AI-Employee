"""Orchestrator service for managing watchers and task processing."""

import os
import json
import subprocess
import threading
from pathlib import Path
from datetime import datetime
from typing import Optional

from ..api.status import load_state, save_state


class Orchestrator:
    """Manages watchers and coordinates task processing."""

    def __init__(self, vault_path: str):
        """Initialize the orchestrator.

        Args:
            vault_path: Path to the Obsidian vault
        """
        self.vault_path = Path(vault_path)
        self.watcher_processes: dict[str, subprocess.Popen] = {}
        self.watcher_threads: dict[str, threading.Thread] = {}

    def start_watcher(self, name: str) -> bool:
        """Start a watcher process.

        Args:
            name: Name of the watcher (file, gmail, whatsapp, linkedin)

        Returns:
            True if started successfully
        """
        if name in self.watcher_processes:
            return True  # Already running

        # Map watcher names to modules
        watcher_map = {
            "file": "watchers.file_watcher",
            "gmail": "watchers.gmail_watcher",
            "whatsapp": "watchers.whatsapp_watcher",
            "linkedin": "watchers.linkedin_watcher",
            "facebook": "watchers.facebook_watcher",
            "instagram": "watchers.instagram_watcher",
            "twitter": "watchers.twitter_watcher"
        }

        if name not in watcher_map:
            return False

        try:
            # Start watcher as subprocess
            process = subprocess.Popen(
                ["python", "-m", watcher_map[name], str(self.vault_path)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            self.watcher_processes[name] = process

            # Update state
            state = load_state()
            if "watchers" not in state:
                state["watchers"] = {}
            state["watchers"][name] = "running"
            state["system"] = "running"
            save_state(state)

            return True

        except Exception as e:
            print(f"Error starting watcher {name}: {e}")
            return False

    def stop_watcher(self, name: str) -> bool:
        """Stop a watcher process.

        Args:
            name: Name of the watcher

        Returns:
            True if stopped successfully
        """
        if name not in self.watcher_processes:
            return True  # Not running

        try:
            process = self.watcher_processes[name]
            process.terminate()
            process.wait(timeout=5)
            del self.watcher_processes[name]

            # Update state
            state = load_state()
            if "watchers" in state and name in state["watchers"]:
                state["watchers"][name] = "stopped"

            # Check if any watchers still running
            if not any(v == "running" for v in state.get("watchers", {}).values()):
                state["system"] = "stopped"

            save_state(state)
            return True

        except Exception as e:
            print(f"Error stopping watcher {name}: {e}")
            return False

    def start_all_watchers(self) -> dict[str, bool]:
        """Start all watchers.

        Returns:
            Dict of watcher names to success status
        """
        results = {}
        for name in ["file", "gmail", "whatsapp", "linkedin", "facebook", "instagram", "twitter"]:
            results[name] = self.start_watcher(name)
        return results

    def stop_all_watchers(self) -> dict[str, bool]:
        """Stop all watchers.

        Returns:
            Dict of watcher names to success status
        """
        results = {}
        for name in list(self.watcher_processes.keys()):
            results[name] = self.stop_watcher(name)
        return results

    def get_watcher_status(self) -> dict[str, str]:
        """Get status of all watchers.

        Returns:
            Dict of watcher names to status
        """
        state = load_state()
        return state.get("watchers", {})

    def process_inbox(self) -> list[str]:
        """Process all files in the Inbox folder.

        Returns:
            List of processed file names
        """
        inbox = self.vault_path / "Inbox"
        processed = []

        for file_path in inbox.glob("*.md"):
            if file_path.name == ".gitkeep":
                continue

            # Move to Needs_Action
            dest = self.vault_path / "Needs_Action" / file_path.name
            file_path.rename(dest)
            processed.append(file_path.name)

            self._log_event("inbox_processed", {
                "file": file_path.name
            })

        return processed

    def _log_event(self, event_type: str, details: dict) -> None:
        """Log an event.

        Args:
            event_type: Type of event
            details: Event details
        """
        log_file = self.vault_path / "Logs" / f"{datetime.now().strftime('%Y-%m-%d')}.json"

        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "watcher": "Orchestrator",
            "event": event_type,
            **details
        }

        logs = []
        if log_file.exists():
            try:
                logs = json.loads(log_file.read_text())
            except json.JSONDecodeError:
                logs = []

        logs.append(log_entry)
        log_file.write_text(json.dumps(logs, indent=2))


# Global orchestrator instance
_orchestrator: Optional[Orchestrator] = None


def get_orchestrator() -> Orchestrator:
    """Get or create the global orchestrator instance."""
    global _orchestrator
    if _orchestrator is None:
        vault_path = os.getenv("VAULT_PATH", "./vault")
        _orchestrator = Orchestrator(vault_path)
    return _orchestrator
