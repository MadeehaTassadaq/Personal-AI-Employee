"""WhatsApp MCP Server for sending messages via WhatsApp Web."""

import os
import json
from pathlib import Path
from datetime import datetime
from typing import Optional

from mcp.server import Server
from mcp.types import Tool, TextContent

# Playwright imports
try:
    from playwright.sync_api import sync_playwright, Browser, Page
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

app = Server("whatsapp-mcp")

# Configuration
DRY_RUN = os.getenv("DRY_RUN", "true").lower() == "true"
SESSION_PATH = os.getenv("WHATSAPP_SESSION_PATH", "./credentials/whatsapp_session")
HEADLESS = os.getenv("WHATSAPP_HEADLESS", "true").lower() == "true"

# Browser instance (initialized on first use)
_browser: Optional[Browser] = None
_page: Optional[Page] = None


def get_whatsapp_page():
    """Get or create WhatsApp Web page."""
    global _browser, _page

    if _page is not None:
        return _page

    if not PLAYWRIGHT_AVAILABLE:
        raise RuntimeError("Playwright not installed. Run: pip install playwright && playwright install chromium")

    session_path = Path(SESSION_PATH)
    session_path.mkdir(parents=True, exist_ok=True)

    playwright = sync_playwright().start()
    _browser = playwright.chromium.launch_persistent_context(
        str(session_path),
        headless=HEADLESS
    )
    _page = _browser.new_page()
    _page.goto("https://web.whatsapp.com")

    # Wait for WhatsApp to load
    try:
        _page.wait_for_selector('[data-testid="chat-list"]', timeout=60000)
    except Exception:
        print("WhatsApp Web may require QR code scan")

    return _page


def log_action(action: str, details: dict) -> None:
    """Log an MCP action."""
    log_dir = Path(os.getenv("VAULT_PATH", "./vault")) / "Logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    log_file = log_dir / f"{datetime.now().strftime('%Y-%m-%d')}.json"

    entry = {
        "timestamp": datetime.now().isoformat(),
        "watcher": "WhatsAppMCP",
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
async def send_message(phone: str, message: str) -> str:
    """Send a WhatsApp message.

    Args:
        phone: Phone number with country code (e.g., +1234567890)
        message: Message content to send

    Returns:
        Result message
    """
    # Clean phone number
    phone_clean = phone.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
    if not phone_clean.startswith("+"):
        phone_clean = "+" + phone_clean

    log_action("whatsapp_send_requested", {
        "phone": phone_clean,
        "message_length": len(message),
        "dry_run": DRY_RUN
    })

    if DRY_RUN:
        return f"[DRY RUN] Would send WhatsApp message:\nTo: {phone_clean}\nMessage: {message[:100]}..."

    try:
        page = get_whatsapp_page()

        # Navigate to chat via direct URL
        url = f"https://web.whatsapp.com/send?phone={phone_clean.replace('+', '')}"
        page.goto(url)

        # Wait for message input
        page.wait_for_selector('[data-testid="conversation-compose-box-input"]', timeout=30000)

        # Type message
        input_box = page.query_selector('[data-testid="conversation-compose-box-input"]')
        input_box.fill(message)

        # Send
        page.keyboard.press("Enter")

        # Wait for send confirmation
        page.wait_for_timeout(2000)

        log_action("whatsapp_sent", {
            "phone": phone_clean,
            "message_length": len(message)
        })

        return f"Message sent to {phone_clean}"

    except Exception as e:
        log_action("whatsapp_send_failed", {
            "phone": phone_clean,
            "error": str(e)
        })
        return f"Failed to send message: {str(e)}"


@app.tool()
async def check_session() -> str:
    """Check if WhatsApp Web session is active.

    Returns:
        Session status
    """
    if DRY_RUN:
        return "[DRY RUN] Would check WhatsApp session status"

    try:
        page = get_whatsapp_page()

        # Check for chat list (indicates logged in)
        chat_list = page.query_selector('[data-testid="chat-list"]')
        if chat_list:
            return "WhatsApp Web session is active"
        else:
            return "WhatsApp Web session not active - may need QR code scan"

    except Exception as e:
        return f"Session check failed: {str(e)}"


@app.tool()
async def get_unread_count() -> str:
    """Get count of unread WhatsApp chats.

    Returns:
        Unread count information
    """
    if DRY_RUN:
        return "[DRY RUN] Would check unread message count"

    try:
        page = get_whatsapp_page()

        # Find unread badges
        unread_badges = page.query_selector_all('[data-testid="icon-unread-count"]')
        count = len(unread_badges)

        return f"Found {count} chats with unread messages"

    except Exception as e:
        return f"Failed to get unread count: {str(e)}"


if __name__ == "__main__":
    app.run()
