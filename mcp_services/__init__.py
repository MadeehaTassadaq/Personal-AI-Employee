"""MCP servers package for Digital FTE.

This package provides access to all MCP server tools.
"""

# Import all MCP modules to make them available via importlib
import importlib
import importlib.util
from pathlib import Path

# Get all MCP server directories
mcp_dir = Path(__file__).parent
mcp_servers = [
    "browser_mcp",
    "calendar_mcp",
    "facebook_mcp",
    "gmail_mcp",
    "instagram_mcp",
    "linkedin_mcp",
    "odoo_mcp",
    "twitter_mcp",
    "whatsapp_mcp",
]

# Import each MCP server's tools
for server in mcp_servers:
    server_path = mcp_dir / server
    if server_path.exists() and (server_path / "__init__.py").exists():
        try:
            importlib.import_module(f"mcp_services.{server}")
        except ImportError as e:
            pass  # Skip if dependencies not installed

# Export commonly used items
__all__ = ["mcp__" + name for name in mcp_servers]
