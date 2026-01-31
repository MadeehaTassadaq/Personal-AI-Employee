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


async def _send_email(to: str, subject: str, body: str, cc: str = "", bcc: str = "") -> str:
    """Send an email via Gmail."""
    log_action("send_email_requested", {
        "to": to,
        "subject": subject,
        "dry_run": DRY_RUN
    })

    if DRY_RUN:
        return f"[DRY RUN] Would send email:\nTo: {to}\nSubject: {subject}\nBody: {body[:100]}..."

    try:
        service = get_gmail_service()

        message = MIMEMultipart()
        message['to'] = to
        message['subject'] = subject
        if cc:
            message['cc'] = cc
        if bcc:
            message['bcc'] = bcc

        message.attach(MIMEText(body, 'plain'))

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


async def _draft_email(to: str, subject: str, body: str) -> str:
    """Create a draft email (doesn't send)."""
    log_action("draft_email_requested", {
        "to": to,
        "subject": subject,
        "dry_run": DRY_RUN
    })

    if DRY_RUN:
        return f"[DRY RUN] Would create draft:\nTo: {to}\nSubject: {subject}"

    try:
        service = get_gmail_service()

        message = MIMEText(body)
        message['to'] = to
        message['subject'] = subject

        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()

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


async def _search_emails(query: str, max_results: int = 10) -> str:
    """Search emails in Gmail."""
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


@app.list_tools()
async def handle_list_tools():
    """List available Gmail tools."""
    return [
        Tool(
            name="send_email",
            description="Send an email via Gmail",
            inputSchema={
                "type": "object",
                "properties": {
                    "to": {"type": "string", "description": "Recipient email address"},
                    "subject": {"type": "string", "description": "Email subject line"},
                    "body": {"type": "string", "description": "Email body (plain text)"},
                    "cc": {"type": "string", "description": "CC recipients (comma-separated)", "default": ""},
                    "bcc": {"type": "string", "description": "BCC recipients (comma-separated)", "default": ""}
                },
                "required": ["to", "subject", "body"]
            }
        ),
        Tool(
            name="draft_email",
            description="Create a draft email (doesn't send)",
            inputSchema={
                "type": "object",
                "properties": {
                    "to": {"type": "string", "description": "Recipient email address"},
                    "subject": {"type": "string", "description": "Email subject line"},
                    "body": {"type": "string", "description": "Email body"}
                },
                "required": ["to", "subject", "body"]
            }
        ),
        Tool(
            name="search_emails",
            description="Search emails in Gmail",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Gmail search query (e.g., 'from:user@example.com subject:hello')"},
                    "max_results": {"type": "integer", "description": "Maximum number of results", "default": 10}
                },
                "required": ["query"]
            }
        )
    ]


@app.call_tool()
async def handle_call_tool(name: str, arguments: dict):
    """Handle tool calls."""
    if name == "send_email":
        result = await _send_email(
            to=arguments["to"],
            subject=arguments["subject"],
            body=arguments["body"],
            cc=arguments.get("cc", ""),
            bcc=arguments.get("bcc", "")
        )
    elif name == "draft_email":
        result = await _draft_email(
            to=arguments["to"],
            subject=arguments["subject"],
            body=arguments["body"]
        )
    elif name == "search_emails":
        result = await _search_emails(
            query=arguments["query"],
            max_results=arguments.get("max_results", 10)
        )
    else:
        result = f"Unknown tool: {name}"

    return [TextContent(type="text", text=result)]


async def main():
    from mcp.server.stdio import stdio_server
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
