"""Instagram notifications and activity watcher using Meta Graph API."""

import os
import json
from pathlib import Path
from datetime import datetime
from typing import Any, Optional

import httpx

from .base_watcher import BaseWatcher


class InstagramWatcher(BaseWatcher):
    """Watches Instagram for new posts, comments, and messages."""

    API_BASE = "https://graph.instagram.com"

    def __init__(
        self,
        vault_path: str,
        access_token: str,
        instagram_business_account_id: str,
        check_interval: int = 300,  # 5 minutes default
    ):
        """Initialize Instagram watcher.

        Args:
            vault_path: Path to Obsidian vault
            access_token: Instagram access token
            instagram_business_account_id: Instagram Business Account ID
            check_interval: Seconds between checks
        """
        super().__init__(vault_path, check_interval)

        self.access_token = access_token
        self.instagram_business_account_id = instagram_business_account_id
        self.headers = {
            "Authorization": f"Bearer {access_token}",
        }
        self.seen_activities: set[str] = set()
        self._load_seen_activities()

    def _load_seen_activities(self) -> None:
        """Load previously seen activity IDs."""
        seen_file = self.vault_path / ".instagram_seen.json"
        if seen_file.exists():
            try:
                self.seen_activities = set(json.loads(seen_file.read_text()))
            except json.JSONDecodeError:
                self.seen_activities = set()

    def _save_seen_activities(self) -> None:
        """Save seen activity IDs."""
        seen_file = self.vault_path / ".instagram_seen.json"
        recent = list(self.seen_activities)[-500:]
        seen_file.write_text(json.dumps(recent))

    def check_for_updates(self) -> list[dict]:
        """Check Instagram for new activities.

        Returns:
            List of new activities
        """
        new_items = []

        try:
            with httpx.Client() as client:
                # Check for new media posts
                media_response = client.get(
                    f"{self.API_BASE}/{self.instagram_business_account_id}/media",
                    params={
                        "fields": "id,caption,permalink,media_type,media_url,username,timestamp,comments_count,like_count",
                        "limit": 10,
                        "access_token": self.access_token
                    }
                )

                if media_response.status_code == 200:
                    media_data = media_response.json()
                    media_items = media_data.get("data", [])

                    for media in media_items:
                        media_id = media.get("id", "")
                        if media_id and media_id not in self.seen_activities:
                            new_items.append({
                                "type": "media_post",
                                "id": media_id,
                                "data": media
                            })
                            self.seen_activities.add(media_id)

                # Check for new comments on posts
                for media in media_items[:5]:  # Check comments on recent posts only
                    media_id = media.get("id", "")
                    comments_response = client.get(
                        f"{self.API_BASE}/{media_id}/comments",
                        params={
                            "fields": "id,text,username,timestamp,replies",
                            "limit": 10,
                            "access_token": self.access_token
                        }
                    )

                    if comments_response.status_code == 200:
                        comments_data = comments_response.json()
                        comments = comments_data.get("data", [])

                        for comment in comments:
                            comment_id = comment.get("id", "")
                            if comment_id and comment_id not in self.seen_activities:
                                new_items.append({
                                    "type": "comment",
                                    "id": comment_id,
                                    "parent_media_id": media_id,
                                    "data": comment
                                })
                                self.seen_activities.add(comment_id)

                # Check for new mentions (tagged posts)
                mentions_response = client.get(
                    f"{self.API_BASE}/{self.instagram_business_account_id}/mentioned_media",
                    params={
                        "fields": "id,caption,permalink,media_type,media_url,username,timestamp",
                        "access_token": self.access_token
                    }
                )

                if mentions_response.status_code == 200:
                    mentions_data = mentions_response.json()
                    mentions = mentions_data.get("data", [])

                    for mention in mentions:
                        mention_id = mention.get("id", "")
                        if mention_id and mention_id not in self.seen_activities:
                            new_items.append({
                                "type": "mention",
                                "id": mention_id,
                                "data": mention
                            })
                            self.seen_activities.add(mention_id)

        except httpx.RequestError as e:
            self.logger.error(f"Instagram API error: {e}")
        except Exception as e:
            self.logger.error(f"Error checking Instagram: {e}")

        if new_items:
            self._save_seen_activities()

        return new_items

    def on_new_item(self, item: dict) -> None:
        """Handle a new Instagram activity.

        Args:
            item: Activity data
        """
        item_type = item.get("type", "unknown")
        item_id = item.get("id", "")
        data = item.get("data", {})

        if item_type == "media_post":
            # New media post from the account
            caption = data.get("caption", "")[:100] + "..." if len(data.get("caption", "")) > 100 else data.get("caption", "")
            username = data.get("username", "Unknown")
            media_type = data.get("media_type", "UNKNOWN")
            permalink = data.get("permalink", "")

            content = f"""## Instagram Post
- **Username:** {username}
- **Media Type:** {media_type}
- **Posted:** {data.get('timestamp', datetime.now().isoformat())}
- **Post ID:** {item_id}
- **Permalink:** {permalink}

## Caption
{caption}

## Engagement
- **Likes:** {data.get('like_count', 0)}
- **Comments:** {data.get('comments_count', 0)}

## Action Items
- [ ] Review post performance
- [ ] Engage with comments
- [ ] Plan similar content if successful
"""
            title = f"Instagram: New {media_type} Post by {username}"
            self.create_task_file(title, content, "medium")

        elif item_type == "comment":
            # New comment on a post
            comment_text = data.get("text", "")[:100] + "..." if len(data.get("text", "")) > 100 else data.get("text", "")
            username = data.get("username", "Unknown")
            parent_media_id = item.get("parent_media_id", "")

            content = f"""## Instagram Comment
- **Author:** {username}
- **Posted:** {data.get('timestamp', datetime.now().isoformat())}
- **Comment ID:** {item_id}
- **On Post:** {parent_media_id}

## Comment
{comment_text}

## Action Items
- [ ] Review comment content
- [ ] Respond appropriately
- [ ] Moderate if necessary
"""
            title = f"Instagram: Comment by {username}"
            self.create_task_file(title, content, "high")

        elif item_type == "mention":
            # New mention/tag in someone else's post
            caption = data.get("caption", "")[:100] + "..." if len(data.get("caption", "")) > 100 else data.get("caption", "")
            username = data.get("username", "Unknown")
            media_type = data.get("media_type", "UNKNOWN")
            permalink = data.get("permalink", "")

            content = f"""## Instagram Mention
- **Tagged by:** {username}
- **Media Type:** {media_type}
- **Posted:** {data.get('timestamp', datetime.now().isoformat())}
- **Mention ID:** {item_id}
- **Permalink:** {permalink}

## Caption
{caption}

## Action Items
- [ ] Review mention content
- [ ] Engage with the post if appropriate
- [ ] Thank user for tagging if positive
"""
            title = f"Instagram: Mention by {username}"
            self.create_task_file(title, content, "medium")

        else:
            # Generic Instagram activity
            content = f"""## Instagram Activity
- **Type:** {item_type}
- **Received:** {datetime.now().isoformat()}

## Details
```json
{json.dumps(data, indent=2)[:500]}
```

## Action Items
- [ ] Review activity
"""
            title = f"Instagram: {item_type.replace('_', ' ').title()}"
            self.create_task_file(title, content, "low")

        self.log_event("instagram_activity", {
            "type": item_type,
            "id": item_id
        })


if __name__ == "__main__":
    import sys

    vault = sys.argv[1] if len(sys.argv) > 1 else "./vault"
    token = os.getenv("INSTAGRAM_ACCESS_TOKEN", "")
    account_id = os.getenv("INSTAGRAM_BUSINESS_ACCOUNT_ID", "")

    if not token or not account_id:
        print("Error: INSTAGRAM_ACCESS_TOKEN and INSTAGRAM_BUSINESS_ACCOUNT_ID must be set")
        sys.exit(1)

    watcher = InstagramWatcher(vault, token, account_id)

    try:
        watcher.run()
    except KeyboardInterrupt:
        watcher.stop()