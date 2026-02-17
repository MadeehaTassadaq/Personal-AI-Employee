"""WhatsApp message watcher using Playwright."""

import os
import json
from pathlib import Path
from datetime import datetime
from typing import Any, Optional

from .base_watcher import BaseWatcher

# Playwright imports (optional, fail gracefully)
try:
    from playwright.sync_api import sync_playwright, Browser, Page
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False


class WhatsAppWatcher(BaseWatcher):
    """Watches WhatsApp Web for new messages and creates vault tasks."""

    WHATSAPP_URL = "https://web.whatsapp.com"

    def __init__(
        self,
        vault_path: str,
        session_path: str,
        check_interval: int = 30,
        headless: bool = True
    ):
        """Initialize WhatsApp watcher.

        Args:
            vault_path: Path to Obsidian vault
            session_path: Path to store browser session data
            check_interval: Seconds between message checks
            headless: Run browser in headless mode
        """
        super().__init__(vault_path, check_interval)

        if not PLAYWRIGHT_AVAILABLE:
            raise ImportError(
                "Playwright not installed. Run: "
                "pip install playwright && playwright install chromium"
            )

        self.session_path = Path(session_path)
        self.headless = headless
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.seen_messages: set[str] = set()

        self._load_seen_messages()

    def _load_seen_messages(self) -> None:
        """Load previously seen message hashes."""
        seen_file = self.vault_path / ".whatsapp_seen.json"
        if seen_file.exists():
            try:
                self.seen_messages = set(json.loads(seen_file.read_text()))
            except json.JSONDecodeError:
                self.seen_messages = set()

    def _save_seen_messages(self) -> None:
        """Save seen message hashes."""
        seen_file = self.vault_path / ".whatsapp_seen.json"
        # Keep only last 1000 messages
        recent = list(self.seen_messages)[-1000:]
        seen_file.write_text(json.dumps(recent))

    def _get_queue_file(self) -> Path:
        """Get the path to the message queue file."""
        return self.vault_path / ".whatsapp_queue.json"

    def _process_message_queue(self) -> None:
        """Process outgoing messages from the shared queue file.

        This allows the publisher service to queue messages without
        launching a new browser instance (which would cause profile lock errors).
        """
        queue_file = self._get_queue_file()

        if not queue_file.exists():
            return

        try:
            queue_data = json.loads(queue_file.read_text())
            messages = queue_data.get("messages", [])

            if not messages:
                return

            self.logger.info(f"Processing {len(messages)} queued WhatsApp messages")

            # Process each message in the queue
            remaining_messages = []
            for msg in messages:
                msg_id = msg.get("id")
                phone = msg.get("phone")
                content = msg.get("content")

                if not phone or not content:
                    remaining_messages.append(msg)
                    continue

                # Attempt to send the message
                success = self._send_message(phone, content)

                if success:
                    self.logger.info(f"Sent queued message to {phone}")
                    self.log_event("whatsapp_sent_queued", {
                        "phone": phone,
                        "message_id": msg_id
                    })
                else:
                    # Keep message in queue if failed
                    remaining_messages.append(msg)

            # Update queue file with remaining messages
            if remaining_messages:
                queue_data["messages"] = remaining_messages
                queue_file.write_text(json.dumps(queue_data, indent=2))
            else:
                # Remove queue file if empty
                queue_file.unlink()

        except json.JSONDecodeError:
            self.logger.error("Invalid queue file format")
        except Exception as e:
            self.logger.error(f"Error processing message queue: {e}")

    def _send_message(self, phone: str, content: str) -> bool:
        """Send a WhatsApp message using the active browser session.

        Args:
            phone: Phone number with country code (e.g., +1234567890)
            content: Message content to send

        Returns:
            True if message was sent successfully
        """
        if not self.page:
            return False

        try:
            # Clean phone number
            phone_clean = phone.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
            if not phone_clean.startswith("+"):
                phone_clean = "+" + phone_clean

            # Use WhatsApp Web URL scheme to open chat
            whatsapp_url = f"https://web.whatsapp.com/send?phone={phone_clean.replace('+', '')}&text={content}"

            # Navigate to the chat
            self.page.goto(whatsapp_url, timeout=15000)

            # Wait for the chat to load and message input to appear
            try:
                # Wait for message input box
                self.page.wait_for_selector('[data-testid="conversation-panel-body"]', timeout=10000)

                # The message should be pre-filled in the input via URL
                # Look for send button and click it
                send_button = self.page.query_selector('[data-testid="send"]')
                if send_button:
                    send_button.click()
                    # Wait a moment for send to complete
                    import time
                    time.sleep(1)
                    return True
                else:
                    self.logger.warning("Could not find send button")
                    return False

            except Exception as e:
                self.logger.error(f"Error sending message: {e}")
                return False

        except Exception as e:
            self.logger.error(f"Error navigating to WhatsApp chat: {e}")
            return False

    def _init_browser(self) -> None:
        """Initialize Playwright browser with saved session."""
        self.session_path.mkdir(parents=True, exist_ok=True)

        playwright = sync_playwright().start()
        self.browser = playwright.chromium.launch_persistent_context(
            str(self.session_path),
            headless=self.headless
        )
        self.page = self.browser.new_page()
        self.page.goto(self.WHATSAPP_URL)

        # Wait for WhatsApp to load
        self.logger.info("Waiting for WhatsApp Web to load...")
        self.logger.info("If first run, scan QR code in browser")

        # Wait for chat list to appear (indicates logged in)
        try:
            self.page.wait_for_selector('[data-testid="chat-list"]', timeout=60000)
            self.logger.info("WhatsApp Web loaded successfully")
        except Exception:
            self.logger.warning("WhatsApp may require QR code scan")

    def check_for_updates(self) -> list[dict]:
        """Check WhatsApp for new unread messages.

        Returns:
            List of new message data
        """
        if not self.page:
            self._init_browser()

        if not self.page:
            return []

        # Check for outgoing message queue before checking for new messages
        self._process_message_queue()

        try:
            new_messages = []

            # Find chats with unread messages
            unread_chats = self.page.query_selector_all('[data-testid="cell-frame-container"]')

            for chat in unread_chats[:10]:  # Limit to 10 chats
                try:
                    # Check for unread indicator
                    unread_badge = chat.query_selector('[data-testid="icon-unread-count"]')
                    if not unread_badge:
                        continue

                    # Get chat name
                    name_el = chat.query_selector('[data-testid="cell-frame-title"]')
                    chat_name = name_el.inner_text() if name_el else "Unknown"

                    # Get last message preview
                    preview_el = chat.query_selector('[data-testid="last-msg-status"]')
                    preview = preview_el.inner_text() if preview_el else ""

                    # Create unique hash
                    msg_hash = f"{chat_name}:{preview}"[:100]

                    if msg_hash not in self.seen_messages:
                        new_messages.append({
                            "chat_name": chat_name,
                            "preview": preview,
                            "timestamp": datetime.now().isoformat()
                        })
                        self.seen_messages.add(msg_hash)

                except Exception as e:
                    self.logger.debug(f"Error processing chat: {e}")

            if new_messages:
                self._save_seen_messages()

            return new_messages

        except Exception as e:
            self.logger.error(f"Error checking WhatsApp: {e}")
            return []

    def on_new_item(self, item: dict) -> None:
        """Handle a new WhatsApp message.

        Args:
            item: Message data
        """
        chat_name = item.get('chat_name', 'Unknown')
        preview = item.get('preview', '')
        timestamp = item.get('timestamp', '')

        # Determine priority
        priority = "medium"
        urgent_keywords = ['urgent', 'asap', 'help', 'emergency']
        if any(kw in preview.lower() for kw in urgent_keywords):
            priority = "high"

        # Create task content
        content = f"""## WhatsApp Message
- **From:** {chat_name}
- **Received:** {timestamp}

## Message Preview
{preview}

## Action Items
- [ ] Review message
- [ ] Respond if needed
"""

        # Create task
        title = f"WhatsApp: {chat_name}"
        self.create_task_file(title, content, priority)

        self.log_event("whatsapp_received", {
            "from": chat_name,
            "preview": preview[:100]
        })

    def stop(self) -> None:
        """Stop watcher and close browser."""
        super().stop()
        if self.browser:
            self.browser.close()


if __name__ == "__main__":
    import sys

    vault = sys.argv[1] if len(sys.argv) > 1 else "./vault"
    session = os.getenv("WHATSAPP_SESSION_PATH", "./credentials/whatsapp_session")
    headless = os.getenv("WHATSAPP_HEADLESS", "false").lower() == "true"

    watcher = WhatsAppWatcher(vault, session, headless=headless)

    try:
        watcher.run()
    except KeyboardInterrupt:
        watcher.stop()
