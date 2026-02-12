"""Facebook MCP client wrapper.

This module exposes the MCP server functions as direct Python calls.
All MCP functions are prefixed with mcp__ for tool discovery.
"""

import sys
from pathlib import Path

# Import internal functions from server
from server import _post_to_page, _get_page_insights, _get_page_notifications, _get_page_info, _check_connection

# Expose functions with mcp__ prefix for tool discovery
async def mcp__facebook__post_to_page(content: str, link: str = None):
    """Create a post on Facebook Page."""
    result = await _post_to_page(content, link)
    if "successfully" in result or "Post ID" in result:
        return {"success": True, "id": result.split("Post ID: ")[-1].split(".")[0] if "Post ID:" in result else None}
    return {"success": False, "error": result}

async def mcp__facebook__get_page_insights(metric: str = "page_impressions", period: str = "day"):
    """Get Facebook Page insights."""
    result = await _get_page_insights(metric, period)
    return {"success": True, "data": result}

async def mcp__facebook__get_page_notifications():
    """Get Facebook Page notifications."""
    result = await _get_page_notifications()
    return {"success": True, "data": result}

async def mcp__facebook__get_page_info():
    """Get Facebook Page info."""
    result = await _get_page_info()
    return {"success": True, "data": result}

async def mcp__facebook__check_connection():
    """Check Facebook connection."""
    result = await _check_connection()
    return {"success": True, "data": result}

__all__ = [
    "mcp__facebook__post_to_page",
    "mcp__facebook__get_page_insights",
    "mcp__facebook__get_page_notifications",
    "mcp__facebook__get_page_info",
    "mcp__facebook__check_connection",
]
