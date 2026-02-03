"""Compose API endpoints for creating posts and messages."""

import os
import json
from pathlib import Path
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

VAULT_PATH = Path(os.getenv("VAULT_PATH", "./vault"))


class ComposeRequest(BaseModel):
    """Request to compose a post or message."""
    platform: str
    content: str
    image_url: Optional[str] = None
    link_url: Optional[str] = None
    recipient: Optional[str] = None
    subject: Optional[str] = None


class ComposeResponse(BaseModel):
    """Response after composing a post."""
    success: bool
    message: str
    filename: str
    platform: str


def create_post_file(platform: str, content: str, options: dict) -> str:
    """Create a post file in Pending_Approval folder.

    Args:
        platform: Target platform (facebook, instagram, twitter, linkedin, whatsapp, email)
        content: Post content
        options: Additional options (image_url, link_url, recipient, subject)

    Returns:
        Filename of created file
    """
    timestamp = datetime.now()
    date_str = timestamp.strftime("%Y-%m-%d")
    time_str = timestamp.strftime("%H%M%S")

    # Create filename
    platform_prefix = {
        'facebook': 'fb_post',
        'instagram': 'ig_post',
        'twitter': 'tweet',
        'linkedin': 'li_post',
        'whatsapp': 'wa_msg',
        'email': 'email'
    }.get(platform, 'post')

    filename = f"{platform_prefix}_{date_str}_{time_str}.md"

    # Build frontmatter
    frontmatter = {
        'title': f'{platform.title()} {"Message" if platform in ["whatsapp", "email"] else "Post"}',
        'platform': platform,
        'type': 'social_post',
        'status': 'pending_approval',
        'priority': 'medium',
        'created': timestamp.isoformat(),
        'tags': ['social', platform, 'outbound']
    }

    # Add platform-specific fields
    if options.get('recipient'):
        frontmatter['recipient'] = options['recipient']
    if options.get('subject'):
        frontmatter['subject'] = options['subject']
    if options.get('image_url'):
        frontmatter['image_url'] = options['image_url']
    if options.get('link_url'):
        frontmatter['link_url'] = options['link_url']

    # Build content
    body_parts = []

    # Header
    body_parts.append(f"## {platform.title()} {'Message' if platform in ['whatsapp', 'email'] else 'Post'}")
    body_parts.append("")

    # Metadata section
    body_parts.append("### Details")
    body_parts.append(f"- **Platform:** {platform.title()}")
    body_parts.append(f"- **Created:** {timestamp.strftime('%Y-%m-%d %H:%M:%S')}")

    if options.get('recipient'):
        body_parts.append(f"- **Recipient:** {options['recipient']}")
    if options.get('subject'):
        body_parts.append(f"- **Subject:** {options['subject']}")
    if options.get('image_url'):
        body_parts.append(f"- **Image URL:** {options['image_url']}")
    if options.get('link_url'):
        body_parts.append(f"- **Link:** {options['link_url']}")

    body_parts.append("")

    # Content section
    body_parts.append("### Content")
    body_parts.append("")
    body_parts.append(content)
    body_parts.append("")

    # Image preview for Instagram
    if platform == 'instagram' and options.get('image_url'):
        body_parts.append("### Image Preview")
        body_parts.append(f"![Post Image]({options['image_url']})")
        body_parts.append("")

    # Action items
    body_parts.append("### Action Required")
    body_parts.append("- [ ] Review content")
    body_parts.append("- [ ] Approve or reject")
    body_parts.append("")

    # Instructions
    body_parts.append("---")
    body_parts.append("*This post is pending approval. Once approved, it will be published automatically.*")

    # Combine frontmatter and body
    frontmatter_yaml = "---\n"
    for key, value in frontmatter.items():
        if isinstance(value, list):
            frontmatter_yaml += f"{key}:\n"
            for item in value:
                frontmatter_yaml += f"  - {item}\n"
        else:
            frontmatter_yaml += f"{key}: {json.dumps(value) if isinstance(value, str) and ':' in value else value}\n"
    frontmatter_yaml += "---\n\n"

    file_content = frontmatter_yaml + "\n".join(body_parts)

    # Write file
    pending_folder = VAULT_PATH / "Pending_Approval"
    pending_folder.mkdir(parents=True, exist_ok=True)

    file_path = pending_folder / filename
    file_path.write_text(file_content)

    # Log the event
    log_compose_event(platform, filename)

    return filename


def log_compose_event(platform: str, filename: str) -> None:
    """Log a compose event to the daily log file."""
    log_file = VAULT_PATH / "Logs" / f"{datetime.now().strftime('%Y-%m-%d')}.json"

    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "watcher": "Compose",
        "event": "post_created",
        "platform": platform,
        "file": filename
    }

    logs = []
    if log_file.exists():
        try:
            logs = json.loads(log_file.read_text())
        except json.JSONDecodeError:
            logs = []

    logs.append(log_entry)
    log_file.parent.mkdir(parents=True, exist_ok=True)
    log_file.write_text(json.dumps(logs, indent=2))


@router.post("", response_model=ComposeResponse)
async def create_post(request: ComposeRequest):
    """Create a new post or message for approval.

    The post will be saved to Pending_Approval folder and must be approved
    before it can be published.
    """
    valid_platforms = ['facebook', 'instagram', 'twitter', 'linkedin', 'whatsapp', 'email']

    if request.platform not in valid_platforms:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid platform. Must be one of: {', '.join(valid_platforms)}"
        )

    if not request.content.strip():
        raise HTTPException(status_code=400, detail="Content cannot be empty")

    # Validate platform-specific requirements
    if request.platform == 'instagram' and not request.image_url:
        raise HTTPException(status_code=400, detail="Instagram posts require an image URL")

    if request.platform in ['whatsapp', 'email'] and not request.recipient:
        raise HTTPException(status_code=400, detail=f"{request.platform.title()} requires a recipient")

    if request.platform == 'email' and not request.subject:
        raise HTTPException(status_code=400, detail="Email requires a subject")

    # Character limits
    limits = {
        'twitter': 280,
        'instagram': 2200,
        'linkedin': 3000,
        'facebook': 63206
    }

    if request.platform in limits and len(request.content) > limits[request.platform]:
        raise HTTPException(
            status_code=400,
            detail=f"Content exceeds {limits[request.platform]} character limit for {request.platform}"
        )

    try:
        filename = create_post_file(
            platform=request.platform,
            content=request.content,
            options={
                'image_url': request.image_url,
                'link_url': request.link_url,
                'recipient': request.recipient,
                'subject': request.subject
            }
        )

        return ComposeResponse(
            success=True,
            message=f"Post created and pending approval",
            filename=filename,
            platform=request.platform
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/platforms")
async def get_platforms():
    """Get available platforms and their requirements."""
    return {
        "platforms": [
            {
                "id": "facebook",
                "name": "Facebook",
                "max_length": 63206,
                "requires_image": False,
                "requires_recipient": False,
                "supports_link": True
            },
            {
                "id": "instagram",
                "name": "Instagram",
                "max_length": 2200,
                "requires_image": True,
                "requires_recipient": False,
                "supports_link": False
            },
            {
                "id": "twitter",
                "name": "Twitter/X",
                "max_length": 280,
                "requires_image": False,
                "requires_recipient": False,
                "supports_link": False
            },
            {
                "id": "linkedin",
                "name": "LinkedIn",
                "max_length": 3000,
                "requires_image": False,
                "requires_recipient": False,
                "supports_link": True
            },
            {
                "id": "whatsapp",
                "name": "WhatsApp",
                "max_length": None,
                "requires_image": False,
                "requires_recipient": True,
                "supports_link": False
            },
            {
                "id": "email",
                "name": "Email",
                "max_length": None,
                "requires_image": False,
                "requires_recipient": True,
                "requires_subject": True,
                "supports_link": False
            }
        ]
    }
