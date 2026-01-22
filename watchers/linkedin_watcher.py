"""LinkedIn notifications watcher using API."""

import os
import json
from pathlib import Path
from datetime import datetime
from typing import Any, Optional

import httpx

from .base_watcher import BaseWatcher


class LinkedInWatcher(BaseWatcher):
    """Watches LinkedIn for notifications and creates vault tasks."""

    API_BASE = "https://api.linkedin.com/v2"

    def __init__(
        self,
        vault_path: str,
        access_token: str,
        check_interval: int = 300,  # 5 minutes default
    ):
        """Initialize LinkedIn watcher.

        Args:
            vault_path: Path to Obsidian vault
            access_token: LinkedIn API access token
            check_interval: Seconds between checks
        """
        super().__init__(vault_path, check_interval)

        self.access_token = access_token
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "X-Restli-Protocol-Version": "2.0.0"
        }
        self.seen_notifications: set[str] = set()
        self._load_seen_notifications()

    def _load_seen_notifications(self) -> None:
        """Load previously seen notification IDs."""
        seen_file = self.vault_path / ".linkedin_seen.json"
        if seen_file.exists():
            try:
                self.seen_notifications = set(json.loads(seen_file.read_text()))
            except json.JSONDecodeError:
                self.seen_notifications = set()

    def _save_seen_notifications(self) -> None:
        """Save seen notification IDs."""
        seen_file = self.vault_path / ".linkedin_seen.json"
        recent = list(self.seen_notifications)[-500:]
        seen_file.write_text(json.dumps(recent))

    def check_for_updates(self) -> list[dict]:
        """Check LinkedIn for new notifications.

        Note: LinkedIn API access is limited. This is a simplified
        implementation that would need proper OAuth setup.

        Returns:
            List of new notifications
        """
        new_items = []

        try:
            # Note: LinkedIn's notification API is restricted
            # This is a placeholder for when access is available

            # Check for new connection requests (simplified)
            with httpx.Client() as client:
                # Get invitations
                response = client.get(
                    f"{self.API_BASE}/invitations",
                    headers=self.headers,
                    params={"q": "received", "count": 10}
                )

                if response.status_code == 200:
                    data = response.json()
                    invitations = data.get("elements", [])

                    for inv in invitations:
                        inv_id = inv.get("id", "")
                        if inv_id and inv_id not in self.seen_notifications:
                            new_items.append({
                                "type": "connection_request",
                                "id": inv_id,
                                "data": inv
                            })
                            self.seen_notifications.add(inv_id)

                elif response.status_code == 401:
                    self.logger.warning("LinkedIn token expired or invalid")
                elif response.status_code == 403:
                    self.logger.debug("LinkedIn API access restricted")

        except httpx.RequestError as e:
            self.logger.error(f"LinkedIn API error: {e}")
        except Exception as e:
            self.logger.error(f"Error checking LinkedIn: {e}")

        if new_items:
            self._save_seen_notifications()

        return new_items

    def on_new_item(self, item: dict) -> None:
        """Handle a new LinkedIn notification.

        Args:
            item: Notification data
        """
        item_type = item.get("type", "unknown")
        item_id = item.get("id", "")
        data = item.get("data", {})

        if item_type == "connection_request":
            # Extract sender info if available
            sender = "Unknown User"
            if "fromMember" in data:
                sender = data["fromMember"].get("name", sender)

            content = f"""## LinkedIn Connection Request
- **From:** {sender}
- **Received:** {datetime.now().isoformat()}
- **Notification ID:** {item_id}

## Action Items
- [ ] Review profile
- [ ] Accept or decline connection
"""
            title = f"LinkedIn: Connection from {sender}"
            self.create_task_file(title, content, "medium")

        elif item_type == "message":
            sender = data.get("sender", "Unknown")
            preview = data.get("preview", "")

            content = f"""## LinkedIn Message
- **From:** {sender}
- **Received:** {datetime.now().isoformat()}

## Preview
{preview}

## Action Items
- [ ] Read full message
- [ ] Respond if needed
"""
            title = f"LinkedIn Message: {sender}"
            self.create_task_file(title, content, "medium")

        else:
            content = f"""## LinkedIn Notification
- **Type:** {item_type}
- **Received:** {datetime.now().isoformat()}

## Details
```json
{json.dumps(data, indent=2)[:500]}
```

## Action Items
- [ ] Review notification
"""
            title = f"LinkedIn: {item_type}"
            self.create_task_file(title, content, "low")

        self.log_event("linkedin_notification", {
            "type": item_type,
            "id": item_id
        })


if __name__ == "__main__":
    import sys

    vault = sys.argv[1] if len(sys.argv) > 1 else "./vault"
    token = os.getenv("LINKEDIN_ACCESS_TOKEN", "")

    if not token:
        print("Error: LINKEDIN_ACCESS_TOKEN not set")
        sys.exit(1)

    watcher = LinkedInWatcher(vault, token)

    try:
        watcher.run()
    except KeyboardInterrupt:
        watcher.stop()
