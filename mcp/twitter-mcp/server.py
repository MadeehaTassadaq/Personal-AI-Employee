"""Twitter/X MCP Server for posting and analytics.

Uses Twitter API v2 with OAuth 2.0.
Requires a Twitter Developer account and app with Read/Write permissions.
"""

import os
import json
import base64
import hashlib
import hmac
import time
from pathlib import Path
from datetime import datetime
from typing import Optional
from urllib.parse import quote

import httpx
from mcp.server import Server
from mcp.types import Tool, TextContent

app = Server("twitter-mcp")

# Configuration
DRY_RUN = os.getenv("DRY_RUN", "true").lower() == "true"
API_KEY = os.getenv("TWITTER_API_KEY", "")
API_SECRET = os.getenv("TWITTER_API_SECRET", "")
ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN", "")
ACCESS_TOKEN_SECRET = os.getenv("TWITTER_ACCESS_TOKEN_SECRET", "")
BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN", "")

API_BASE_V2 = "https://api.twitter.com/2"


def log_action(action: str, details: dict) -> None:
    """Log an MCP action."""
    log_dir = Path(os.getenv("VAULT_PATH", "./vault")) / "Logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    log_file = log_dir / f"{datetime.now().strftime('%Y-%m-%d')}.json"

    entry = {
        "timestamp": datetime.now().isoformat(),
        "watcher": "TwitterMCP",
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


def create_oauth_signature(
    method: str,
    url: str,
    params: dict,
    oauth_params: dict
) -> str:
    """Create OAuth 1.0a signature for Twitter API."""
    # Combine all parameters
    all_params = {**params, **oauth_params}

    # Sort and encode parameters
    sorted_params = sorted(all_params.items())
    param_string = "&".join(
        f"{quote(str(k), safe='')}"
        f"={quote(str(v), safe='')}"
        for k, v in sorted_params
    )

    # Create signature base string
    base_string = (
        f"{method.upper()}&"
        f"{quote(url, safe='')}&"
        f"{quote(param_string, safe='')}"
    )

    # Create signing key
    signing_key = f"{quote(API_SECRET, safe='')}&{quote(ACCESS_TOKEN_SECRET, safe='')}"

    # Generate signature
    signature = hmac.new(
        signing_key.encode(),
        base_string.encode(),
        hashlib.sha1
    )

    return base64.b64encode(signature.digest()).decode()


def get_oauth_header(method: str, url: str, params: dict = None) -> str:
    """Generate OAuth 1.0a header for Twitter API."""
    params = params or {}

    oauth_params = {
        "oauth_consumer_key": API_KEY,
        "oauth_token": ACCESS_TOKEN,
        "oauth_signature_method": "HMAC-SHA1",
        "oauth_timestamp": str(int(time.time())),
        "oauth_nonce": base64.b64encode(os.urandom(32)).decode().replace("=", ""),
        "oauth_version": "1.0"
    }

    signature = create_oauth_signature(method, url, params, oauth_params)
    oauth_params["oauth_signature"] = signature

    header_params = ", ".join(
        f'{quote(k, safe="")}="{quote(v, safe="")}"'
        for k, v in sorted(oauth_params.items())
    )

    return f"OAuth {header_params}"


def get_bearer_header() -> dict:
    """Get headers with Bearer token for read-only operations."""
    return {
        "Authorization": f"Bearer {BEARER_TOKEN}",
        "Content-Type": "application/json"
    }


@app.tool()
async def post_tweet(content: str, reply_to: Optional[str] = None) -> str:
    """Post a tweet to Twitter/X.

    Args:
        content: Tweet content (max 280 characters)
        reply_to: Optional tweet ID to reply to

    Returns:
        Result message with tweet ID or error
    """
    if len(content) > 280:
        return f"Error: Tweet exceeds 280 characters (current: {len(content)})"

    log_action("twitter_post_requested", {
        "content_length": len(content),
        "is_reply": reply_to is not None,
        "dry_run": DRY_RUN
    })

    if DRY_RUN:
        reply_info = f"\nIn reply to: {reply_to}" if reply_to else ""
        return f"[DRY RUN] Would post tweet:\n{content}{reply_info}"

    if not all([API_KEY, API_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SECRET]):
        return "Error: Twitter OAuth credentials not fully configured"

    try:
        url = f"{API_BASE_V2}/tweets"

        tweet_data = {"text": content}
        if reply_to:
            tweet_data["reply"] = {"in_reply_to_tweet_id": reply_to}

        oauth_header = get_oauth_header("POST", url)

        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                headers={
                    "Authorization": oauth_header,
                    "Content-Type": "application/json"
                },
                json=tweet_data
            )

            if response.status_code in [200, 201]:
                data = response.json()
                tweet_id = data.get("data", {}).get("id", "unknown")
                log_action("twitter_posted", {
                    "tweet_id": tweet_id,
                    "content_length": len(content)
                })
                return f"Tweet posted successfully. Tweet ID: {tweet_id}"
            else:
                error_data = response.json()
                error_msg = error_data.get("detail", response.text)
                log_action("twitter_post_failed", {
                    "status": response.status_code,
                    "error": error_msg
                })
                return f"Failed to post tweet: {response.status_code} - {error_msg}"

    except Exception as e:
        log_action("twitter_post_error", {"error": str(e)})
        return f"Error posting tweet: {str(e)}"


@app.tool()
async def get_mentions(count: int = 10) -> str:
    """Get recent mentions of the authenticated user.

    Args:
        count: Number of mentions to retrieve (max 100)

    Returns:
        List of recent mentions or error message
    """
    log_action("twitter_mentions_requested", {"count": count, "dry_run": DRY_RUN})

    if DRY_RUN:
        return f"[DRY RUN] Would fetch last {count} Twitter mentions"

    if not BEARER_TOKEN:
        return "Error: Twitter Bearer token not configured"

    try:
        # First get the authenticated user's ID
        async with httpx.AsyncClient() as client:
            me_response = await client.get(
                f"{API_BASE_V2}/users/me",
                headers=get_bearer_header()
            )

            if me_response.status_code != 200:
                return f"Failed to get user info: {me_response.status_code}"

            user_id = me_response.json().get("data", {}).get("id")

            # Now get mentions
            params = {
                "max_results": min(count, 100),
                "tweet.fields": "created_at,author_id,text",
                "expansions": "author_id",
                "user.fields": "username"
            }

            mentions_response = await client.get(
                f"{API_BASE_V2}/users/{user_id}/mentions",
                headers=get_bearer_header(),
                params=params
            )

            if mentions_response.status_code == 200:
                data = mentions_response.json()
                mentions = data.get("data", [])
                users = {
                    u["id"]: u["username"]
                    for u in data.get("includes", {}).get("users", [])
                }

                if not mentions:
                    return "No recent mentions found"

                result = "Recent Twitter Mentions:\n\n"
                for mention in mentions:
                    author_id = mention.get("author_id", "")
                    username = users.get(author_id, "Unknown")
                    result += f"@{username}: {mention.get('text', '')[:100]}...\n"
                    result += f"  Time: {mention.get('created_at', 'Unknown')}\n"
                    result += f"  ID: {mention.get('id')}\n\n"

                return result
            else:
                return f"Failed to get mentions: {mentions_response.status_code}"

    except Exception as e:
        log_action("twitter_mentions_error", {"error": str(e)})
        return f"Error getting mentions: {str(e)}"


@app.tool()
async def get_timeline(count: int = 10) -> str:
    """Get the home timeline of the authenticated user.

    Args:
        count: Number of tweets to retrieve (max 100)

    Returns:
        Recent timeline tweets or error message
    """
    log_action("twitter_timeline_requested", {"count": count, "dry_run": DRY_RUN})

    if DRY_RUN:
        return f"[DRY RUN] Would fetch last {count} timeline tweets"

    if not BEARER_TOKEN:
        return "Error: Twitter Bearer token not configured"

    try:
        async with httpx.AsyncClient() as client:
            # Get user ID
            me_response = await client.get(
                f"{API_BASE_V2}/users/me",
                headers=get_bearer_header()
            )

            if me_response.status_code != 200:
                return f"Failed to get user info: {me_response.status_code}"

            user_id = me_response.json().get("data", {}).get("id")

            # Get reverse chronological timeline
            params = {
                "max_results": min(count, 100),
                "tweet.fields": "created_at,author_id,public_metrics",
                "expansions": "author_id",
                "user.fields": "username"
            }

            timeline_response = await client.get(
                f"{API_BASE_V2}/users/{user_id}/timelines/reverse_chronological",
                headers=get_bearer_header(),
                params=params
            )

            if timeline_response.status_code == 200:
                data = timeline_response.json()
                tweets = data.get("data", [])
                users = {
                    u["id"]: u["username"]
                    for u in data.get("includes", {}).get("users", [])
                }

                if not tweets:
                    return "No timeline tweets found"

                result = "Twitter Timeline:\n\n"
                for tweet in tweets:
                    author_id = tweet.get("author_id", "")
                    username = users.get(author_id, "Unknown")
                    metrics = tweet.get("public_metrics", {})
                    result += f"@{username}: {tweet.get('text', '')[:100]}...\n"
                    result += f"  Likes: {metrics.get('like_count', 0)} | "
                    result += f"Retweets: {metrics.get('retweet_count', 0)} | "
                    result += f"Replies: {metrics.get('reply_count', 0)}\n\n"

                return result
            else:
                return f"Failed to get timeline: {timeline_response.status_code}"

    except Exception as e:
        log_action("twitter_timeline_error", {"error": str(e)})
        return f"Error getting timeline: {str(e)}"


@app.tool()
async def get_analytics() -> str:
    """Get analytics for recent tweets from the authenticated user.

    Returns:
        Analytics summary or error message
    """
    log_action("twitter_analytics_requested", {"dry_run": DRY_RUN})

    if DRY_RUN:
        return "[DRY RUN] Would fetch Twitter analytics"

    if not BEARER_TOKEN:
        return "Error: Twitter Bearer token not configured"

    try:
        async with httpx.AsyncClient() as client:
            # Get user ID
            me_response = await client.get(
                f"{API_BASE_V2}/users/me",
                headers=get_bearer_header(),
                params={"user.fields": "public_metrics"}
            )

            if me_response.status_code != 200:
                return f"Failed to get user info: {me_response.status_code}"

            user_data = me_response.json().get("data", {})
            user_id = user_data.get("id")
            user_metrics = user_data.get("public_metrics", {})

            # Get recent tweets with metrics
            params = {
                "max_results": 20,
                "tweet.fields": "created_at,public_metrics"
            }

            tweets_response = await client.get(
                f"{API_BASE_V2}/users/{user_id}/tweets",
                headers=get_bearer_header(),
                params=params
            )

            result = "Twitter Analytics Summary:\n\n"
            result += f"Account Metrics:\n"
            result += f"  Followers: {user_metrics.get('followers_count', 0)}\n"
            result += f"  Following: {user_metrics.get('following_count', 0)}\n"
            result += f"  Total Tweets: {user_metrics.get('tweet_count', 0)}\n\n"

            if tweets_response.status_code == 200:
                tweets = tweets_response.json().get("data", [])

                if tweets:
                    total_likes = sum(
                        t.get("public_metrics", {}).get("like_count", 0)
                        for t in tweets
                    )
                    total_retweets = sum(
                        t.get("public_metrics", {}).get("retweet_count", 0)
                        for t in tweets
                    )
                    total_replies = sum(
                        t.get("public_metrics", {}).get("reply_count", 0)
                        for t in tweets
                    )

                    result += f"Recent Tweets Performance (last {len(tweets)} tweets):\n"
                    result += f"  Total Likes: {total_likes}\n"
                    result += f"  Total Retweets: {total_retweets}\n"
                    result += f"  Total Replies: {total_replies}\n"
                    result += f"  Avg Engagement: {(total_likes + total_retweets + total_replies) / len(tweets):.1f}\n"

            return result

    except Exception as e:
        log_action("twitter_analytics_error", {"error": str(e)})
        return f"Error getting analytics: {str(e)}"


@app.tool()
async def get_user_info() -> str:
    """Get information about the authenticated Twitter user.

    Returns:
        User information or error message
    """
    if DRY_RUN:
        return "[DRY RUN] Would fetch Twitter user info"

    if not BEARER_TOKEN:
        return "Error: Twitter Bearer token not configured"

    try:
        params = {
            "user.fields": "name,username,description,public_metrics,created_at,verified"
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{API_BASE_V2}/users/me",
                headers=get_bearer_header(),
                params=params
            )

            if response.status_code == 200:
                data = response.json().get("data", {})
                metrics = data.get("public_metrics", {})
                return (
                    f"Twitter User Info:\n"
                    f"- Name: {data.get('name', 'Unknown')}\n"
                    f"- Username: @{data.get('username', 'Unknown')}\n"
                    f"- Bio: {data.get('description', 'N/A')}\n"
                    f"- Verified: {data.get('verified', False)}\n"
                    f"- Followers: {metrics.get('followers_count', 0)}\n"
                    f"- Following: {metrics.get('following_count', 0)}\n"
                    f"- Tweets: {metrics.get('tweet_count', 0)}\n"
                    f"- Joined: {data.get('created_at', 'Unknown')}"
                )
            else:
                return f"Failed to get user info: {response.status_code}"

    except Exception as e:
        return f"Error getting user info: {str(e)}"


@app.tool()
async def check_connection() -> str:
    """Check if Twitter API connection is working.

    Returns:
        Connection status
    """
    if not BEARER_TOKEN:
        return "Error: Twitter Bearer token not configured"

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{API_BASE_V2}/users/me",
                headers=get_bearer_header()
            )

            if response.status_code == 200:
                data = response.json().get("data", {})
                username = data.get("username", "Unknown")
                return f"Twitter API connection is active. User: @{username}"
            elif response.status_code == 401:
                return "Twitter token expired or invalid"
            else:
                return f"Twitter API returned status: {response.status_code}"

    except Exception as e:
        return f"Connection check failed: {str(e)}"


if __name__ == "__main__":
    app.run()
