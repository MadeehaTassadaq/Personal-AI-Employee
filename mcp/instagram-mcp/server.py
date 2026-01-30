"""Instagram MCP Server for business account posting and insights.

Uses the Instagram Graph API which requires:
1. A Business or Creator Instagram account
2. A linked Facebook Page
3. A Facebook Page Access Token with instagram_basic and instagram_content_publish permissions
"""

import os
import json
from pathlib import Path
from datetime import datetime
from typing import Optional

import httpx
from mcp.server import Server
from mcp.types import Tool, TextContent

app = Server("instagram-mcp")

# Configuration
DRY_RUN = os.getenv("DRY_RUN", "true").lower() == "true"
PAGE_ACCESS_TOKEN = os.getenv("FACEBOOK_PAGE_ACCESS_TOKEN", "")
INSTAGRAM_ACCOUNT_ID = os.getenv("INSTAGRAM_BUSINESS_ACCOUNT_ID", "")
API_VERSION = "v18.0"
API_BASE = f"https://graph.facebook.com/{API_VERSION}"


def log_action(action: str, details: dict) -> None:
    """Log an MCP action."""
    log_dir = Path(os.getenv("VAULT_PATH", "./vault")) / "Logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    log_file = log_dir / f"{datetime.now().strftime('%Y-%m-%d')}.json"

    entry = {
        "timestamp": datetime.now().isoformat(),
        "watcher": "InstagramMCP",
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
async def post_image(image_url: str, caption: str) -> str:
    """Post an image to Instagram.

    Note: The image must be hosted at a publicly accessible URL.
    Instagram will fetch the image from this URL.

    Args:
        image_url: Public URL of the image to post (must be accessible by Instagram)
        caption: Caption for the post (max 2,200 characters, 30 hashtags)

    Returns:
        Result message with post ID or error
    """
    log_action("instagram_post_requested", {
        "image_url": image_url[:50] + "...",
        "caption_length": len(caption),
        "dry_run": DRY_RUN
    })

    if DRY_RUN:
        return f"[DRY RUN] Would create Instagram post:\nImage: {image_url[:50]}...\nCaption: {caption[:100]}..."

    if not PAGE_ACCESS_TOKEN:
        return "Error: Facebook Page access token not configured"

    if not INSTAGRAM_ACCOUNT_ID:
        return "Error: Instagram Business Account ID not configured"

    try:
        # Step 1: Create a media container
        container_data = {
            "image_url": image_url,
            "caption": caption,
            "access_token": PAGE_ACCESS_TOKEN
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            # Create container
            container_response = await client.post(
                f"{API_BASE}/{INSTAGRAM_ACCOUNT_ID}/media",
                data=container_data
            )

            if container_response.status_code != 200:
                error_data = container_response.json()
                error_msg = error_data.get("error", {}).get("message", container_response.text)
                log_action("instagram_container_failed", {"error": error_msg})
                return f"Failed to create media container: {error_msg}"

            container_id = container_response.json().get("id")

            # Step 2: Publish the container
            publish_data = {
                "creation_id": container_id,
                "access_token": PAGE_ACCESS_TOKEN
            }

            publish_response = await client.post(
                f"{API_BASE}/{INSTAGRAM_ACCOUNT_ID}/media_publish",
                data=publish_data
            )

            if publish_response.status_code == 200:
                post_id = publish_response.json().get("id", "unknown")
                log_action("instagram_posted", {
                    "post_id": post_id,
                    "caption_length": len(caption)
                })
                return f"Post created successfully. Post ID: {post_id}"
            else:
                error_data = publish_response.json()
                error_msg = error_data.get("error", {}).get("message", publish_response.text)
                log_action("instagram_publish_failed", {"error": error_msg})
                return f"Failed to publish post: {error_msg}"

    except Exception as e:
        log_action("instagram_post_error", {"error": str(e)})
        return f"Error creating post: {str(e)}"


@app.tool()
async def post_carousel(image_urls: str, caption: str) -> str:
    """Post a carousel (multiple images) to Instagram.

    Args:
        image_urls: Comma-separated list of public image URLs (2-10 images)
        caption: Caption for the carousel post

    Returns:
        Result message with post ID or error
    """
    urls = [url.strip() for url in image_urls.split(",")]

    if len(urls) < 2 or len(urls) > 10:
        return "Error: Carousel requires 2-10 images"

    log_action("instagram_carousel_requested", {
        "image_count": len(urls),
        "caption_length": len(caption),
        "dry_run": DRY_RUN
    })

    if DRY_RUN:
        return f"[DRY RUN] Would create Instagram carousel with {len(urls)} images:\nCaption: {caption[:100]}..."

    if not PAGE_ACCESS_TOKEN:
        return "Error: Facebook Page access token not configured"

    if not INSTAGRAM_ACCOUNT_ID:
        return "Error: Instagram Business Account ID not configured"

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            # Step 1: Create containers for each image
            children_ids = []

            for url in urls:
                container_data = {
                    "image_url": url,
                    "is_carousel_item": "true",
                    "access_token": PAGE_ACCESS_TOKEN
                }

                response = await client.post(
                    f"{API_BASE}/{INSTAGRAM_ACCOUNT_ID}/media",
                    data=container_data
                )

                if response.status_code != 200:
                    error_msg = response.json().get("error", {}).get("message", response.text)
                    return f"Failed to create carousel item: {error_msg}"

                children_ids.append(response.json().get("id"))

            # Step 2: Create the carousel container
            carousel_data = {
                "media_type": "CAROUSEL",
                "caption": caption,
                "children": ",".join(children_ids),
                "access_token": PAGE_ACCESS_TOKEN
            }

            carousel_response = await client.post(
                f"{API_BASE}/{INSTAGRAM_ACCOUNT_ID}/media",
                data=carousel_data
            )

            if carousel_response.status_code != 200:
                error_msg = carousel_response.json().get("error", {}).get("message", carousel_response.text)
                return f"Failed to create carousel: {error_msg}"

            carousel_id = carousel_response.json().get("id")

            # Step 3: Publish the carousel
            publish_data = {
                "creation_id": carousel_id,
                "access_token": PAGE_ACCESS_TOKEN
            }

            publish_response = await client.post(
                f"{API_BASE}/{INSTAGRAM_ACCOUNT_ID}/media_publish",
                data=publish_data
            )

            if publish_response.status_code == 200:
                post_id = publish_response.json().get("id", "unknown")
                log_action("instagram_carousel_posted", {
                    "post_id": post_id,
                    "image_count": len(urls)
                })
                return f"Carousel posted successfully. Post ID: {post_id}"
            else:
                error_msg = publish_response.json().get("error", {}).get("message", publish_response.text)
                return f"Failed to publish carousel: {error_msg}"

    except Exception as e:
        log_action("instagram_carousel_error", {"error": str(e)})
        return f"Error creating carousel: {str(e)}"


@app.tool()
async def get_insights(metric: str = "impressions") -> str:
    """Get Instagram account insights.

    Args:
        metric: Metric to retrieve. Options:
            - impressions: Total content impressions
            - reach: Unique accounts reached
            - profile_views: Profile view count
            - follower_count: Current follower count

    Returns:
        Insights data or error message
    """
    log_action("instagram_insights_requested", {
        "metric": metric,
        "dry_run": DRY_RUN
    })

    if DRY_RUN:
        return f"[DRY RUN] Would fetch Instagram insights for: {metric}"

    if not PAGE_ACCESS_TOKEN:
        return "Error: Facebook Page access token not configured"

    if not INSTAGRAM_ACCOUNT_ID:
        return "Error: Instagram Business Account ID not configured"

    try:
        params = {
            "metric": metric,
            "period": "day",
            "access_token": PAGE_ACCESS_TOKEN
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{API_BASE}/{INSTAGRAM_ACCOUNT_ID}/insights",
                params=params
            )

            if response.status_code == 200:
                data = response.json()
                insights = data.get("data", [])

                if not insights:
                    return f"No insights data available for {metric}"

                result = f"Instagram Insights - {metric}:\n"
                for insight in insights:
                    values = insight.get("values", [])
                    for v in values[-7:]:  # Last 7 data points
                        result += f"- {v.get('end_time', 'N/A')}: {v.get('value', 0)}\n"

                return result
            else:
                error_data = response.json()
                error_msg = error_data.get("error", {}).get("message", response.text)
                return f"Failed to get insights: {response.status_code} - {error_msg}"

    except Exception as e:
        log_action("instagram_insights_error", {"error": str(e)})
        return f"Error getting insights: {str(e)}"


@app.tool()
async def get_media(limit: int = 10) -> str:
    """Get recent Instagram posts/media.

    Args:
        limit: Number of posts to retrieve (max 50)

    Returns:
        List of recent posts or error message
    """
    if DRY_RUN:
        return f"[DRY RUN] Would fetch last {limit} Instagram posts"

    if not PAGE_ACCESS_TOKEN:
        return "Error: Facebook Page access token not configured"

    if not INSTAGRAM_ACCOUNT_ID:
        return "Error: Instagram Business Account ID not configured"

    try:
        params = {
            "fields": "id,caption,media_type,timestamp,like_count,comments_count,permalink",
            "limit": min(limit, 50),
            "access_token": PAGE_ACCESS_TOKEN
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{API_BASE}/{INSTAGRAM_ACCOUNT_ID}/media",
                params=params
            )

            if response.status_code == 200:
                data = response.json()
                posts = data.get("data", [])

                if not posts:
                    return "No posts found"

                result = "Recent Instagram Posts:\n\n"
                for post in posts:
                    caption = post.get("caption", "")[:50] + "..." if post.get("caption") else "[No caption]"
                    result += f"ID: {post.get('id')}\n"
                    result += f"  Type: {post.get('media_type', 'Unknown')}\n"
                    result += f"  Caption: {caption}\n"
                    result += f"  Likes: {post.get('like_count', 0)}\n"
                    result += f"  Comments: {post.get('comments_count', 0)}\n"
                    result += f"  Posted: {post.get('timestamp', 'Unknown')}\n\n"

                return result
            else:
                error_data = response.json()
                error_msg = error_data.get("error", {}).get("message", response.text)
                return f"Failed to get media: {response.status_code} - {error_msg}"

    except Exception as e:
        return f"Error getting media: {str(e)}"


@app.tool()
async def get_account_info() -> str:
    """Get Instagram business account information.

    Returns:
        Account information or error message
    """
    if DRY_RUN:
        return "[DRY RUN] Would fetch Instagram account info"

    if not PAGE_ACCESS_TOKEN:
        return "Error: Facebook Page access token not configured"

    if not INSTAGRAM_ACCOUNT_ID:
        return "Error: Instagram Business Account ID not configured"

    try:
        params = {
            "fields": "username,name,biography,followers_count,follows_count,media_count,profile_picture_url,website",
            "access_token": PAGE_ACCESS_TOKEN
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{API_BASE}/{INSTAGRAM_ACCOUNT_ID}",
                params=params
            )

            if response.status_code == 200:
                data = response.json()
                return (
                    f"Instagram Account Info:\n"
                    f"- Username: @{data.get('username', 'Unknown')}\n"
                    f"- Name: {data.get('name', 'Unknown')}\n"
                    f"- Bio: {data.get('biography', 'N/A')}\n"
                    f"- Followers: {data.get('followers_count', 0)}\n"
                    f"- Following: {data.get('follows_count', 0)}\n"
                    f"- Posts: {data.get('media_count', 0)}\n"
                    f"- Website: {data.get('website', 'N/A')}"
                )
            else:
                error_data = response.json()
                error_msg = error_data.get("error", {}).get("message", response.text)
                return f"Failed to get account info: {response.status_code} - {error_msg}"

    except Exception as e:
        return f"Error getting account info: {str(e)}"


@app.tool()
async def check_connection() -> str:
    """Check if Instagram API connection is working.

    Returns:
        Connection status
    """
    if not PAGE_ACCESS_TOKEN:
        return "Error: Facebook Page access token not configured"

    if not INSTAGRAM_ACCOUNT_ID:
        return "Error: Instagram Business Account ID not configured"

    try:
        params = {
            "fields": "username",
            "access_token": PAGE_ACCESS_TOKEN
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{API_BASE}/{INSTAGRAM_ACCOUNT_ID}",
                params=params
            )

            if response.status_code == 200:
                data = response.json()
                username = data.get("username", "Unknown")
                return f"Instagram API connection is active. Account: @{username}"
            elif response.status_code == 401:
                return "Instagram token expired or invalid"
            else:
                return f"Instagram API returned status: {response.status_code}"

    except Exception as e:
        return f"Connection check failed: {str(e)}"


if __name__ == "__main__":
    app.run()
