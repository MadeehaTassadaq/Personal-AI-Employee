"""Filesystem watcher for Inbox folder."""

import json
from pathlib import Path
from datetime import datetime
from typing import Callable, Optional

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent


class InboxHandler(FileSystemEventHandler):
    """Handler for filesystem events in the Inbox folder."""

    def __init__(self, vault_path: str, callback: Optional[Callable] = None):
        """Initialize the handler.

        Args:
            vault_path: Path to the Obsidian vault
            callback: Optional callback function when new file detected
        """
        self.vault_path = Path(vault_path)
        self.inbox = self.vault_path / "Inbox"
        self.logs = self.vault_path / "Logs"
        self.callback = callback

    def on_created(self, event: FileCreatedEvent) -> None:
        """Handle file creation events.

        Args:
            event: The file creation event
        """
        if event.is_directory:
            return

        if not event.src_path.endswith('.md'):
            return

        if '.gitkeep' in event.src_path:
            return

        file_path = Path(event.src_path)
        self.log_event("file_created", file_path)
        print(f"[FILE_WATCHER] New file detected: {file_path.name}")

        if self.callback:
            self.callback(file_path)

    def log_event(self, event_type: str, file_path: Path) -> None:
        """Log an event to the daily log file.

        Args:
            event_type: Type of event
            file_path: Path to the file involved
        """
        log_file = self.logs / f"{datetime.now().strftime('%Y-%m-%d')}.json"
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "watcher": "FileWatcher",
            "event": event_type,
            "file": str(file_path.name),
            "path": str(file_path)
        }

        logs = []
        if log_file.exists():
            try:
                logs = json.loads(log_file.read_text())
            except json.JSONDecodeError:
                logs = []

        logs.append(log_entry)
        log_file.write_text(json.dumps(logs, indent=2))


class FileWatcher:
    """Watches the vault Inbox for new files."""

    def __init__(self, vault_path: str, callback: Optional[Callable] = None):
        """Initialize the file watcher.

        Args:
            vault_path: Path to the Obsidian vault
            callback: Optional callback when new file detected
        """
        self.vault_path = Path(vault_path)
        self.inbox_path = self.vault_path / "Inbox"
        self.callback = callback
        self.observer: Optional[Observer] = None

    def start(self) -> Observer:
        """Start watching the Inbox folder.

        Returns:
            The Observer instance
        """
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
    """Start watching the Inbox folder.

    Args:
        vault_path: Path to the Obsidian vault
        callback: Optional callback when new file detected

    Returns:
        The Observer instance
    """
    watcher = FileWatcher(vault_path, callback)
    return watcher.start()


if __name__ == "__main__":
    import sys

    vault = sys.argv[1] if len(sys.argv) > 1 else "./vault"

    def on_new_file(path: Path):
        print(f"[CALLBACK] Processing: {path}")

    observer = start_watcher(vault, on_new_file)

    try:
        print("[FILE_WATCHER] Press Ctrl+C to stop")
        while True:
            pass
    except KeyboardInterrupt:
        observer.stop()

    observer.join()
