"""WhatsApp MCP Server for sending messages via WhatsApp Web."""

import os
import json
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Optional
import tempfile

from mcp.server import Server
from mcp.types import Tool, TextContent

# Playwright imports - use async API for MCP server
try:
    from playwright.async_api import async_playwright, BrowserContext, Page
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

app = Server("whatsapp-mcp")

# Configuration
DRY_RUN = os.getenv("DRY_RUN", "true").lower() == "true"
SESSION_PATH = os.getenv("WHATSAPP_SESSION_PATH", "./credentials/whatsapp_session")
HEADLESS = os.getenv("WHATSAPP_HEADLESS", "true").lower() == "true"

# Browser instance (initialized per session)
_browser_contexts = {}  # Store contexts by session ID to avoid conflicts
_last_access = {}  # Track when each context was last used


async def get_whatsapp_page():
    """Get or create WhatsApp Web page with proper session management."""
    import secrets
    session_id = os.getenv("USER", "default") + "_" + secrets.token_hex(4)

    # Clean up old contexts that haven't been used in 10 minutes
    current_time = datetime.now().timestamp()
    to_remove = []
    for sid, last_time in _last_access.items():
        if current_time - last_time > 600:  # 10 minutes
            to_remove.append(sid)

    for sid in to_remove:
        if sid in _browser_contexts:
            try:
                await _browser_contexts[sid]['context'].close()
            except:
                pass
            del _browser_contexts[sid]
        if sid in _last_access:
            del _last_access[sid]

    # Check if we have a valid context for this session
    if session_id in _browser_contexts:
        ctx_info = _browser_contexts[session_id]
        try:
            # Test if page is still accessible
            await ctx_info['page'].title()
            _last_access[session_id] = current_time
            return ctx_info['page']
        except Exception:
            # Page is closed, remove the context
            try:
                await ctx_info['context'].close()
            except:
                pass
            del _browser_contexts[session_id]
            del _last_access[session_id]

    if not PLAYWRIGHT_AVAILABLE:
        raise RuntimeError("Playwright not installed. Run: pip install playwright && playwright install chromium")

    session_path = Path(SESSION_PATH)
    session_path.mkdir(parents=True, exist_ok=True)

    # Create a unique session directory to avoid lock conflicts
    unique_session_path = session_path / session_id
    unique_session_path.mkdir(exist_ok=True)

    # Remove any existing lock files
    for lock_file in unique_session_path.glob('*lock*'):
        try:
            lock_file.unlink()
        except:
            pass

    try:
        _playwright = await async_playwright().start()
        _browser = await _playwright.chromium.launch_persistent_context(
            str(unique_session_path),
            headless=HEADLESS,
            args=[
                "--disable-web-security",
                "--disable-features=VizDisplayCompositor",
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
            ]
        )
        _page = await _browser.new_page()
        await _page.goto("https://web.whatsapp.com", wait_until="networkidle")

        # Wait for WhatsApp to load
        try:
            # Wait for either the chat list (logged in) or QR code (need to log in)
            await _page.wait_for_selector(
                '[data-testid="chat-list"], [data-testid="qr-code"]',
                timeout=60000
            )

            # Check if QR code is present (not logged in)
            qr_present = await _page.query_selector('[data-testid="qr-code"]')
            if qr_present:
                print("WhatsApp Web requires QR code scan for first-time setup")

        except Exception as e:
            print(f"Warning: Could not detect WhatsApp Web state: {e}")

        # Store the context info
        _browser_contexts[session_id] = {
            'playwright': _playwright,
            'context': _browser,
            'page': _page,
            'created_at': current_time
        }
        _last_access[session_id] = current_time

        return _page

    except Exception as e:
        print(f"Error initializing WhatsApp browser: {e}")
        # Clean up on error
        if 'unique_session_path' in locals():
            import shutil
            try:
                shutil.rmtree(unique_session_path, ignore_errors=True)
            except:
                pass
        raise


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

        # Check if WhatsApp is properly logged in
        logged_in = await page.query_selector('[data-testid="chat-list"]')
        if not logged_in:
            # Check if QR code is present (not logged in)
            qr_present = await page.query_selector('[data-testid="qr-code"]')
            if qr_present:
                return "WhatsApp Web not logged in - please scan QR code in a browser first."

        # Navigate to chat via direct URL
        url = f"https://web.whatsapp.com/send?phone={phone_clean.replace('+', '')}"
        await page.goto(url)

        # Wait for message input or check for errors
        try:
            # Wait for the chat to load
            await page.wait_for_selector('[data-testid="conversation-compose-box-input"], [data-testid="conversation-compose-box-send-button"]', timeout=15000)

            # Check if there's an error message
            error_element = await page.query_selector('text="Phone number shared via url is invalid"')
            if error_element:
                return f"Invalid phone number: {phone_clean}"

        except Exception:
            # If timeout occurs, check for error messages
            error_text = await page.text_content('body')
            if "invalid" in error_text.lower():
                return f"Invalid phone number or unable to reach user: {phone_clean}"
            raise

        # Type message
        input_box = await page.query_selector('[data-testid="conversation-compose-box-input"]')
        if input_box:
            await input_box.fill(message)
        else:
            # Alternative selector
            input_box = await page.query_selector('div[contenteditable="true"][tabindex="0"]')
            if input_box:
                await input_box.fill(message)
            else:
                return "Could not find message input field"

        # Send
        send_button = await page.query_selector('[data-testid="conversation-compose-box-send-button"]')
        if send_button:
            await send_button.click()
        else:
            # Alternative: press Enter
            await page.keyboard.press("Enter")

        # Wait for send confirmation
        await page.wait_for_timeout(2000)

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


async def _check_session() -> str:
    """Check if WhatsApp Web session is active."""
    if DRY_RUN:
        return "[DRY RUN] Would check WhatsApp session status"

    try:
        page = await get_whatsapp_page()

        # Check for chat list (indicates logged in)
        chat_list = await page.query_selector('[data-testid="chat-list"]')
        if chat_list:
            return "WhatsApp Web session is active"
        else:
            return "WhatsApp Web session not active - may need QR code scan"

    except Exception as e:
        return f"Session check failed: {str(e)}"


async def _get_unread_count() -> str:
    """Get count of unread WhatsApp chats."""
    if DRY_RUN:
        return "[DRY RUN] Would check unread message count"

    try:
        page = await get_whatsapp_page()

        # Find unread badges
        unread_badges = await page.query_selector_all('[data-testid="icon-unread-count"]')
        count = len(unread_badges)

        return f"Found {count} chats with unread messages"

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
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="get_unread_count",
            description="Get count of unread WhatsApp chats",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        )
    ]


@app.call_tool()
async def handle_call_tool(name: str, arguments: dict):
    """Handle tool calls."""
    if name == "send_message":
        result = await _send_message(
            phone=arguments["phone"],
            message=arguments["message"]
        )
    elif name == "check_session":
        result = await _check_session()
    elif name == "get_unread_count":
        result = await _get_unread_count()
    else:
        result = f"Unknown tool: {name}"

    return [TextContent(type="text", text=result)]


async def cleanup_old_contexts():
    """Periodically clean up old browser contexts."""
    global _last_access, _browser_contexts

    current_time = datetime.now().timestamp()
    to_remove = []

    for session_id, last_time in _last_access.items():
        if current_time - last_time > 600:  # 10 minutes
            to_remove.append(session_id)

    for session_id in to_remove:
        if session_id in _browser_contexts:
            try:
                await _browser_contexts[session_id]['context'].close()
            except:
                pass
            del _browser_contexts[session_id]
        if session_id in _last_access:
            del _last_access[session_id]


async def main():
    from mcp.server.stdio import stdio_server

    # Set up periodic cleanup
    async def periodic_cleanup():
        while True:
            try:
                await cleanup_old_contexts()
            except:
                pass
            await asyncio.sleep(30)  # Clean up every 30 seconds

    # Start cleanup task
    cleanup_task = asyncio.create_task(periodic_cleanup())

    try:
        async with stdio_server() as (read_stream, write_stream):
            await app.run(read_stream, write_stream, app.create_initialization_options())
    finally:
        # Cleanup on shutdown
        cleanup_task.cancel()
        try:
            await cleanup_task
        except asyncio.CancelledError:
            pass

        # Close all remaining contexts
        for ctx_info in _browser_contexts.values():
            try:
                await ctx_info['context'].close()
            except:
                pass


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
