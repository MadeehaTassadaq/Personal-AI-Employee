"""Browser MCP Server for web automation tasks."""

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

app = Server("browser-mcp")

# Configuration
DRY_RUN = os.getenv("DRY_RUN", "true").lower() == "true"
HEADLESS = os.getenv("BROWSER_HEADLESS", "true").lower() == "true"

# Browser instance
_browser: Optional[Browser] = None
_page: Optional[Page] = None


def get_browser_page():
    """Get or create browser page."""
    global _browser, _page

    if _page is not None:
        return _page

    if not PLAYWRIGHT_AVAILABLE:
        raise RuntimeError("Playwright not installed")

    playwright = sync_playwright().start()
    _browser = playwright.chromium.launch(headless=HEADLESS)
    _page = _browser.new_page()

    return _page


def log_action(action: str, details: dict) -> None:
    """Log an MCP action."""
    log_dir = Path(os.getenv("VAULT_PATH", "./vault")) / "Logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    log_file = log_dir / f"{datetime.now().strftime('%Y-%m-%d')}.json"

    entry = {
        "timestamp": datetime.now().isoformat(),
        "watcher": "BrowserMCP",
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
async def navigate(url: str) -> str:
    """Navigate to a URL.

    Args:
        url: URL to navigate to

    Returns:
        Page title and URL
    """
    log_action("browser_navigate", {"url": url, "dry_run": DRY_RUN})

    if DRY_RUN:
        return f"[DRY RUN] Would navigate to: {url}"

    try:
        page = get_browser_page()
        page.goto(url, wait_until="domcontentloaded")

        return f"Navigated to: {page.title()}\nURL: {page.url}"

    except Exception as e:
        return f"Navigation failed: {str(e)}"


@app.tool()
async def get_page_content() -> str:
    """Get the current page's text content.

    Returns:
        Page text content
    """
    if DRY_RUN:
        return "[DRY RUN] Would get page content"

    try:
        page = get_browser_page()
        content = page.inner_text("body")
        # Limit content length
        return content[:5000] + ("..." if len(content) > 5000 else "")

    except Exception as e:
        return f"Failed to get content: {str(e)}"


@app.tool()
async def screenshot(filename: str = "screenshot.png") -> str:
    """Take a screenshot of the current page.

    Args:
        filename: Name for the screenshot file

    Returns:
        Path to saved screenshot
    """
    log_action("browser_screenshot", {"filename": filename, "dry_run": DRY_RUN})

    if DRY_RUN:
        return f"[DRY RUN] Would take screenshot: {filename}"

    try:
        page = get_browser_page()

        # Save to vault
        vault_path = Path(os.getenv("VAULT_PATH", "./vault"))
        screenshot_path = vault_path / "Logs" / filename

        page.screenshot(path=str(screenshot_path))

        return f"Screenshot saved: {screenshot_path}"

    except Exception as e:
        return f"Screenshot failed: {str(e)}"


@app.tool()
async def click(selector: str) -> str:
    """Click an element on the page.

    Args:
        selector: CSS selector for the element

    Returns:
        Result message
    """
    log_action("browser_click", {"selector": selector, "dry_run": DRY_RUN})

    if DRY_RUN:
        return f"[DRY RUN] Would click: {selector}"

    try:
        page = get_browser_page()
        page.click(selector)
        return f"Clicked: {selector}"

    except Exception as e:
        return f"Click failed: {str(e)}"


@app.tool()
async def fill_input(selector: str, text: str) -> str:
    """Fill an input field.

    Args:
        selector: CSS selector for the input
        text: Text to fill

    Returns:
        Result message
    """
    log_action("browser_fill", {"selector": selector, "dry_run": DRY_RUN})

    if DRY_RUN:
        return f"[DRY RUN] Would fill {selector} with: {text[:50]}..."

    try:
        page = get_browser_page()
        page.fill(selector, text)
        return f"Filled {selector}"

    except Exception as e:
        return f"Fill failed: {str(e)}"


@app.tool()
async def close_browser() -> str:
    """Close the browser.

    Returns:
        Result message
    """
    global _browser, _page

    if DRY_RUN:
        return "[DRY RUN] Would close browser"

    try:
        if _browser:
            _browser.close()
            _browser = None
            _page = None
        return "Browser closed"

    except Exception as e:
        return f"Close failed: {str(e)}"


if __name__ == "__main__":
    app.run()
