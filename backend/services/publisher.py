"""Publisher service for executing approved social media posts and messages.

This service publishes directly to platform APIs with proper authentication.
"""

import os
import json
import httpx
from pathlib import Path
from datetime import datetime
from typing import Optional

import yaml


class Publisher:
    """Publishes approved content to social media platforms via direct API calls.

    Each platform uses its configured credentials and implements proper API handling.
    """

    def __init__(self):
        """Initialize publisher with API credentials."""
        self.vault_path = Path(os.getenv("VAULT_PATH", "./vault"))
        self.dry_run = os.getenv("DRY_RUN", "true").lower() == "true"

        # Load credentials
        self.facebook_token = os.getenv("FACEBOOK_PAGE_ACCESS_TOKEN", "")
        self.facebook_page_id = os.getenv("FACEBOOK_PAGE_ID", "")
        self.instagram_account_id = os.getenv("INSTAGRAM_BUSINESS_ACCOUNT_ID", "")

        self.twitter_api_key = os.getenv("TWITTER_API_KEY", "")
        self.twitter_api_secret = os.getenv("TWITTER_API_SECRET", "")
        self.twitter_access_token = os.getenv("TWITTER_ACCESS_TOKEN", "")
        self.twitter_access_secret = os.getenv("TWITTER_ACCESS_TOKEN_SECRET", "")
        self.twitter_bearer_token = os.getenv("TWITTER_BEARER_TOKEN", "")

        self.linkedin_token = os.getenv("LINKEDIN_ACCESS_TOKEN", "")

        # Gmail OAuth - would need token file
        self.gmail_token_path = os.getenv("GMAIL_CREDENTIALS_PATH", "./credentials/gmail_token.json")

        # WhatsApp session path
        self.whatsapp_session_path = os.getenv("WHATSAPP_SESSION_PATH", "./credentials/whatsapp_session")

    def log_action(self, platform: str, action: str, details: dict) -> None:
        """Log a publisher action."""
        log_file = self.vault_path / "Logs" / f"{datetime.now().strftime('%Y-%m-%d')}.json"

        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "watcher": f"Publisher_{platform}",
            "event": action,
            **details
        }

        logs = []
        if log_file.exists():
            try:
                logs = json.loads(log_file.read_text())
            except json.JSONDecodeError:
                logs = []

        logs.append(log_entry)
        log_file.write_text(json.dumps(logs, indent=2))

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
        """Extract actual post content from markdown body.

        Supports multiple content section formats:
        - ### Content
        - ### Post Content
        - ### Message Content
        - ## Caption (Instagram posts)
        """
        lines = body.split('\n')
        in_content = False
        content_lines = []

        for line in lines:
            # Check for content markers (both ## and ### levels)
            content_markers = ['### Content', '### Post Content', '### Message Content', '## Caption']
            if any(marker in line for marker in content_markers):
                in_content = True
                continue
            # Stop at next heading of same or higher level
            elif in_content and (line.startswith('### ') or line.startswith('## ')):
                break
            elif in_content and line.strip():
                content_lines.append(line)

        return '\n'.join(content_lines).strip()

    async def publish_facebook(self, content: str, link_url: Optional[str] = None) -> dict:
        """Publish to Facebook Page via Graph API."""
        if self.dry_run:
            return {"success": True, "dry_run": True, "platform": "facebook"}

        if not self.facebook_token or not self.facebook_page_id:
            return {"success": False, "error": "Facebook credentials not configured", "platform": "facebook"}

        try:
            url = f"https://graph.facebook.com/v18.0/{self.facebook_page_id}/feed"
            post_data = {
                "message": content,
                "access_token": self.facebook_token
            }
            if link_url:
                post_data["link"] = link_url

            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=post_data)

                if response.status_code in [200, 201]:
                    data = response.json()
                    post_id = data.get("id", "")
                    self.log_action("facebook", "post_success", {"post_id": post_id})
                    return {"success": True, "post_id": post_id, "platform": "facebook"}
                else:
                    error_data = response.json()
                    error_msg = error_data.get("error", {}).get("message", response.text)
                    self.log_action("facebook", "post_failed", {"error": error_msg})
                    return {"success": False, "error": error_msg, "platform": "facebook"}

        except Exception as e:
            self.log_action("facebook", "post_error", {"error": str(e)})
            return {"success": False, "error": str(e), "platform": "facebook"}

    async def publish_twitter(self, content: str) -> dict:
        """Publish to Twitter/X via API using OAuth 1.0a."""
        if self.dry_run:
            return {"success": True, "dry_run": True, "platform": "twitter"}

        # Check for OAuth 1.0a credentials (required for posting)
        if not all([self.twitter_api_key, self.twitter_api_secret, self.twitter_access_token, self.twitter_access_secret]):
            return {"success": False, "error": "Twitter OAuth 1.0a credentials not configured", "platform": "twitter"}

        try:
            from requests_oauthlib import OAuth1Session

            # Create OAuth1 session
            twitter = OAuth1Session(
                client_key=self.twitter_api_key,
                client_secret=self.twitter_api_secret,
                resource_owner_key=self.twitter_access_token,
                resource_owner_secret=self.twitter_access_secret
            )

            url = "https://api.twitter.com/2/tweets"
            post_data = {"text": content}

            # Post tweet
            response = twitter.post(url, json=post_data)

            if response.status_code in [200, 201]:
                data = response.json()
                tweet_id = data.get("data", {}).get("id")
                self.log_action("twitter", "post_success", {"tweet_id": tweet_id})
                return {"success": True, "tweet_id": tweet_id, "platform": "twitter"}
            else:
                error_msg = response.text
                self.log_action("twitter", "post_failed", {"error": error_msg})
                return {"success": False, "error": error_msg, "platform": "twitter"}

        except Exception as e:
            self.log_action("twitter", "post_error", {"error": str(e)})
            return {"success": False, "error": str(e), "platform": "twitter"}

    async def _get_linkedin_user_id(self) -> Optional[str]:
        """Get current user's LinkedIn member ID."""
        if not self.linkedin_token:
            return None

        try:
            url = "https://api.linkedin.com/v2/userinfo"
            headers = {
                "Authorization": f"Bearer {self.linkedin_token}",
                "X-Restli-Protocol-Version": "2.0.0"
            }

            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers)

                if response.status_code == 200:
                    data = response.json()
                    return data.get("sub", "")
                else:
                    self.log_action("linkedin", "user_id_failed", {"status": response.status_code})
                    return None

        except Exception as e:
            self.log_action("linkedin", "user_id_error", {"error": str(e)})
            return None

    async def publish_linkedin(self, content: str, link_url: Optional[str] = None) -> dict:
        """Publish to LinkedIn via API."""
        if self.dry_run:
            return {"success": True, "dry_run": True, "platform": "linkedin"}

        if not self.linkedin_token:
            return {"success": False, "error": "LinkedIn credentials not configured", "platform": "linkedin"}

        try:
            # Get user's member URN first
            user_id = await self._get_linkedin_user_id()
            if not user_id:
                return {"success": False, "error": "Could not retrieve LinkedIn user ID", "platform": "linkedin"}

            author_urn = f"urn:li:person:{user_id}"

            url = "https://api.linkedin.com/v2/ugcPosts"
            headers = {
                "Authorization": f"Bearer {self.linkedin_token}",
                "Content-Type": "application/json",
                "X-Restli-Protocol-Version": "2.0.0",
                "LinkedIn-Version": "202401"
            }

            # Build post data with required visibility field
            post_data = {
                "author": author_urn,
                "lifecycleState": "PUBLISHED",
                "visibility": {
                    "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
                },
                "specificContent": {
                    "com.linkedin.ugc.ShareContent": {
                        "shareCommentary": {"text": content},
                        "shareMediaCategory": "NONE"
                    }
                }
            }

            # Add link/media if provided
            if link_url:
                post_data["specificContent"]["com.linkedin.ugc.ShareContent"]["media"] = [
                    {
                        "status": "READY",
                        "description": {"text": content},
                        "attributes": [],
                        "media": f"urn:li:digitalmediaAsset:{link_url}"
                    }
                ]
                post_data["specificContent"]["com.linkedin.ugc.ShareContent"]["shareMediaCategory"] = "ARTICLE"

            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=headers, json=post_data)

                if response.status_code == 201:
                    post_id = response.headers.get("x-restli-id", "")
                    self.log_action("linkedin", "post_success", {"post_id": post_id})
                    return {"success": True, "post_id": post_id, "platform": "linkedin"}
                else:
                    error_msg = response.text
                    self.log_action("linkedin", "post_failed", {"error": error_msg})
                    return {"success": False, "error": error_msg, "platform": "linkedin"}

        except Exception as e:
            self.log_action("linkedin", "post_error", {"error": str(e)})
            return {"success": False, "error": str(e), "platform": "linkedin"}

    async def publish_instagram(self, content: str, image_url: str) -> dict:
        """Publish to Instagram via Facebook Graph API."""
        if self.dry_run:
            return {"success": True, "dry_run": True, "platform": "instagram"}

        if not self.facebook_token or not self.instagram_account_id:
            return {"success": False, "error": "Instagram credentials not configured", "platform": "instagram"}

        try:
            # Create media container
            container_url = f"https://graph.facebook.com/v18.0/{self.instagram_account_id}/media"
            container_data = {
                "image_url": image_url,
                "caption": content,
                "access_token": self.facebook_token
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(container_url, json=container_data)

                if response.status_code in [200, 201]:
                    data = response.json()
                    container_id = data.get("id")

                    # Publish container
                    publish_url = f"https://graph.facebook.com/v18.0/{self.instagram_account_id}/media_publish"
                    publish_data = {
                        "creation_id": container_id,
                        "access_token": self.facebook_token
                    }
                    publish_response = await client.post(publish_url, json=publish_data)

                    if publish_response.status_code in [200, 201]:
                        self.log_action("instagram", "post_success", {"media_id": container_id})
                        return {"success": True, "media_id": container_id, "platform": "instagram"}
                    else:
                        error_msg = publish_response.text
                        self.log_action("instagram", "publish_failed", {"error": error_msg})
                        return {"success": False, "error": error_msg, "platform": "instagram"}
                else:
                    error_msg = response.text
                    self.log_action("instagram", "container_failed", {"error": error_msg})
                    return {"success": False, "error": error_msg, "platform": "instagram"}

        except Exception as e:
            self.log_action("instagram", "post_error", {"error": str(e)})
            return {"success": False, "error": str(e), "platform": "instagram"}

    async def send_whatsapp(self, content: str, recipient: str) -> dict:
        """Send WhatsApp message via Meta Business API."""
        if self.dry_run:
            self.log_action("whatsapp", "dry_run", {"recipient": recipient})
            return {"success": True, "dry_run": True, "platform": "whatsapp"}

        # Get WhatsApp credentials from environment
        phone_number_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
        access_token = os.getenv("WHATSAPP_ACCESS_TOKEN")

        if not phone_number_id or not access_token:
            self.log_action("whatsapp", "credentials_missing", {})
            return {
                "success": False,
                "error": "WhatsApp credentials not configured (WHATSAPP_PHONE_NUMBER_ID, WHATSAPP_ACCESS_TOKEN)",
                "platform": "whatsapp"
            }

        try:
            # Clean phone number
            recipient_clean = recipient.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
            if not recipient_clean.startswith("+"):
                recipient_clean = "+" + recipient_clean

            # Send via Meta Graph API
            url = f"https://graph.facebook.com/v18.0/{phone_number_id}/messages"

            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }

            payload = {
                "messaging_product": "whatsapp",
                "to": recipient_clean,
                "type": "text",
                "text": {"body": content}
            }

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=payload, headers=headers)

                if response.status_code == 200:
                    result = response.json()
                    msg_id = result.get("messages", [{}])[0].get("id", "")
                    self.log_action("whatsapp", "send_success", {"recipient": recipient_clean, "message_id": msg_id})
                    return {"success": True, "message_id": msg_id, "platform": "whatsapp"}
                else:
                    error_detail = response.text
                    self.log_action("whatsapp", "send_failed", {"recipient": recipient_clean, "error": error_detail})
                    return {"success": False, "error": error_detail, "platform": "whatsapp"}

        except Exception as e:
            self.log_action("whatsapp", "send_error", {"recipient": recipient, "error": str(e)})
            return {"success": False, "error": str(e), "platform": "whatsapp"}

    async def send_email(self, content: str, recipient: str, subject: str) -> dict:
        """Send email via Gmail API."""
        if self.dry_run:
            return {"success": True, "dry_run": True, "platform": "email"}

        # Check if token exists
        token_path = Path(self.gmail_token_path)
        if not token_path.exists():
            return {"success": False, "error": "Gmail token not found. Run OAuth setup first.", "platform": "email"}

        try:
            # Build Gmail API service
            from google.oauth2.credentials import Credentials
            from google.auth.transport.requests import Request
            from googleapiclient.discovery import build
            import base64
            from email.mime.text import MIMEText

            creds = Credentials.from_authorized_user_file(str(token_path),
                scopes=['https://www.googleapis.com/auth/gmail.send'])
            service = build('gmail', 'v1', credentials=creds)

            # Create message
            message = MIMEText(content)
            message['to'] = recipient
            message['subject'] = subject

            # Send message
            raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
            result = service.users().messages().send(userId='me', body={'raw': raw}).execute()

            self.log_action("email", "send_success", {"recipient": recipient})
            return {"success": True, "platform": "email"}

        except ImportError:
            return {"success": False, "error": "Gmail libraries not installed", "platform": "email"}
        except Exception as e:
            self.log_action("email", "send_error", {"error": str(e)})
            return {"success": False, "error": str(e), "platform": "email"}

    async def publish(self, file_path: Path) -> dict:
        """Publish content from an approved file.

        Args:
            file_path: Path to approved markdown file

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

    def log_auto_action(
        self,
        action_type: str,
        channel: str,
        recipient: str,
        success: bool,
        details: dict = None
    ) -> None:
        """Log auto-approved action to audit trail.

        Used for tracking messages sent without manual approval.

        Args:
            action_type: Type of auto-action (e.g., "appointment_confirmation", "appointment_reminder")
            channel: Communication channel (whatsapp, email)
            recipient: Recipient contact info
            success: Whether the action succeeded
            details: Optional additional details (appointment_id, hours_before, etc.)
        """
        log_file = self.vault_path / "Logs" / f"{datetime.now().strftime('%Y-%m-%d')}.json"

        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "watcher": f"Publisher_{channel}",
            "event": "auto_action",
            "action_type": action_type,
            "channel": channel,
            "recipient": recipient,
            "success": success,
            "auto_approved": True,
        }

        if details:
            log_entry.update(details)

        logs = []
        if log_file.exists():
            try:
                logs = json.loads(log_file.read_text())
            except json.JSONDecodeError:
                logs = []

        logs.append(log_entry)
        log_file.parent.mkdir(parents=True, exist_ok=True)
        log_file.write_text(json.dumps(logs, indent=2))

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
_publisher = None


def get_publisher() -> Publisher:
    """Get or create global publisher instance."""
    global _publisher
    if _publisher is None:
        _publisher = Publisher()
    return _publisher
