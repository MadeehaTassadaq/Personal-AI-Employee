"""Base class for all watchers."""

import time
import logging
from pathlib import Path
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any


class BaseWatcher(ABC):
    """Abstract base class for all watchers.

    Provides common functionality for monitoring external sources
    and creating tasks in the vault.
    """

    def __init__(self, vault_path: str, check_interval: int = 5):
        """Initialize the watcher.

        Args:
            vault_path: Path to the Obsidian vault
            check_interval: Seconds between checks (default: 5)
        """
        self.vault_path = Path(vault_path)
        self.check_interval = check_interval
        self.logger = logging.getLogger(self.__class__.__name__)
        self.running = False
        self._setup_logging()

    def _setup_logging(self):
        """Configure logging for this watcher."""
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            f'[%(asctime)s] [{self.__class__.__name__}] %(levelname)s: %(message)s'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)

    @abstractmethod
    def check_for_updates(self) -> list[Any]:
        """Check for new items to process.

        Returns:
            List of new items found
        """
        pass

    @abstractmethod
    def on_new_item(self, item: Any) -> None:
        """Handle a new item.

        Args:
            item: The item to process
        """
        pass

    def create_task_file(self, title: str, content: str, priority: str = "medium", folder: str = "Inbox") -> Path:
        """Create a task file in the specified folder.

        Args:
            title: Task title (will be slugified for filename)
            content: Task description and details
            priority: Task priority (high/medium/low)
            folder: Target folder (Inbox, Needs_Action, Done, etc.)

        Returns:
            Path to created file
        """
        # Create slug from title
        slug = title.lower().replace(" ", "-").replace("_", "-")
        slug = "".join(c for c in slug if c.isalnum() or c == "-")

        # Create filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        filename = f"{timestamp}-{slug}.md"

        # Build file content with frontmatter
        file_content = f"""---
created: {datetime.now().isoformat()}
priority: {priority}
status: new
source: {self.__class__.__name__}
---

# {title}

{content}

## Notes
<!-- AI processing notes go here -->
"""

        # Write to specified folder
        target_path = self.vault_path / folder / filename
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(file_content)

        self.logger.info(f"Created task in {folder}: {filename}")
        return target_path

    def log_event(self, event_type: str, details: dict) -> None:
        """Log an event to the vault logs.

        Args:
            event_type: Type of event (e.g., "task_created", "error")
            details: Event details
        """
        import json

        log_dir = self.vault_path / "Logs"
        log_file = log_dir / f"{datetime.now().strftime('%Y-%m-%d')}.json"

        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "watcher": self.__class__.__name__,
            "event": event_type,
            **details
        }

        # Load existing logs or create new list
        logs = []
        if log_file.exists():
            try:
                logs = json.loads(log_file.read_text())
            except json.JSONDecodeError:
                logs = []

        logs.append(log_entry)
        log_file.write_text(json.dumps(logs, indent=2))

    def run(self) -> None:
        """Start the watcher loop."""
        self.logger.info(f"Starting {self.__class__.__name__}")
        self.running = True

        while self.running:
            try:
                items = self.check_for_updates()
                for item in items:
                    try:
                        self.on_new_item(item)
                    except Exception as e:
                        self.logger.error(f"Error processing item: {e}")
                        self.log_event("error", {"error": str(e), "item": str(item)})
            except Exception as e:
                self.logger.error(f"Error in check loop: {e}")

            time.sleep(self.check_interval)

    def stop(self) -> None:
        """Stop the watcher loop."""
        self.running = False
        self.logger.info(f"Stopping {self.__class__.__name__}")
