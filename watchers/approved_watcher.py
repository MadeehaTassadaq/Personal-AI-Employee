"""Watcher for monitoring and processing approved actions.

This watcher monitors the Approved/ folder and automatically processes
files that have been approved for execution (social posts, WhatsApp messages, emails).
"""

import asyncio
import logging
import os
import time
from datetime import datetime
from pathlib import Path

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from backend.services.publisher import get_publisher


VAULT_PATH = Path(os.getenv("VAULT_PATH", "./AI_Employee_Vault"))
APPROVED_FOLDER = VAULT_PATH / "Approved"
DONE_FOLDER = VAULT_PATH / "Done"

# Ensure folders exist
APPROVED_FOLDER.mkdir(parents=True, exist_ok=True)
DONE_FOLDER.mkdir(parents=True, exist_ok=True)

# Track processed files to avoid duplicates
_processed_files = set()


class ApprovedFileHandler(FileSystemEventHandler):
    """Handler for file system events in Approved folder."""

    def __init__(self):
        super().__init__()
        self.publisher = get_publisher()
        self.logger = logging.getLogger(self.__class__.__name__)

    def on_created(self, event):
        """Handle new file created in Approved folder."""
        if event.is_directory:
            return

        file_path = Path(event.src_path)
        if file_path.suffix != ".md":
            return

        # Skip .gitkeep
        if file_path.name == ".gitkeep":
            return

        self.logger.info(f"New approved file detected: {file_path.name}")
        asyncio.create_task(self.process_approved_file(file_path))

    async def process_approved_file(self, file_path: Path):
        """Process an approved file by publishing its content."""
        global _processed_files

        # Skip if already processed
        file_key = str(file_path)
        if file_key in _processed_files:
            return

        _processed_files.add(file_key)

        # Wait a brief moment for file write to complete
        await asyncio.sleep(0.5)

        try:
            self.logger.info(f"Processing approved file: {file_path.name}")

            # Publish the content
            result = await self.publisher.publish(file_path)

            # Read current content
            content = file_path.read_text()
            import yaml
            frontmatter = {}
            body = content

            if content.startswith("---"):
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    try:
                        frontmatter = yaml.safe_load(parts[1]) or {}
                    except yaml.YAMLError:
                        frontmatter = {}
                    body = parts[2].strip()

            # Update frontmatter with results
            frontmatter["executed_at"] = datetime.now().isoformat()

            if result.get("success"):
                frontmatter["status"] = "completed"
                frontmatter["published"] = True
                if result.get("post_id"):
                    frontmatter["post_id"] = result.get("post_id")
                if result.get("tweet_id"):
                    frontmatter["tweet_id"] = result.get("tweet_id")
                if result.get("media_id"):
                    frontmatter["media_id"] = result.get("media_id")

                body += f"\n\n## Execution Result\nSuccessfully published to {result.get('platform', 'platform')} at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

                # Move to Done
                done_path = DONE_FOLDER / file_path.name
                done_path.write_text(f"---\n{yaml.dump(frontmatter, default_flow_style=False)}---\n\n{body}")
                file_path.unlink()

                self.logger.info(f"Successfully processed and moved to Done: {file_path.name}")
            else:
                frontmatter["status"] = "failed"
                frontmatter["error"] = result.get("error", "Unknown error")
                body += f"\n\n## Execution Failed\nError: {result.get('error', 'Unknown error')}\n\nWill retry on next check..."

                # Update file with error (keep in Approved for retry)
                file_path.write_text(f"---\n{yaml.dump(frontmatter, default_flow_style=False)}---\n\n{body}")

                self.logger.error(f"Failed to process {file_path.name}: {result.get('error')}")

            # Log the result
            self.publisher.log_publish_result(file_path.name, result)

        except Exception as e:
            self.logger.error(f"Error processing approved file {file_path.name}: {e}")
            import traceback
            traceback.print_exc()


class ApprovedWatcher:
    """Watcher for monitoring and processing approved actions."""

    def __init__(self, check_interval: int = 5):
        """Initialize the approved watcher.

        Args:
            check_interval: Seconds between checks (default: 5)
        """
        self.vault_path = VAULT_PATH
        self.approved_folder = APPROVED_FOLDER
        self.check_interval = check_interval
        self.running = False
        self.logger = logging.getLogger(self.__class__.__name__)
        self._setup_logging()
        self.publisher = get_publisher()

    def _setup_logging(self):
        """Configure logging for this watcher."""
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            f'[%(asctime)s] [ApprovedWatcher] %(levelname)s: %(message)s'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)

    async def process_existing_files(self):
        """Process any files that were already in Approved folder on startup."""
        for file_path in self.approved_folder.glob("*.md"):
            if file_path.name == ".gitkeep":
                continue

            # Read file content to check status
            content = file_path.read_text()

            # Skip files that have already failed multiple times (to avoid infinite retry)
            if content.count("## Execution Failed") >= 3:
                self.logger.warning(f"Skipping repeatedly failed file: {file_path.name}")
                continue

            # Check if file has error status (for retry)
            if "status: failed" in content or "error:" in content:
                self.logger.info(f"Retrying failed file: {file_path.name}")
                await self._process_file(file_path)
            elif "status: approved" in content:
                self.logger.info(f"Processing approved file: {file_path.name}")
                await self._process_file(file_path)

    async def _process_file(self, file_path: Path):
        """Process a single approved file."""
        try:
            self.logger.info(f"Processing: {file_path.name}")

            # Publish the content
            result = await self.publisher.publish(file_path)

            # Read and parse content
            content = file_path.read_text()
            import yaml
            frontmatter = {}
            body = content

            if content.startswith("---"):
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    try:
                        frontmatter = yaml.safe_load(parts[1]) or {}
                    except yaml.YAMLError:
                        frontmatter = {}
                    body = parts[2].strip()

            # Update frontmatter with results
            frontmatter["executed_at"] = datetime.now().isoformat()

            if result.get("success"):
                frontmatter["status"] = "completed"
                frontmatter["published"] = True
                if result.get("post_id"):
                    frontmatter["post_id"] = result.get("post_id")
                if result.get("tweet_id"):
                    frontmatter["tweet_id"] = result.get("tweet_id")
                if result.get("media_id"):
                    frontmatter["media_id"] = result.get("media_id")

                body += f"\n\n## Execution Result\nSuccessfully published to {result.get('platform', 'platform')} at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

                # Move to Done
                done_path = DONE_FOLDER / file_path.name
                done_path.write_text(f"---\n{yaml.dump(frontmatter, default_flow_style=False)}---\n\n{body}")
                file_path.unlink()

                self.logger.info(f"Successfully processed and moved to Done: {file_path.name}")
            else:
                frontmatter["status"] = "failed"
                frontmatter["error"] = result.get("error", "Unknown error")
                body += f"\n\n## Execution Failed\nError: {result.get('error', 'Unknown error')}"

                # Update file with error (keep in Approved for retry)
                file_path.write_text(f"---\n{yaml.dump(frontmatter, default_flow_style=False)}---\n\n{body}")

                self.logger.error(f"Failed to process {file_path.name}: {result.get('error')}")

            # Log the result
            self.publisher.log_publish_result(file_path.name, result)

        except Exception as e:
            self.logger.error(f"Error processing approved file {file_path.name}: {e}")
            import traceback
            traceback.print_exc()

    async def run_async(self):
        """Async run loop for processing approved files."""
        self.running = True
        self.logger.info("Starting Approved Watcher (async mode)")

        # Process existing files first
        await self.process_existing_files()

        while self.running:
            try:
                # Check for new files
                await self.process_existing_files()
            except Exception as e:
                self.logger.error(f"Error in check loop: {e}")

            await asyncio.sleep(self.check_interval)

    def run(self):
        """Run the watcher (blocking)."""
        self.logger.info("Starting Approved Watcher")
        asyncio.run(self.run_async())

    def stop(self):
        """Stop the watcher."""
        self.running = False
        self.logger.info("Stopping Approved Watcher")


# Global instance
_watcher_instance = None


def get_approved_watcher() -> ApprovedWatcher:
    """Get or create the global approved watcher instance."""
    global _watcher_instance
    if _watcher_instance is None:
        _watcher_instance = ApprovedWatcher()
    return _watcher_instance


if __name__ == "__main__":
    watcher = get_approved_watcher()
    try:
        watcher.run()
    except KeyboardInterrupt:
        watcher.stop()
