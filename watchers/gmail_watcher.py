"""Gmail inbox watcher using Google API with enhanced email analysis."""

import os
import json
import base64
import re
from pathlib import Path
from datetime import datetime, timedelta
from typing import Any, Optional
from email.utils import parsedate_to_datetime

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
        """Handle a new email with enhanced analysis.

        Args:
            item: Gmail message data
        """
        # Extract email details
        headers = {h['name']: h['value'] for h in item['payload'].get('headers', [])}

        sender = headers.get('From', 'Unknown')
        sender_email = self._extract_email(sender)
        subject = headers.get('Subject', 'No Subject')
        date = headers.get('Date', '')

        # Get full email body
        body = self._extract_body(item.get('payload', {}))
        snippet = item.get('snippet', '')[:500]

        # Analyze email using enhanced logic
        analysis = self._analyze_email(subject, body, sender, sender_email)

        # Get deadline if present
        deadline = self._extract_deadline(subject + ' ' + body)

        # Extract action items
        action_items = self._extract_action_items(subject, body)

        # Determine if response is needed
        response_needed = self._determine_response_needed(subject, body, sender_email)

        # Create enhanced task content
        content = self._create_analysis_task(
            item['id'], sender, sender_email, subject, date,
            analysis, body, action_items, deadline, response_needed
        )

        # Create task in appropriate folder
        # Newsletters go directly to Done/, others to Inbox/
        if analysis['category'] == 'newsletter':
            title = f"[Newsletter] {subject[:50]}"
            self.create_task_file(title, content, "low", folder="Done")
        else:
            title = f"Email: {subject[:50]}"
            self.create_task_file(title, content, analysis['priority'], folder="Inbox")

        self.log_event("email_received", {
            "gmail_id": item['id'],
            "from": sender,
            "sender_email": sender_email,
            "subject": subject,
            "category": analysis['category'],
            "priority": analysis['priority'],
            "response_needed": response_needed
        })

    def _extract_email(self, sender: str) -> str:
        """Extract email address from sender string."""
        email_match = re.search(r'[\w.+-]+@[\w-]+\.[\w.-]+', sender)
        return email_match.group() if email_match else sender

    def _extract_body(self, payload: dict) -> str:
        """Extract email body from payload."""
        body = ""

        # Try to get body from different parts
        if 'body' in payload and 'data' in payload['body']:
            body = base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8', errors='ignore')

        if not body and 'parts' in payload:
            for part in payload['parts']:
                if 'body' in part and 'data' in part['body']:
                    body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8', errors='ignore')
                    break

        return body[:2000] if body else ""

    def _analyze_email(self, subject: str, body: str, sender: str, sender_email: str) -> dict:
        """Analyze email to determine category and priority.

        Returns dict with category and priority.
        """
        subject_lower = subject.lower()
        body_lower = body.lower()
        combined = subject_lower + ' ' + body_lower

        # Define category patterns
        categories = {
            'urgent': {
                'keywords': ['urgent', 'asap', 'emergency', 'immediately', 'time-sensitive', 'critical', 'deadline today'],
                'priority': 'high'
            },
            'complaint': {
                'keywords': ['complaint', 'issue', 'problem', 'not working', 'broken', 'error', 'disappointed', 'unhappy', 'refund'],
                'priority': 'high'
            },
            'client_inquiry': {
                'keywords': ['question', 'inquiry', 'interested in', 'pricing', 'quote', 'proposal', 'can you', 'would you', 'wondering'],
                'priority': 'high'
            },
            'newsletter': {
                'keywords': ['unsubscribe', 'newsletter', 'digest', 'weekly update', 'monthly update', 'notification'],
                'priority': 'low'
            },
            'follow_up': {
                'keywords': ['follow up', 'follow-up', 'checking in', 'just checking', 'reminder'],
                'priority': 'medium'
            },
            'meeting': {
                'keywords': ['meeting', 'call', 'schedule', 'calendar invite', 'zoom', 'teams', 'google meet'],
                'priority': 'medium'
            }
        }

        # Check for VIP senders (clients, important contacts)
        vip_keywords = ['client', 'customer', 'prospect', 'lead']
        is_vip = any(kw in sender_email.lower() or kw in sender.lower() for kw in vip_keywords)

        # Determine category
        category = 'general'
        priority = 'medium'

        for cat_name, cat_info in categories.items():
            if any(kw in combined for kw in cat_info['keywords']):
                category = cat_name
                priority = cat_info['priority']
                break

        # Upgrade priority for VIP senders
        if is_vip and priority == 'low':
            priority = 'medium'
        elif is_vip and priority == 'medium':
            priority = 'high'

        return {
            'category': category,
            'priority': priority,
            'is_vip': is_vip
        }

    def _extract_deadline(self, text: str) -> Optional[str]:
        """Extract deadline from email text."""
        deadline_patterns = [
            r'by\s+(\w+\s+\d{1,2}(?:st|nd|rd|th)?)',
            r'before\s+(\w+\s+\d{1,2}(?:st|nd|rd|th)?)',
            r'due\s+(\w+\s+\d{1,2}(?:st|nd|rd|th)?)',
            r'deadline\s+(\w+\s+\d{1,2}(?:st|nd|rd|th)?)',
            r'(?:need|required)\s+by\s+(\w+\s+\d{1,2}(?:st|nd|rd|th)?)',
            r'end of day(?:\s+(\w+))?',
            r'eod(?:\s+(\w+))?',
            r'end of week(?:\s+(\w+))?',
            r'eow(?:\s+(\w+))?'
        ]

        for pattern in deadline_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(0)

        return None

    def _extract_action_items(self, subject: str, body: str) -> list[str]:
        """Extract action items from email."""
        action_items = []
        combined = subject + ' ' + body

        # Look for explicit action item indicators
        action_patterns = [
            r'please\s+(.+?)(?:\.|!|\n)',
            r'kindly\s+(.+?)(?:\.|!|\n)',
            r'action\s+(?:required|needed):\s*(.+?)(?:\.|!|\n)',
            r'next\s+steps?:\s*(.+?)(?:\.|\n)',
            r'to-do:\s*(.+?)(?:\.|\n)',
            r'(.+?)\s+is\s+(?:required|needed)',
        ]

        for pattern in action_patterns:
            matches = re.finditer(pattern, combined, re.IGNORECASE)
            for match in matches:
                action = match.group(1).strip()
                if len(action) > 10 and len(action) < 200:
                    action_items.append(action.capitalize())

        # Limit to top 5 action items
        return action_items[:5]

    def _determine_response_needed(self, subject: str, body: str, sender_email: str) -> bool:
        """Determine if a response is needed."""
        combined = (subject + ' ' + body).lower()

        # No response needed patterns
        no_response_patterns = [
            'no response needed',
            'do not reply',
            'for your information',
            'fyi only',
            'auto-generated',
            'notification',
            'receipt'
        ]

        if any(pattern in combined for pattern in no_response_patterns):
            return False

        # Question indicators
        question_indicators = ['?', 'please', 'can you', 'would you', 'help', 'advice']
        if any(indicator in combined for indicator in question_indicators):
            return True

        return False

    def _create_analysis_task(
        self,
        email_id: str,
        sender: str,
        sender_email: str,
        subject: str,
        date: str,
        analysis: dict,
        body: str,
        action_items: list[str],
        deadline: Optional[str],
        response_needed: bool
    ) -> str:
        """Create enhanced email analysis task content."""

        # Build summary
        summary = body[:500] + '...' if len(body) > 500 else body

        # Build action items section
        action_section = ""
        if action_items:
            action_section = "\n".join([f"- [ ] {item}" for item in action_items])
        else:
            action_section = "- [ ] Review email content"

        # Add default actions
        default_actions = [
            "- [ ] Review email content",
            "- [ ] Determine appropriate response" if response_needed else "- [ ] Acknowledge receipt (no action required)"
        ]

        # Build response strategy
        response_strategy = "No response required - FYI only"
        if response_needed:
            if analysis['category'] == 'client_inquiry':
                response_strategy = "Provide professional response addressing inquiry, offer call if needed"
            elif analysis['category'] == 'complaint':
                response_strategy = "Acknowledge issue, express concern, propose resolution timeline"
            elif analysis['category'] == 'urgent':
                response_strategy = "Immediate response required, prioritize above other tasks"
            elif analysis['category'] == 'follow_up':
                response_strategy = "Provide requested information or confirm action taken"
            else:
                response_strategy = "Provide appropriate professional response"

        return f"""---
type: email_analysis
email_id: {email_id}
category: {analysis['category']}
priority: {analysis['priority']}
status: inbox
response_needed: {str(response_needed).lower()}
created: {datetime.now().isoformat()}
deadline: {deadline or 'None'}
sender: {sender_email}
subject: {subject}
vip_sender: {str(analysis['is_vip']).lower()}
---

# Email Analysis: {subject[:60]}

## Email Details
- **From:** {sender}
- **Date:** {date}
- **Category:** {analysis['category'].replace('_', ' ').title()}
- **Priority:** {analysis['priority'].title()}
- **VIP Sender:** {'Yes' if analysis['is_vip'] else 'No'}

## Summary
{summary}

## Action Items
{action_section}

## Response Strategy
{response_strategy}

## Deadline
{deadline if deadline else 'No deadline specified'}

## Original Email
{body}
"""


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
