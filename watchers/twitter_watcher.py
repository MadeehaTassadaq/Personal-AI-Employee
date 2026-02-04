"""Twitter/X notifications and activity watcher using Twitter API v2."""

import os
import json
from pathlib import Path
from datetime import datetime
from typing import Any, Optional

import httpx

from .base_watcher import BaseWatcher


class TwitterWatcher(BaseWatcher):
    """Watches Twitter/X for mentions, DMs, and relevant activities."""

    API_BASE = "https://api.twitter.com/2"

    def __init__(
        self,
        vault_path: str,
        bearer_token: str,
        user_id: str = None,
        check_interval: int = 300,  # 5 minutes default
    ):
        """Initialize Twitter watcher.

        Args:
            vault_path: Path to Obsidian vault
            bearer_token: Twitter Bearer Token
            user_id: Twitter User ID (optional, will be fetched if not provided)
            check_interval: Seconds between checks
        """
        super().__init__(vault_path, check_interval)

        self.bearer_token = bearer_token
        self.headers = {
            "Authorization": f"Bearer {bearer_token}",
        }

        # Get user ID if not provided
        if user_id:
            self.user_id = user_id
        else:
            self.user_id = self._get_user_id()

        self.seen_activities: set[str] = set()
        self._load_seen_activities()

    def _get_user_id(self) -> str:
        """Get the user ID for the authenticated account."""
        try:
            with httpx.Client() as client:
                response = client.get(
                    f"{self.API_BASE}/users/by/username/me",
                    headers=self.headers
                )

                if response.status_code == 200:
                    data = response.json()
                    return data.get("data", {}).get("id", "")
                else:
                    self.logger.error(f"Could not fetch user ID: {response.status_code}")
                    return ""
        except Exception as e:
            self.logger.error(f"Error getting user ID: {e}")
            return ""

    def _load_seen_activities(self) -> None:
        """Load previously seen activity IDs."""
        seen_file = self.vault_path / ".twitter_seen.json"
        if seen_file.exists():
            try:
                self.seen_activities = set(json.loads(seen_file.read_text()))
            except json.JSONDecodeError:
                self.seen_activities = set()

    def _save_seen_activities(self) -> None:
        """Save seen activity IDs."""
        seen_file = self.vault_path / ".twitter_seen.json"
        recent = list(self.seen_activities)[-500:]
        seen_file.write_text(json.dumps(recent))

    def check_for_updates(self) -> list[dict]:
        """Check Twitter for new activities.

        Returns:
            List of new activities
        """
        new_items = []

        if not self.user_id:
            self.logger.error("Cannot check Twitter: user_id not available")
            return []

        try:
            with httpx.Client() as client:
                # Check for mentions and replies
                mentions_response = client.get(
                    f"{self.API_BASE}/users/{self.user_id}/mentions",
                    headers=self.headers,
                    params={
                        "tweet.fields": "id,text,author_id,created_at,public_metrics,context_annotations,entities",
                        "expansions": "author_id",
                        "user.fields": "id,name,username,verified",
                        "max_results": 10
                    }
                )

                if mentions_response.status_code == 200:
                    mentions_data = mentions_response.json()

                    # Get users from expansions
                    users_map = {}
                    if "includes" in mentions_data and "users" in mentions_data["includes"]:
                        for user in mentions_data["includes"]["users"]:
                            users_map[user["id"]] = user

                    # Process tweets
                    tweets = mentions_data.get("data", [])
                    for tweet in tweets:
                        tweet_id = tweet.get("id", "")
                        if tweet_id and tweet_id not in self.seen_activities:
                            # Add user info to tweet data
                            author_id = tweet.get("author_id", "")
                            if author_id in users_map:
                                tweet["author"] = users_map[author_id]

                            new_items.append({
                                "type": "mention",
                                "id": tweet_id,
                                "data": tweet
                            })
                            self.seen_activities.add(tweet_id)

                # Check for new messages (DMs) - Twitter API v2 doesn't have DM endpoints
                # We'll monitor for DM notifications through webhook or alternative approach
                # For now, we'll focus on public interactions

                # Check for new follows
                follows_response = client.get(
                    f"{self.API_BASE}/users/{self.user_id}/following",
                    headers=self.headers,
                    params={
                        "user.fields": "id,name,username,verified,description,public_metrics",
                        "max_results": 10
                    }
                )

                if follows_response.status_code == 200:
                    follows_data = follows_response.json()
                    follows = follows_data.get("data", [])

                    for follow in follows:
                        follow_id = follow.get("id", "")
                        if follow_id and follow_id not in self.seen_activities:
                            new_items.append({
                                "type": "follow",
                                "id": follow_id,
                                "data": follow
                            })
                            self.seen_activities.add(follow_id)

                # Check for likes on recent tweets (would require knowing our recent tweets)
                # This would typically be handled through webhooks, but we'll do a simple check
                # by monitoring our recent tweets for engagement

        except httpx.RequestError as e:
            self.logger.error(f"Twitter API error: {e}")
        except Exception as e:
            self.logger.error(f"Error checking Twitter: {e}")

        if new_items:
            self._save_seen_activities()

        return new_items

    def on_new_item(self, item: dict) -> None:
        """Handle a new Twitter activity.

        Args:
            item: Activity data
        """
        item_type = item.get("type", "unknown")
        item_id = item.get("id", "")
        data = item.get("data", {})

        if item_type == "mention":
            # New mention or reply
            text = data.get("text", "")[:200] + "..." if len(data.get("text", "")) > 200 else data.get("text", "")
            created_at = data.get("created_at", datetime.now().isoformat())

            # Get author info
            author = data.get("author", {})
            author_name = author.get("name", "Unknown")
            author_username = author.get("username", "unknown")
            verified = author.get("verified", False)

            content = f"""## Twitter Mention/Reply
- **Author:** {author_name} (@{author_username}){' ✓' if verified else ''}
- **Posted:** {created_at}
- **Tweet ID:** {item_id}

## Tweet Text
{text}

## Engagement Metrics
- **Retweets:** {data.get('public_metrics', {}).get('retweet_count', 0)}
- **Likes:** {data.get('public_metrics', {}).get('like_count', 0)}
- **Replies:** {data.get('public_metrics', {}).get('reply_count', 0)}
- **Quotes:** {data.get('public_metrics', {}).get('quote_count', 0)}

## Action Items
- [ ] Review mention content
- [ ] Respond appropriately if needed
- [ ] Engage with the tweet if relevant
"""
            title = f"Twitter: Mention by @{author_username}"
            self.create_task_file(title, content, "high")

        elif item_type == "follow":
            # New follower
            name = data.get("name", "Unknown")
            username = data.get("username", "unknown")
            verified = data.get("verified", False)
            description = data.get("description", "")

            content = f"""## Twitter Follow
- **Name:** {name} (@{username}){' ✓' if verified else ''}
- **Followed:** {datetime.now().isoformat()}

## Profile Description
{description}

## Public Metrics
- **Followers:** {data.get('public_metrics', {}).get('followers_count', 0)}
- **Following:** {data.get('public_metrics', {}).get('following_count', 0)}
- **Tweets:** {data.get('public_metrics', {}).get('tweet_count', 0)}

## Action Items
- [ ] Review profile
- [ ] Welcome new follower if appropriate
- [ ] Check for spam accounts
"""
            title = f"Twitter: New Follower @{username}"
            self.create_task_file(title, content, "medium")

        else:
            # Generic Twitter activity
            content = f"""## Twitter Activity
- **Type:** {item_type}
- **Received:** {datetime.now().isoformat()}

## Details
```json
{json.dumps(data, indent=2)[:500]}
```

## Action Items
- [ ] Review activity
"""
            title = f"Twitter: {item_type.replace('_', ' ').title()}"
            self.create_task_file(title, content, "low")

        self.log_event("twitter_activity", {
            "type": item_type,
            "id": item_id
        })


if __name__ == "__main__":
    import sys

    vault = sys.argv[1] if len(sys.argv) > 1 else "./vault"
    token = os.getenv("TWITTER_BEARER_TOKEN", "")

    if not token:
        print("Error: TWITTER_BEARER_TOKEN must be set")
        sys.exit(1)

    # Optionally pass user ID as command line arg
    user_id = sys.argv[2] if len(sys.argv) > 2 else None

    watcher = TwitterWatcher(vault, token, user_id)

    try:
        watcher.run()
    except KeyboardInterrupt:
        watcher.stop()