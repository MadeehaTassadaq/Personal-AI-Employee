"""Facebook notifications and activity watcher using Graph API."""

import os
import json
from pathlib import Path
from datetime import datetime
from typing import Any, Optional

import httpx

from .base_watcher import BaseWatcher


class FacebookWatcher(BaseWatcher):
    """Watches Facebook for notifications, messages, and page activities."""

    API_BASE = "https://graph.facebook.com/v18.0"

    def __init__(
        self,
        vault_path: str,
        page_access_token: str,
        page_id: str,
        check_interval: int = 300,  # 5 minutes default
    ):
        """Initialize Facebook watcher.

        Args:
            vault_path: Path to Obsidian vault
            page_access_token: Facebook Page access token
            page_id: Facebook Page ID
            check_interval: Seconds between checks
        """
        super().__init__(vault_path, check_interval)

        self.page_access_token = page_access_token
        self.page_id = page_id
        self.headers = {
            "Authorization": f"Bearer {page_access_token}",
        }
        self.seen_activities: set[str] = set()
        self._load_seen_activities()

    def _load_seen_activities(self) -> None:
        """Load previously seen activity IDs."""
        seen_file = self.vault_path / ".facebook_seen.json"
        if seen_file.exists():
            try:
                self.seen_activities = set(json.loads(seen_file.read_text()))
            except json.JSONDecodeError:
                self.seen_activities = set()

    def _save_seen_activities(self) -> None:
        """Save seen activity IDs."""
        seen_file = self.vault_path / ".facebook_seen.json"
        recent = list(self.seen_activities)[-500:]
        seen_file.write_text(json.dumps(recent))

    def check_for_updates(self) -> list[dict]:
        """Check Facebook for new activities.

        Returns:
            List of new activities
        """
        new_items = []

        try:
            with httpx.Client() as client:
                # Check for new posts on the page
                posts_response = client.get(
                    f"{self.API_BASE}/{self.page_id}/posts",
                    params={
                        "fields": "id,message,created_time,from,comments.summary(total_count),likes.summary(total_count)",
                        "limit": 10,
                        "access_token": self.page_access_token
                    }
                )

                if posts_response.status_code == 200:
                    posts_data = posts_response.json()
                    posts = posts_data.get("data", [])

                    for post in posts:
                        post_id = post.get("id", "")
                        if post_id and post_id not in self.seen_activities:
                            new_items.append({
                                "type": "page_post",
                                "id": post_id,
                                "data": post
                            })
                            self.seen_activities.add(post_id)

                # Check for new comments on page posts
                comments_response = client.get(
                    f"{self.API_BASE}/{self.page_id}/feed",
                    params={
                        "fields": "id,message,created_time,from,parent_id,comments.summary(total_count),likes.summary(total_count)",
                        "limit": 20,
                        "access_token": self.page_access_token
                    }
                )

                if comments_response.status_code == 200:
                    comments_data = comments_response.json()
                    posts_with_comments = comments_data.get("data", [])

                    for post in posts_with_comments:
                        post_id = post.get("id", "")
                        comments = post.get("comments", {}).get("data", [])

                        for comment in comments:
                            comment_id = comment.get("id", "")
                            if comment_id and comment_id not in self.seen_activities:
                                new_items.append({
                                    "type": "comment",
                                    "id": comment_id,
                                    "parent_post_id": post_id,
                                    "data": comment
                                })
                                self.seen_activities.add(comment_id)

                # Check for new messages (if page has messaging enabled)
                try:
                    messages_response = client.get(
                        f"{self.API_BASE}/{self.page_id}/conversations",
                        params={
                            "fields": "id,updated_time,participants,messages.fields(message,created_time)",
                            "limit": 10,
                            "access_token": self.page_access_token
                        }
                    )

                    if messages_response.status_code == 200:
                        messages_data = messages_response.json()
                        conversations = messages_data.get("data", [])

                        for convo in conversations:
                            convo_id = convo.get("id", "")
                            if convo_id and convo_id not in self.seen_activities:
                                new_items.append({
                                    "type": "message_conversation",
                                    "id": convo_id,
                                    "data": convo
                                })
                                self.seen_activities.add(convo_id)
                except Exception:
                    # Messaging might not be enabled for this page
                    pass

        except httpx.RequestError as e:
            self.logger.error(f"Facebook API error: {e}")
        except Exception as e:
            self.logger.error(f"Error checking Facebook: {e}")

        if new_items:
            self._save_seen_activities()

        return new_items

    def on_new_item(self, item: dict) -> None:
        """Handle a new Facebook activity.

        Args:
            item: Activity data
        """
        item_type = item.get("type", "unknown")
        item_id = item.get("id", "")
        data = item.get("data", {})

        if item_type == "page_post":
            # New post on the page
            message = data.get("message", "")[:100] + "..." if len(data.get("message", "")) > 100 else data.get("message", "")
            author = data.get("from", {}).get("name", "Unknown")

            content = f"""## Facebook Page Post
- **Author:** {author}
- **Posted:** {data.get('created_time', datetime.now().isoformat())}
- **Post ID:** {item_id}

## Message Preview
{message}

## Engagement
- **Likes:** {data.get('likes', {}).get('summary', {}).get('total_count', 0)}
- **Comments:** {data.get('comments', {}).get('summary', {}).get('total_count', 0)}

## Action Items
- [ ] Review post content
- [ ] Engage with comments if needed
- [ ] Monitor performance
"""
            title = f"Facebook: New Post by {author}"
            self.create_task_file(title, content, "medium")

        elif item_type == "comment":
            # New comment on a post
            comment_text = data.get("message", "")[:100] + "..." if len(data.get("message", "")) > 100 else data.get("message", "")
            author = data.get("from", {}).get("name", "Unknown")
            parent_post_id = item.get("parent_post_id", "")

            content = f"""## Facebook Comment
- **Author:** {author}
- **Posted:** {data.get('created_time', datetime.now().isoformat())}
- **Comment ID:** {item_id}
- **On Post:** {parent_post_id}

## Comment
{comment_text}

## Action Items
- [ ] Review comment content
- [ ] Respond appropriately
- [ ] Moderate if necessary
"""
            title = f"Facebook: Comment by {author}"
            self.create_task_file(title, content, "high")

        elif item_type == "message_conversation":
            # New message conversation
            participants = [p.get("name", "Unknown") for p in data.get("participants", {}).get("data", [])]
            participant_names = ", ".join(participants)

            messages = data.get("messages", {}).get("data", [])
            latest_msg = messages[0] if messages else {}
            preview = latest_msg.get("message", "")[:100] + "..." if len(latest_msg.get("message", "")) > 100 else latest_msg.get("message", "")

            content = f"""## Facebook Message Conversation
- **Participants:** {participant_names}
- **Last Updated:** {data.get('updated_time', datetime.now().isoformat())}
- **Conversation ID:** {item_id}

## Latest Message
{preview}

## Action Items
- [ ] Check full conversation
- [ ] Respond if needed
- [ ] Categorize inquiry
"""
            title = f"Facebook: New Message from {participant_names}"
            self.create_task_file(title, content, "high")

        else:
            # Generic Facebook activity
            content = f"""## Facebook Activity
- **Type:** {item_type}
- **Received:** {datetime.now().isoformat()}

## Details
```json
{json.dumps(data, indent=2)[:500]}
```

## Action Items
- [ ] Review activity
"""
            title = f"Facebook: {item_type.replace('_', ' ').title()}"
            self.create_task_file(title, content, "low")

        self.log_event("facebook_activity", {
            "type": item_type,
            "id": item_id
        })


if __name__ == "__main__":
    import sys

    vault = sys.argv[1] if len(sys.argv) > 1 else "./vault"
    token = os.getenv("FACEBOOK_PAGE_ACCESS_TOKEN", "")
    page_id = os.getenv("FACEBOOK_PAGE_ID", "")

    if not token or not page_id:
        print("Error: FACEBOOK_PAGE_ACCESS_TOKEN and FACEBOOK_PAGE_ID must be set")
        sys.exit(1)

    watcher = FacebookWatcher(vault, token, page_id)

    try:
        watcher.run()
    except KeyboardInterrupt:
        watcher.stop()