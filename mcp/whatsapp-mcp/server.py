"""WhatsApp MCP Server for sending messages via WhatsApp Web.

Session is persisted in WHATSAPP_SESSION_PATH - QR code only needed once.
"""

import os
import json
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Optional

from mcp.server import Server
from mcp.types import Tool, TextContent

# Playwright imports
try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

app = Server("whatsapp-mcp")

# Configuration
DRY_RUN = os.getenv("DRY_RUN", "true").lower() == "true"
SESSION_PATH = Path(os.getenv("WHATSAPP_SESSION_PATH", "./credentials/whatsapp_session")).resolve()
HEADLESS = os.getenv("WHATSAPP_HEADLESS", "true").lower() == "true"

# Single persistent browser instance
_playwright = None
_browser = None
_page = None


async def get_whatsapp_page():
    """Get or create WhatsApp Web page with PERSISTENT session."""
    global _playwright, _browser, _page

    # Reuse existing page if valid
    if _page is not None:
        try:
            await _page.title()
            return _page
        except:
            _page = None

    # Reuse existing browser if valid
    if _browser is not None:
        try:
            _page = _browser.pages[0] if _browser.pages else await _browser.new_page()
            await _page.title()
            return _page
        except:
            _browser = None
            _page = None

    if not PLAYWRIGHT_AVAILABLE:
        raise RuntimeError("Playwright not installed. Run: uv add playwright && uv run playwright install chromium")

    # Ensure session directory exists
    SESSION_PATH.mkdir(parents=True, exist_ok=True)

    # Clean lock files that prevent reusing session
    for lock_pattern in ['*lock*', 'SingletonLock', 'SingletonCookie', 'SingletonSocket']:
        for lock_file in SESSION_PATH.glob(lock_pattern):
            try:
                lock_file.unlink()
            except:
                pass

    # Start Playwright
    _playwright = await async_playwright().start()

    # Launch persistent context - THIS SAVES THE SESSION
    _browser = await _playwright.chromium.launch_persistent_context(
        str(SESSION_PATH),
        headless=HEADLESS,
        args=[
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-dev-shm-usage",
            "--disable-blink-features=AutomationControlled",
        ],
        user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    # Get or create page
    _page = _browser.pages[0] if _browser.pages else await _browser.new_page()

    # Navigate to WhatsApp Web
    await _page.goto("https://web.whatsapp.com", wait_until="domcontentloaded", timeout=60000)

    # Wait for WhatsApp to load (either logged in or QR code)
    try:
        await _page.wait_for_selector(
            '[data-testid="chat-list"], canvas[aria-label="Scan this QR code to link a device!"]',
            timeout=30000
        )
    except:
        # Wait a bit more for slow connections
        await _page.wait_for_timeout(5000)

    return _page


async def is_logged_in(page) -> bool:
    """Check if WhatsApp Web is logged in."""
    try:
        # Try multiple selectors - WhatsApp Web changes frequently
        selectors = [
            '[data-testid="chat-list"]',
            'div#pane-side',
            '[data-testid="default-user"]',
            '[data-testid="menu-bar-menu"]',
            'div[aria-label="Chat list"]',
            'div[data-tab="3"]',
        ]
        for selector in selectors:
            element = await page.query_selector(selector)
            if element:
                return True
        return False
    except:
        return False


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
        except:
            logs = []

    logs.append(entry)
    log_file.write_text(json.dumps(logs, indent=2))


async def _send_message(phone: str, message: str) -> str:
    """Send a WhatsApp message."""
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
        page = await get_whatsapp_page()

        # Check if logged in
        if not await is_logged_in(page):
            return "WhatsApp Web not logged in. Please scan QR code in the browser window. Session will be saved for future use."

        # Navigate to chat
        url = f"https://web.whatsapp.com/send?phone={phone_clean.replace('+', '')}"
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)

        # Wait for chat to load - try multiple selectors
        chat_loaded = False
        try:
            await page.wait_for_selector(
                '[data-testid="conversation-compose-box-input"], div[contenteditable="true"][data-tab="10"]',
                timeout=25000
            )
            chat_loaded = True
        except:
            pass

        if not chat_loaded:
            # Check for specific error conditions
            try:
                # Check for "Phone number shared via url is invalid" popup
                invalid_popup = await page.query_selector('div[data-animate-modal-popup="true"]')
                if invalid_popup:
                    popup_text = await invalid_popup.inner_text()
                    if "invalid" in popup_text.lower():
                        return f"Invalid phone number: {phone_clean} - not registered on WhatsApp"

                # Check if we're still on the main page (number not found)
                current_url = page.url
                if "send?phone=" not in current_url:
                    return f"Could not navigate to chat for {phone_clean}"

                # Try clicking OK on any popup
                ok_button = await page.query_selector('div[role="button"]:has-text("OK")')
                if ok_button:
                    await ok_button.click()
                    await page.wait_for_timeout(1000)

            except Exception as e:
                pass

            return f"Could not load chat for {phone_clean} - please verify the number is on WhatsApp"

        # Type and send message - try multiple selectors
        input_selectors = [
            '[data-testid="conversation-compose-box-input"]',
            'div[contenteditable="true"][data-tab="10"]',
            'div[contenteditable="true"][title="Type a message"]',
            'footer div[contenteditable="true"]',
        ]

        input_box = None
        for selector in input_selectors:
            input_box = await page.query_selector(selector)
            if input_box:
                break

        if input_box:
            await input_box.click()
            await page.wait_for_timeout(500)
            await input_box.fill(message)
            await page.wait_for_timeout(500)

            # Try to find and click send button, or press Enter
            send_button = await page.query_selector('[data-testid="send"], button[aria-label="Send"]')
            if send_button:
                await send_button.click()
            else:
                await page.keyboard.press("Enter")

            await page.wait_for_timeout(2000)

            log_action("whatsapp_sent", {"phone": phone_clean, "message_length": len(message)})
            return f"Message sent to {phone_clean}"
        else:
            return "Could not find message input field - WhatsApp Web UI may have changed"

    except Exception as e:
        log_action("whatsapp_send_failed", {"phone": phone_clean, "error": str(e)})
        return f"Failed to send message: {str(e)}"


async def _check_session() -> str:
    """Check if WhatsApp Web session is active."""
    if DRY_RUN:
        return "[DRY RUN] Would check WhatsApp session status"

    try:
        page = await get_whatsapp_page()

        if await is_logged_in(page):
            return f"WhatsApp Web session is active. Session saved at: {SESSION_PATH}"
        else:
            return "WhatsApp Web needs QR code scan. Please scan in browser window - session will be saved."

    except Exception as e:
        return f"Session check failed: {str(e)}"


async def _get_unread_count() -> str:
    """Get count of unread WhatsApp chats."""
    if DRY_RUN:
        return "[DRY RUN] Would check unread message count"

    try:
        page = await get_whatsapp_page()

        if not await is_logged_in(page):
            return "Not logged in - please scan QR code first"

        unread_badges = await page.query_selector_all('[data-testid="icon-unread-count"]')
        return f"Found {len(unread_badges)} chats with unread messages"

    except Exception as e:
        return f"Failed to get unread count: {str(e)}"


@app.list_tools()
async def handle_list_tools():
    """List available WhatsApp tools."""
    return [
        Tool(
            name="send_message",
            description="Send a WhatsApp message",
            inputSchema={
                "type": "object",
                "properties": {
                    "phone": {"type": "string", "description": "Phone number with country code (e.g., +1234567890)"},
                    "message": {"type": "string", "description": "Message content to send"}
                },
                "required": ["phone", "message"]
            }
        ),
        Tool(
            name="check_session",
            description="Check if WhatsApp Web session is active",
            inputSchema={"type": "object", "properties": {}}
        ),
        Tool(
            name="get_unread_count",
            description="Get count of unread WhatsApp chats",
            inputSchema={"type": "object", "properties": {}}
        )
    ]


@app.call_tool()
async def handle_call_tool(name: str, arguments: dict):
    """Handle tool calls."""
    if name == "send_message":
        result = await _send_message(arguments["phone"], arguments["message"])
    elif name == "check_session":
        result = await _check_session()
    elif name == "get_unread_count":
        result = await _get_unread_count()
    else:
        result = f"Unknown tool: {name}"

    return [TextContent(type="text", text=result)]


async def main():
    from mcp.server.stdio import stdio_server

    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
