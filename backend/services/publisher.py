"""Publisher service for executing approved social media posts and messages."""

import os
import json
import httpx
from pathlib import Path
from datetime import datetime
from typing import Optional, Any

import yaml


class Publisher:
    """Publishes approved content to social media platforms."""

    def __init__(self):
        """Initialize publisher with MCP server endpoints."""
        # MCP server configurations
        self.mcp_base = "http://localhost"
        self.vault_path = Path(os.getenv("VAULT_PATH", "./vault"))

    def parse_frontmatter(self, content: str) -> tuple[dict, str]:
        """Parse YAML frontmatter from markdown content."""
        frontmatter = {}
        body = content

        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                try:
                    frontmatter = yaml.safe_load(parts[1]) or {}
                except yaml.YAMLError:
                    frontmatter = {}
                body = parts[2].strip()

        return frontmatter, body

    def extract_content_from_body(self, body: str) -> str:
        """Extract the actual post content from markdown body."""
        # Look for content section
        lines = body.split('\n')
        in_content = False
        content_lines = []

        for line in lines:
            if '### Content' in line:
                in_content = True
                continue
            elif line.startswith('### ') and in_content:
                break
            elif in_content and line.strip():
                content_lines.append(line)

        return '\n'.join(content_lines).strip()

    async def publish_facebook(self, content: str, link_url: Optional[str] = None) -> dict:
        """Publish to Facebook Page."""
        try:
            # Use environment variables for Facebook credentials
            page_access_token = os.getenv("FACEBOOK_PAGE_ACCESS_TOKEN")
            page_id = os.getenv("FACEBOOK_PAGE_ID")

            if not page_access_token or not page_id:
                return {"success": False, "error": "Facebook credentials not configured"}

            async with httpx.AsyncClient() as client:
                params = {
                    "message": content,
                    "access_token": page_access_token
                }
                if link_url:
                    params["link"] = link_url

                response = await client.post(
                    f"https://graph.facebook.com/v18.0/{page_id}/feed",
                    params=params
                )

                if response.status_code == 200:
                    data = response.json()
                    return {"success": True, "post_id": data.get("id"), "platform": "facebook"}
                else:
                    return {"success": False, "error": response.text, "platform": "facebook"}

        except Exception as e:
            return {"success": False, "error": str(e), "platform": "facebook"}

    async def publish_twitter(self, content: str) -> dict:
        """Publish to Twitter/X."""
        try:
            bearer_token = os.getenv("TWITTER_BEARER_TOKEN")
            api_key = os.getenv("TWITTER_API_KEY")
            api_secret = os.getenv("TWITTER_API_SECRET")
            access_token = os.getenv("TWITTER_ACCESS_TOKEN")
            access_secret = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")

            if not all([api_key, api_secret, access_token, access_secret]):
                return {"success": False, "error": "Twitter credentials not configured"}

            # Twitter API v2 requires OAuth 1.0a for posting
            from requests_oauthlib import OAuth1Session

            oauth = OAuth1Session(
                api_key,
                client_secret=api_secret,
                resource_owner_key=access_token,
                resource_owner_secret=access_secret
            )

            response = oauth.post(
                "https://api.twitter.com/2/tweets",
                json={"text": content}
            )

            if response.status_code in [200, 201]:
                data = response.json()
                return {"success": True, "tweet_id": data.get("data", {}).get("id"), "platform": "twitter"}
            else:
                return {"success": False, "error": response.text, "platform": "twitter"}

        except ImportError:
            return {"success": False, "error": "requests-oauthlib not installed", "platform": "twitter"}
        except Exception as e:
            return {"success": False, "error": str(e), "platform": "twitter"}

    async def publish_linkedin(self, content: str, link_url: Optional[str] = None) -> dict:
        """Publish to LinkedIn."""
        try:
            access_token = os.getenv("LINKEDIN_ACCESS_TOKEN")
            person_id = os.getenv("LINKEDIN_PERSON_ID")

            if not access_token:
                return {"success": False, "error": "LinkedIn credentials not configured"}

            async with httpx.AsyncClient() as client:
                # First get the person URN if not provided
                if not person_id:
                    me_response = await client.get(
                        "https://api.linkedin.com/v2/userinfo",
                        headers={"Authorization": f"Bearer {access_token}"}
                    )
                    if me_response.status_code == 200:
                        person_id = me_response.json().get("sub")

                if not person_id:
                    return {"success": False, "error": "Could not get LinkedIn person ID"}

                post_data = {
                    "author": f"urn:li:person:{person_id}",
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
                        "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
                    }
                }

                response = await client.post(
                    "https://api.linkedin.com/v2/ugcPosts",
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        "Content-Type": "application/json",
                        "X-Restli-Protocol-Version": "2.0.0"
                    },
                    json=post_data
                )

                if response.status_code in [200, 201]:
                    return {"success": True, "platform": "linkedin"}
                else:
                    return {"success": False, "error": response.text, "platform": "linkedin"}

        except Exception as e:
            return {"success": False, "error": str(e), "platform": "linkedin"}

    async def publish_instagram(self, content: str, image_url: str) -> dict:
        """Publish to Instagram."""
        try:
            access_token = os.getenv("INSTAGRAM_ACCESS_TOKEN")
            account_id = os.getenv("INSTAGRAM_BUSINESS_ACCOUNT_ID")

            if not access_token or not account_id:
                return {"success": False, "error": "Instagram credentials not configured"}

            async with httpx.AsyncClient() as client:
                # Step 1: Create media container
                container_response = await client.post(
                    f"https://graph.instagram.com/{account_id}/media",
                    params={
                        "image_url": image_url,
                        "caption": content,
                        "access_token": access_token
                    }
                )

                if container_response.status_code != 200:
                    return {"success": False, "error": container_response.text, "platform": "instagram"}

                container_id = container_response.json().get("id")

                # Step 2: Publish the container
                publish_response = await client.post(
                    f"https://graph.instagram.com/{account_id}/media_publish",
                    params={
                        "creation_id": container_id,
                        "access_token": access_token
                    }
                )

                if publish_response.status_code == 200:
                    return {"success": True, "media_id": publish_response.json().get("id"), "platform": "instagram"}
                else:
                    return {"success": False, "error": publish_response.text, "platform": "instagram"}

        except Exception as e:
            return {"success": False, "error": str(e), "platform": "instagram"}

    async def send_whatsapp(self, content: str, recipient: str) -> dict:
        """Send WhatsApp message."""
        try:
            # WhatsApp Business API configuration
            phone_number_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
            access_token = os.getenv("WHATSAPP_ACCESS_TOKEN")

            if not phone_number_id or not access_token:
                return {"success": False, "error": "WhatsApp credentials not configured"}

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"https://graph.facebook.com/v18.0/{phone_number_id}/messages",
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "messaging_product": "whatsapp",
                        "to": recipient.replace("+", ""),
                        "type": "text",
                        "text": {"body": content}
                    }
                )

                if response.status_code == 200:
                    return {"success": True, "platform": "whatsapp"}
                else:
                    return {"success": False, "error": response.text, "platform": "whatsapp"}

        except Exception as e:
            return {"success": False, "error": str(e), "platform": "whatsapp"}

    async def send_email(self, content: str, recipient: str, subject: str) -> dict:
        """Send email via Gmail."""
        try:
            # This would use the Gmail API
            # For now, return a placeholder
            return {"success": False, "error": "Email sending requires Gmail OAuth setup", "platform": "email"}

        except Exception as e:
            return {"success": False, "error": str(e), "platform": "email"}

    async def publish(self, file_path: Path) -> dict:
        """Publish content from an approved file.

        Args:
            file_path: Path to the approved markdown file

        Returns:
            Result dictionary with success status and details
        """
        if not file_path.exists():
            return {"success": False, "error": "File not found"}

        content = file_path.read_text()
        frontmatter, body = self.parse_frontmatter(content)

        platform = frontmatter.get("platform", "").lower()
        post_content = self.extract_content_from_body(body)

        if not post_content:
            post_content = frontmatter.get("content", "")

        if not platform:
            return {"success": False, "error": "No platform specified in file"}

        if not post_content:
            return {"success": False, "error": "No content found in file"}

        # Route to appropriate publisher
        if platform == "facebook":
            link_url = frontmatter.get("link_url")
            return await self.publish_facebook(post_content, link_url)

        elif platform == "twitter":
            return await self.publish_twitter(post_content)

        elif platform == "linkedin":
            link_url = frontmatter.get("link_url")
            return await self.publish_linkedin(post_content, link_url)

        elif platform == "instagram":
            image_url = frontmatter.get("image_url")
            if not image_url:
                return {"success": False, "error": "Instagram requires image_url"}
            return await self.publish_instagram(post_content, image_url)

        elif platform == "whatsapp":
            recipient = frontmatter.get("recipient")
            if not recipient:
                return {"success": False, "error": "WhatsApp requires recipient"}
            return await self.send_whatsapp(post_content, recipient)

        elif platform == "email":
            recipient = frontmatter.get("recipient")
            subject = frontmatter.get("subject")
            if not recipient or not subject:
                return {"success": False, "error": "Email requires recipient and subject"}
            return await self.send_email(post_content, recipient, subject)

        else:
            return {"success": False, "error": f"Unknown platform: {platform}"}

    def log_publish_result(self, filename: str, result: dict) -> None:
        """Log publishing result."""
        log_file = self.vault_path / "Logs" / f"{datetime.now().strftime('%Y-%m-%d')}.json"

        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "watcher": "Publisher",
            "event": "publish_success" if result.get("success") else "publish_failed",
            "file": filename,
            "platform": result.get("platform", "unknown"),
            "error": result.get("error") if not result.get("success") else None
        }

        logs = []
        if log_file.exists():
            try:
                logs = json.loads(log_file.read_text())
            except json.JSONDecodeError:
                logs = []

        logs.append(log_entry)
        log_file.write_text(json.dumps(logs, indent=2))


# Global publisher instance
_publisher: Optional[Publisher] = None


def get_publisher() -> Publisher:
    """Get or create the global publisher instance."""
    global _publisher
    if _publisher is None:
        _publisher = Publisher()
    return _publisher
