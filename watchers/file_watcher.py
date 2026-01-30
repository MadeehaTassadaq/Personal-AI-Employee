"""Filesystem watcher for Inbox folder with automatic task processing."""

import json
import re
import shutil
import time
from pathlib import Path
from datetime import datetime
from typing import Callable, Optional

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent


def process_task(file_path: Path, vault_path: Path) -> None:
    """Process a task file through the workflow: Inbox → Needs_Action → Done.

    Args:
        file_path: Path to the task file
        vault_path: Path to the vault root
    """
    needs_action = vault_path / "Needs_Action"
    done = vault_path / "Done"
    logs = vault_path / "Logs"

    # Ensure directories exist
    needs_action.mkdir(exist_ok=True)
    done.mkdir(exist_ok=True)
    logs.mkdir(exist_ok=True)

    # Read file content
    content = file_path.read_text()
    print(f"[PROCESS] Reading: {file_path.name}")
    print(f"[PROCESS] Content preview: {content[:200]}...")

    # Update frontmatter status and move to Needs_Action
    timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

    # Update status in frontmatter
    if "status:" in content:
        content = re.sub(r"status:\s*\w+", "status: in_progress", content)

    # Add processing log entry
    if "## Processing Log" not in content:
        content += f"\n\n## Processing Log\n- **{timestamp}**: Moved from Inbox to Needs_Action\n"
    else:
        content = content.rstrip() + f"\n- **{timestamp}**: Moved from Inbox to Needs_Action\n"

    # Write to Needs_Action
    needs_action_file = needs_action / file_path.name
    needs_action_file.write_text(content)
    print(f"[PROCESS] Moved to Needs_Action: {file_path.name}")

    # Remove from Inbox
    file_path.unlink()

    # Simulate processing delay
    time.sleep(1)

    # Read updated content
    content = needs_action_file.read_text()

    # Update status to completed
    content = re.sub(r"status:\s*\w+", "status: completed", content)

    # Mark checkboxes as done
    content = re.sub(r"- \[ \]", "- [x]", content)

    # Add completion log
    timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    content = content.rstrip() + f"\n- **{timestamp}**: Task completed, moved to Done\n"

    # Write to Done
    done_file = done / file_path.name
    done_file.write_text(content)
    print(f"[PROCESS] Completed and moved to Done: {file_path.name}")

    # Remove from Needs_Action
    needs_action_file.unlink()

    # Log the action
    log_file = logs / f"{datetime.now().strftime('%Y-%m-%d')}.json"
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "watcher": "FileWatcher",
        "event": "task_completed",
        "file": file_path.name,
        "workflow": "Inbox → Needs_Action → Done"
    }

    logs_data = []
    if log_file.exists():
        try:
            logs_data = json.loads(log_file.read_text())
        except json.JSONDecodeError:
            logs_data = []

    logs_data.append(log_entry)
    log_file.write_text(json.dumps(logs_data, indent=2))
    print(f"[PROCESS] Logged action to: {log_file.name}")


class InboxHandler(FileSystemEventHandler):
    """Handler for filesystem events in the Inbox folder."""

    def __init__(self, vault_path: str, callback: Optional[Callable] = None):
        self.vault_path = Path(vault_path)
        self.inbox = self.vault_path / "Inbox"
        self.logs = self.vault_path / "Logs"
        self.callback = callback

    def on_created(self, event: FileCreatedEvent) -> None:
        if event.is_directory:
            return

        if not event.src_path.endswith('.md'):
            return

        if '.gitkeep' in event.src_path:
            return

        # Wait for file to be fully written
        time.sleep(0.5)

        file_path = Path(event.src_path)
        print(f"[FILE_WATCHER] New file detected: {file_path.name}")

        # Process the task automatically
        process_task(file_path, self.vault_path)

        if self.callback:
            self.callback(file_path)


class FileWatcher:
    """Watches the vault Inbox for new files."""

    def __init__(self, vault_path: str, callback: Optional[Callable] = None):
        self.vault_path = Path(vault_path)
        self.inbox_path = self.vault_path / "Inbox"
        self.callback = callback
        self.observer: Optional[Observer] = None

    def process_existing(self) -> None:
        """Process any existing files in Inbox on startup."""
        if not self.inbox_path.exists():
            self.inbox_path.mkdir(parents=True, exist_ok=True)
            return

        for file_path in self.inbox_path.glob("*.md"):
            if file_path.name == ".gitkeep":
                continue
            print(f"[FILE_WATCHER] Found existing file: {file_path.name}")
            process_task(file_path, self.vault_path)

    def start(self) -> Observer:
        """Start watching the Inbox folder."""
        # Process existing files first
        self.process_existing()

        handler = InboxHandler(str(self.vault_path), self.callback)
        self.observer = Observer()
        self.observer.schedule(handler, str(self.inbox_path), recursive=False)
        self.observer.start()
        print(f"[FILE_WATCHER] Monitoring: {self.inbox_path}")
        return self.observer

    def stop(self) -> None:
        """Stop watching."""
        if self.observer:
            self.observer.stop()
            self.observer.join()
            print("[FILE_WATCHER] Stopped")


def start_watcher(vault_path: str, callback: Optional[Callable] = None) -> Observer:
    """Start watching the Inbox folder."""
    watcher = FileWatcher(vault_path, callback)
    return watcher.start()


if __name__ == "__main__":
    import sys

    vault = sys.argv[1] if len(sys.argv) > 1 else "./vault"

    print(f"[FILE_WATCHER] Starting with vault: {vault}")

    observer = start_watcher(vault)

    try:
        print("[FILE_WATCHER] Press Ctrl+C to stop")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()

    observer.join()
