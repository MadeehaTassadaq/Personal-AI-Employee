"""LinkedIn MCP Server for posting and messaging."""

import os
import json
from pathlib import Path
from datetime import datetime

import httpx
from mcp.server import Server
from mcp.types import Tool, TextContent

app = Server("linkedin-mcp")

# Configuration
DRY_RUN = os.getenv("DRY_RUN", "true").lower() == "true"
ACCESS_TOKEN = os.getenv("LINKEDIN_ACCESS_TOKEN", "")
API_BASE = "https://api.linkedin.com/v2"


def get_headers():
    """Get LinkedIn API headers."""
    return {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json",
        "X-Restli-Protocol-Version": "2.0.0"
    }


def log_action(action: str, details: dict) -> None:
    """Log an MCP action."""
    log_dir = Path(os.getenv("VAULT_PATH", "./vault")) / "Logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    log_file = log_dir / f"{datetime.now().strftime('%Y-%m-%d')}.json"

    entry = {
        "timestamp": datetime.now().isoformat(),
        "watcher": "LinkedInMCP",
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


async def get_user_id() -> str:
    """Get the current user's LinkedIn ID."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{API_BASE}/userinfo",
            headers=get_headers()
        )
        if response.status_code == 200:
            return response.json().get("sub", "")
    return ""


@app.tool()
async def create_post(content: str, visibility: str = "PUBLIC") -> str:
    """Create a LinkedIn post.

    Args:
        content: Post content (text)
        visibility: Post visibility - "PUBLIC" or "CONNECTIONS"

    Returns:
        Result message
    """
    log_action("linkedin_post_requested", {
        "content_length": len(content),
        "visibility": visibility,
        "dry_run": DRY_RUN
    })

    if DRY_RUN:
        return f"[DRY RUN] Would create LinkedIn post:\nVisibility: {visibility}\nContent: {content[:100]}..."

    if not ACCESS_TOKEN:
        return "Error: LinkedIn access token not configured"

    try:
        user_id = await get_user_id()
        if not user_id:
            return "Error: Could not get LinkedIn user ID"

        post_data = {
            "author": f"urn:li:person:{user_id}",
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {
                        "text": content
                    },
                    "shareMediaCategory": "NONE"
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": visibility
            }
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{API_BASE}/ugcPosts",
                headers=get_headers(),
                json=post_data
            )

            if response.status_code in [200, 201]:
                post_id = response.headers.get("x-restli-id", "unknown")
                log_action("linkedin_posted", {
                    "post_id": post_id,
                    "content_length": len(content)
                })
                return f"Post created successfully. Post ID: {post_id}"
            else:
                log_action("linkedin_post_failed", {
                    "status": response.status_code,
                    "error": response.text
                })
                return f"Failed to create post: {response.status_code} - {response.text}"

    except Exception as e:
        log_action("linkedin_post_error", {"error": str(e)})
        return f"Error creating post: {str(e)}"


@app.tool()
async def get_profile() -> str:
    """Get the current user's LinkedIn profile info.

    Returns:
        Profile information
    """
    if DRY_RUN:
        return "[DRY RUN] Would fetch LinkedIn profile"

    if not ACCESS_TOKEN:
        return "Error: LinkedIn access token not configured"

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{API_BASE}/userinfo",
                headers=get_headers()
            )

            if response.status_code == 200:
                data = response.json()
                return (
                    f"LinkedIn Profile:\n"
                    f"- Name: {data.get('name', 'Unknown')}\n"
                    f"- Email: {data.get('email', 'Not available')}\n"
                    f"- ID: {data.get('sub', 'Unknown')}"
                )
            else:
                return f"Failed to get profile: {response.status_code}"

    except Exception as e:
        return f"Error getting profile: {str(e)}"


@app.tool()
async def check_connection() -> str:
    """Check if LinkedIn API connection is working.

    Returns:
        Connection status
    """
    if not ACCESS_TOKEN:
        return "Error: LinkedIn access token not configured"

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{API_BASE}/userinfo",
                headers=get_headers()
            )

            if response.status_code == 200:
                return "LinkedIn API connection is active"
            elif response.status_code == 401:
                return "LinkedIn token expired or invalid"
            else:
                return f"LinkedIn API returned status: {response.status_code}"

    except Exception as e:
        return f"Connection check failed: {str(e)}"


if __name__ == "__main__":
    app.run()
