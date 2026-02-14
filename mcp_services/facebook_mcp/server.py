"""Facebook MCP Server for page posting and insights."""

import os
import json
from pathlib import Path
from datetime import datetime
from typing import Optional

import httpx
from mcp.server import Server
from mcp.types import Tool, TextContent

app = Server("facebook-mcp")

# Configuration
DRY_RUN = False  # Set to False for live posting
PAGE_ACCESS_TOKEN = os.getenv("FACEBOOK_PAGE_ACCESS_TOKEN", "")
PAGE_ID = os.getenv("FACEBOOK_PAGE_ID", "")
API_VERSION = "v18.0"
API_BASE = f"https://graph.facebook.com/{API_VERSION}"


def log_action(action: str, details: dict) -> None:
    """Log an MCP action."""
    log_dir = Path(os.getenv("VAULT_PATH", "./vault")) / "Logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    log_file = log_dir / f"{datetime.now().strftime('%Y-%m-%d')}.json"

    entry = {
        "timestamp": datetime.now().isoformat(),
        "watcher": "FacebookMCP",
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


def get_headers():
    """Get Facebook API headers."""
    return {
        "Content-Type": "application/json"
    }


async def _post_to_page(content: str, link: Optional[str] = None) -> str:
    """Create a post on the Facebook Page."""
    log_action("facebook_post_requested", {
        "content_length": len(content),
        "has_link": link is not None,
        "dry_run": DRY_RUN
    })

    if DRY_RUN:
        link_info = f"\nLink: {link}" if link else ""
        return f"[DRY RUN] Would create Facebook Page post:\nContent: {content[:100]}...{link_info}"

    if not PAGE_ACCESS_TOKEN:
        return "Error: Facebook Page access token not configured"

    if not PAGE_ID:
        return "Error: Facebook Page ID not configured"

    try:
        post_data = {
            "message": content,
            "access_token": PAGE_ACCESS_TOKEN
        }

        if link:
            post_data["link"] = link

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{API_BASE}/{PAGE_ID}/feed",
                headers=get_headers(),
                json=post_data
            )

            if response.status_code in [200, 201]:
                data = response.json()
                post_id = data.get("id", "unknown")
                log_action("facebook_posted", {
                    "post_id": post_id,
                    "content_length": len(content)
                })
                return f"Post created successfully. Post ID: {post_id}"
            else:
                error_data = response.json()
                error_msg = error_data.get("error", {}).get("message", response.text)
                log_action("facebook_post_failed", {
                    "status": response.status_code,
                    "error": error_msg
                })
                return f"Failed to create post: {response.status_code} - {error_msg}"

    except Exception as e:
        log_action("facebook_post_error", {"error": str(e)})
        return f"Error creating post: {str(e)}"


async def _get_page_insights(metric: str = "page_impressions", period: str = "day") -> str:
    """Get Facebook Page insights and analytics."""
    log_action("facebook_insights_requested", {
        "metric": metric,
        "period": period,
        "dry_run": DRY_RUN
    })

    if DRY_RUN:
        return f"[DRY RUN] Would fetch Facebook insights:\nMetric: {metric}\nPeriod: {period}"

    if not PAGE_ACCESS_TOKEN:
        return "Error: Facebook Page access token not configured"

    if not PAGE_ID:
        return "Error: Facebook Page ID not configured"

    try:
        params = {
            "metric": metric,
            "period": period,
            "access_token": PAGE_ACCESS_TOKEN
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{API_BASE}/{PAGE_ID}/insights",
                params=params
            )

            if response.status_code == 200:
                data = response.json()
                insights = data.get("data", [])

                if not insights:
                    return f"No insights data available for {metric}"

                result = f"Facebook Page Insights - {metric} ({period}):\n"
                for insight in insights:
                    values = insight.get("values", [])
                    for v in values[-3:]:
                        result += f"- {v.get('end_time', 'N/A')}: {v.get('value', 0)}\n"

                return result
            else:
                error_data = response.json()
                error_msg = error_data.get("error", {}).get("message", response.text)
                return f"Failed to get insights: {response.status_code} - {error_msg}"

    except Exception as e:
        log_action("facebook_insights_error", {"error": str(e)})
        return f"Error getting insights: {str(e)}"


async def _get_page_notifications() -> str:
    """Get recent notifications for the Facebook Page."""
    log_action("facebook_notifications_requested", {"dry_run": DRY_RUN})

    if DRY_RUN:
        return "[DRY RUN] Would fetch Facebook Page notifications"

    if not PAGE_ACCESS_TOKEN:
        return "Error: Facebook Page access token not configured"

    if not PAGE_ID:
        return "Error: Facebook Page ID not configured"

    try:
        params = {
            "access_token": PAGE_ACCESS_TOKEN,
            "limit": 25
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{API_BASE}/{PAGE_ID}/feed",
                params={
                    **params,
                    "fields": "message,created_time,comments.limit(5),reactions.summary(true)"
                }
            )

            if response.status_code == 200:
                data = response.json()
                posts = data.get("data", [])

                if not posts:
                    return "No recent activity on the page"

                result = "Facebook Page Recent Activity:\n\n"
                for post in posts[:5]:
                    msg = post.get("message", "")[:50] + "..." if post.get("message") else "[No text]"
                    created = post.get("created_time", "Unknown")
                    reactions = post.get("reactions", {}).get("summary", {}).get("total_count", 0)
                    comments = post.get("comments", {}).get("data", [])

                    result += f"Post: {msg}\n"
                    result += f"  Created: {created}\n"
                    result += f"  Reactions: {reactions}\n"
                    result += f"  Comments: {len(comments)}\n\n"

                return result
            else:
                error_data = response.json()
                error_msg = error_data.get("error", {}).get("message", response.text)
                return f"Failed to get notifications: {response.status_code} - {error_msg}"

    except Exception as e:
        log_action("facebook_notifications_error", {"error": str(e)})
        return f"Error getting notifications: {str(e)}"


async def _get_page_info() -> str:
    """Get basic information about the Facebook Page."""
    if DRY_RUN:
        return "[DRY RUN] Would fetch Facebook Page info"

    if not PAGE_ACCESS_TOKEN:
        return "Error: Facebook Page access token not configured"

    if not PAGE_ID:
        return "Error: Facebook Page ID not configured"

    try:
        params = {
            "access_token": PAGE_ACCESS_TOKEN,
            "fields": "name,about,fan_count,followers_count,website,category"
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{API_BASE}/{PAGE_ID}",
                params=params
            )

            if response.status_code == 200:
                data = response.json()
                return (
                    f"Facebook Page Info:\n"
                    f"- Name: {data.get('name', 'Unknown')}\n"
                    f"- Category: {data.get('category', 'Unknown')}\n"
                    f"- About: {data.get('about', 'N/A')}\n"
                    f"- Fans: {data.get('fan_count', 0)}\n"
                    f"- Followers: {data.get('followers_count', 0)}\n"
                    f"- Website: {data.get('website', 'N/A')}"
                )
            else:
                error_data = response.json()
                error_msg = error_data.get("error", {}).get("message", response.text)
                return f"Failed to get page info: {response.status_code} - {error_msg}"

    except Exception as e:
        return f"Error getting page info: {str(e)}"


async def _check_connection() -> str:
    """Check if Facebook API connection is working."""
    if not PAGE_ACCESS_TOKEN:
        return "Error: Facebook Page access token not configured"

    if not PAGE_ID:
        return "Error: Facebook Page ID not configured"

    try:
        params = {
            "access_token": PAGE_ACCESS_TOKEN,
            "fields": "name"
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{API_BASE}/{PAGE_ID}",
                params=params
            )

            if response.status_code == 200:
                data = response.json()
                page_name = data.get("name", "Unknown")
                return f"Facebook API connection is active. Page: {page_name}"
            elif response.status_code == 401:
                return "Facebook token expired or invalid"
            else:
                return f"Facebook API returned status: {response.status_code}"

    except Exception as e:
        return f"Connection check failed: {str(e)}"


@app.list_tools()
async def handle_list_tools():
    """List available Facebook tools."""
    return [
        Tool(
            name="post_to_page",
            description="Create a post on the Facebook Page",
            inputSchema={
                "type": "object",
                "properties": {
                    "content": {"type": "string", "description": "Post content (text)"},
                    "link": {"type": "string", "description": "Optional URL to include with the post"}
                },
                "required": ["content"]
            }
        ),
        Tool(
            name="get_page_insights",
            description="Get Facebook Page insights and analytics",
            inputSchema={
                "type": "object",
                "properties": {
                    "metric": {
                        "type": "string",
                        "description": "Metric to retrieve: page_impressions, page_engaged_users, page_post_engagements, page_fans",
                        "default": "page_impressions"
                    },
                    "period": {
                        "type": "string",
                        "description": "Time period: day, week, days_28",
                        "default": "day"
                    }
                }
            }
        ),
        Tool(
            name="get_page_notifications",
            description="Get recent notifications for the Facebook Page",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="get_page_info",
            description="Get basic information about the Facebook Page",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="check_connection",
            description="Check if Facebook API connection is working",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        )
    ]


@app.call_tool()
async def handle_call_tool(name: str, arguments: dict):
    """Handle tool calls."""
    if name == "post_to_page":
        result = await _post_to_page(
            content=arguments["content"],
            link=arguments.get("link")
        )
    elif name == "get_page_insights":
        result = await _get_page_insights(
            metric=arguments.get("metric", "page_impressions"),
            period=arguments.get("period", "day")
        )
    elif name == "get_page_notifications":
        result = await _get_page_notifications()
    elif name == "get_page_info":
        result = await _get_page_info()
    elif name == "check_connection":
        result = await _check_connection()
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
