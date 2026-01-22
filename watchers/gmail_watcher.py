"""Gmail inbox watcher using Google API."""

import os
import json
import base64
from pathlib import Path
from datetime import datetime
from typing import Any, Optional

from .base_watcher import BaseWatcher

# Gmail API imports (optional, fail gracefully)
try:
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    GMAIL_AVAILABLE = True
except ImportError:
    GMAIL_AVAILABLE = False


class GmailWatcher(BaseWatcher):
    """Watches Gmail inbox for new emails and creates vault tasks."""

    SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

    def __init__(
        self,
        vault_path: str,
        credentials_path: str,
        token_path: str,
        check_interval: int = 60,
        label: str = "INBOX"
    ):
        """Initialize Gmail watcher.

        Args:
            vault_path: Path to Obsidian vault
            credentials_path: Path to OAuth client credentials JSON
            token_path: Path to store/load OAuth token
            check_interval: Seconds between inbox checks
            label: Gmail label to watch (default: INBOX)
        """
        super().__init__(vault_path, check_interval)

        if not GMAIL_AVAILABLE:
            raise ImportError(
                "Gmail dependencies not installed. Run: "
                "pip install google-auth-oauthlib google-api-python-client"
            )

        self.credentials_path = Path(credentials_path)
        self.token_path = Path(token_path)
        self.label = label
        self.service = None
        self.seen_ids: set[str] = set()

        self._authenticate()
        self._load_seen_ids()

    def _authenticate(self) -> None:
        """Authenticate with Gmail API."""
        creds = None

        # Load existing token
        if self.token_path.exists():
            creds = Credentials.from_authorized_user_file(
                str(self.token_path), self.SCOPES
            )

        # Refresh or get new credentials
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(self.credentials_path), self.SCOPES
                )
                creds = flow.run_local_server(port=0)

            # Save credentials
            self.token_path.parent.mkdir(parents=True, exist_ok=True)
            self.token_path.write_text(creds.to_json())

        self.service = build('gmail', 'v1', credentials=creds)
        self.logger.info("Gmail authenticated successfully")

    def _load_seen_ids(self) -> None:
        """Load previously seen message IDs."""
        seen_file = self.vault_path / ".gmail_seen_ids.json"
        if seen_file.exists():
            try:
                self.seen_ids = set(json.loads(seen_file.read_text()))
            except json.JSONDecodeError:
                self.seen_ids = set()

    def _save_seen_ids(self) -> None:
        """Save seen message IDs."""
        seen_file = self.vault_path / ".gmail_seen_ids.json"
        seen_file.write_text(json.dumps(list(self.seen_ids)))

    def check_for_updates(self) -> list[dict]:
        """Check Gmail for new messages.

        Returns:
            List of new message data
        """
        if not self.service:
            return []

        try:
            # Get message list
            results = self.service.users().messages().list(
                userId='me',
                labelIds=[self.label],
                maxResults=10
            ).execute()

            messages = results.get('messages', [])
            new_messages = []

            for msg in messages:
                if msg['id'] not in self.seen_ids:
                    # Get full message
                    full_msg = self.service.users().messages().get(
                        userId='me',
                        id=msg['id'],
                        format='full'
                    ).execute()
                    new_messages.append(full_msg)
                    self.seen_ids.add(msg['id'])

            if new_messages:
                self._save_seen_ids()

            return new_messages

        except Exception as e:
            self.logger.error(f"Error checking Gmail: {e}")
            return []

    def on_new_item(self, item: dict) -> None:
        """Handle a new email.

        Args:
            item: Gmail message data
        """
        # Extract email details
        headers = {h['name']: h['value'] for h in item['payload']['headers']}

        sender = headers.get('From', 'Unknown')
        subject = headers.get('Subject', 'No Subject')
        date = headers.get('Date', '')

        # Get body preview
        snippet = item.get('snippet', '')[:500]

        # Determine priority based on keywords
        priority = "medium"
        urgent_keywords = ['urgent', 'asap', 'important', 'action required']
        if any(kw in subject.lower() or kw in snippet.lower() for kw in urgent_keywords):
            priority = "high"

        # Create task content
        content = f"""## Email Details
- **From:** {sender}
- **Subject:** {subject}
- **Date:** {date}
- **Gmail ID:** {item['id']}

## Preview
{snippet}

## Action Items
- [ ] Review email
- [ ] Determine response needed
- [ ] Draft response if required
"""

        # Create task in vault
        title = f"Email: {subject[:50]}"
        self.create_task_file(title, content, priority)

        self.log_event("email_received", {
            "gmail_id": item['id'],
            "from": sender,
            "subject": subject
        })


if __name__ == "__main__":
    import sys

    vault = sys.argv[1] if len(sys.argv) > 1 else "./vault"
    creds = os.getenv("GMAIL_CREDENTIALS_PATH", "./credentials/client_secrets.json")
    token = os.getenv("GMAIL_TOKEN_PATH", "./credentials/gmail_token.json")

    watcher = GmailWatcher(vault, creds, token)

    try:
        watcher.run()
    except KeyboardInterrupt:
        watcher.stop()
