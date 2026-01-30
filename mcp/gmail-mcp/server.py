"""Gmail MCP Server for sending and managing emails."""

import os
import json
import base64
from pathlib import Path
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from mcp.server import Server
from mcp.types import Tool, TextContent

# Gmail API imports
try:
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    GMAIL_AVAILABLE = True
except ImportError:
    GMAIL_AVAILABLE = False

app = Server("gmail-mcp")

# Configuration
DRY_RUN = os.getenv("DRY_RUN", "true").lower() == "true"
CREDENTIALS_PATH = os.getenv("GMAIL_CREDENTIALS_PATH", "./credentials/client_secrets.json")
TOKEN_PATH = os.getenv("GMAIL_TOKEN_PATH", "./credentials/gmail_token.json")
SCOPES = [
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.compose',
    'https://www.googleapis.com/auth/gmail.readonly'
]

# Gmail service (initialized on first use)
_gmail_service = None


def get_gmail_service():
    """Get or create Gmail API service."""
    global _gmail_service

    if _gmail_service is not None:
        return _gmail_service

    if not GMAIL_AVAILABLE:
        raise RuntimeError("Gmail API libraries not installed")

    creds = None
    token_path = Path(TOKEN_PATH)
    credentials_path = Path(CREDENTIALS_PATH)

    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not credentials_path.exists():
                raise FileNotFoundError(f"Credentials not found: {credentials_path}")
            flow = InstalledAppFlow.from_client_secrets_file(str(credentials_path), SCOPES)
            creds = flow.run_local_server(port=0)

        token_path.parent.mkdir(parents=True, exist_ok=True)
        token_path.write_text(creds.to_json())

    _gmail_service = build('gmail', 'v1', credentials=creds)
    return _gmail_service


def log_action(action: str, details: dict) -> None:
    """Log an MCP action."""
    log_dir = Path(os.getenv("VAULT_PATH", "./vault")) / "Logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    log_file = log_dir / f"{datetime.now().strftime('%Y-%m-%d')}.json"

    entry = {
        "timestamp": datetime.now().isoformat(),
        "watcher": "GmailMCP",
        "event": action,
        **details
    }

    logs = []
    if log_file.exists():
        try:
            logs = json.loads(log_file.read_text())
        except json.JSONDecodeError:
            logs = []

    logs.append(entry)
    log_file.write_text(json.dumps(logs, indent=2))


@app.tool()
async def send_email(to: str, subject: str, body: str, cc: str = "", bcc: str = "") -> str:
    """Send an email via Gmail.

    Args:
        to: Recipient email address
        subject: Email subject line
        body: Email body (plain text)
        cc: CC recipients (comma-separated)
        bcc: BCC recipients (comma-separated)

    Returns:
        Result message
    """
    log_action("send_email_requested", {
        "to": to,
        "subject": subject,
        "dry_run": DRY_RUN
    })

    if DRY_RUN:
        return f"[DRY RUN] Would send email:\nTo: {to}\nSubject: {subject}\nBody: {body[:100]}..."

    try:
        service = get_gmail_service()

        # Create message
        message = MIMEMultipart()
        message['to'] = to
        message['subject'] = subject
        if cc:
            message['cc'] = cc
        if bcc:
            message['bcc'] = bcc

        message.attach(MIMEText(body, 'plain'))

        # Encode and send
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        result = service.users().messages().send(
            userId='me',
            body={'raw': raw}
        ).execute()

        log_action("email_sent", {
            "to": to,
            "subject": subject,
            "message_id": result.get('id')
        })

        return f"Email sent successfully to {to}. Message ID: {result.get('id')}"

    except Exception as e:
        log_action("email_send_failed", {
            "to": to,
            "error": str(e)
        })
        return f"Failed to send email: {str(e)}"


@app.tool()
async def draft_email(to: str, subject: str, body: str) -> str:
    """Create a draft email (doesn't send).

    Args:
        to: Recipient email address
        subject: Email subject line
        body: Email body

    Returns:
        Result message
    """
    log_action("draft_email_requested", {
        "to": to,
        "subject": subject,
        "dry_run": DRY_RUN
    })

    if DRY_RUN:
        return f"[DRY RUN] Would create draft:\nTo: {to}\nSubject: {subject}"

    try:
        service = get_gmail_service()

        # Create message
        message = MIMEText(body)
        message['to'] = to
        message['subject'] = subject

        # Encode
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()

        # Create draft
        draft = service.users().drafts().create(
            userId='me',
            body={'message': {'raw': raw}}
        ).execute()

        log_action("draft_created", {
            "to": to,
            "subject": subject,
            "draft_id": draft.get('id')
        })

        return f"Draft created for {to}. Draft ID: {draft.get('id')}"

    except Exception as e:
        log_action("draft_create_failed", {
            "to": to,
            "error": str(e)
        })
        return f"Failed to create draft: {str(e)}"


@app.tool()
async def search_emails(query: str, max_results: int = 10) -> str:
    """Search emails in Gmail.

    Args:
        query: Gmail search query (e.g., "from:user@example.com subject:hello")
        max_results: Maximum number of results to return

    Returns:
        Search results
    """
    if DRY_RUN:
        return f"[DRY RUN] Would search for: {query}"

    try:
        service = get_gmail_service()

        results = service.users().messages().list(
            userId='me',
            q=query,
            maxResults=max_results
        ).execute()

        messages = results.get('messages', [])

        if not messages:
            return "No emails found matching the query."

        # Get details for each message
        email_summaries = []
        for msg in messages[:max_results]:
            full_msg = service.users().messages().get(
                userId='me',
                id=msg['id'],
                format='metadata',
                metadataHeaders=['From', 'Subject', 'Date']
            ).execute()

            headers = {h['name']: h['value'] for h in full_msg['payload']['headers']}
            email_summaries.append(
                f"- From: {headers.get('From', 'Unknown')}\n"
                f"  Subject: {headers.get('Subject', 'No Subject')}\n"
                f"  Date: {headers.get('Date', 'Unknown')}"
            )

        return f"Found {len(messages)} emails:\n\n" + "\n\n".join(email_summaries)

    except Exception as e:
        return f"Search failed: {str(e)}"


if __name__ == "__main__":
    app.run()
