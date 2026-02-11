"""AI Reasoning Service for intelligent content generation.

Provides centralized AI-powered content generation for Ralph Wiggum handlers,
with fallback strategies when Claude API is unavailable.
"""

import json
import logging
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

import httpx
import yaml

from .error_recovery import (
    ErrorRecoveryService,
    RetryConfig,
    get_error_recovery,
)

logger = logging.getLogger(__name__)


@dataclass
class TaskContext:
    """Structured context extracted from a task file."""

    task_id: str
    task_type: str  # email, whatsapp, linkedin, instagram, facebook, etc.
    title: str
    recipient: Optional[str] = None
    subject: Optional[str] = None
    platform: str = "unknown"
    priority: str = "normal"
    raw_content: str = ""
    description: str = ""
    context_hints: list[str] = field(default_factory=list)
    company_context: dict = field(default_factory=dict)


@dataclass
class GeneratedContent:
    """Result of AI content generation."""

    content: str  # Main generated content
    subject: Optional[str] = None  # For emails
    hashtags: list[str] = field(default_factory=list)  # For social posts
    confidence: float = 0.0  # 0-1 score
    fallback_used: bool = False  # True if Claude unavailable


class AIReasoningService:
    """Centralized service for AI-powered content generation.

    Handles context extraction from vault tasks and generates
    intelligent, pre-filled content for approval workflows.
    """

    # Claude API configuration
    CLAUDE_API_URL = "https://api.anthropic.com/v1/messages"
    CLAUDE_MODEL = "claude-3-5-sonnet-20241022"
    CLAUDE_API_VERSION = "2023-06-01"
    MAX_TOKENS = 1024
    API_TIMEOUT = 30.0

    # Platform-specific guidelines
    PLATFORM_GUIDELINES = {
        "email": {
            "tone": "professional and courteous",
            "length": "concise but complete",
            "format": "greeting, body, sign-off",
        },
        "whatsapp": {
            "tone": "friendly but professional",
            "length": "under 500 characters",
            "format": "brief message, no formal greeting needed",
        },
        "linkedin": {
            "tone": "professional and engaging",
            "length": "150-300 words optimal",
            "format": "hook, value, call-to-action",
            "hashtags": "3-5 relevant hashtags",
        },
        "instagram": {
            "tone": "engaging and visual-focused",
            "length": "under 2200 characters",
            "format": "attention-grabbing first line, story, CTA",
            "hashtags": "up to 30 relevant hashtags",
        },
        "facebook": {
            "tone": "conversational and community-focused",
            "length": "40-80 characters for best engagement",
            "format": "question or statement that invites engagement",
        },
    }

    def __init__(self, vault_path: Path):
        """Initialize the AI Reasoning Service.

        Args:
            vault_path: Path to the vault directory
        """
        self.vault_path = Path(vault_path)
        self._error_recovery = get_error_recovery()
        self._error_recovery.register_service("claude_api")
        self._company_context: Optional[dict] = None

    def parse_task_context(self, task_content: str, task_path: Path) -> TaskContext:
        """Extract structured context from a task file.

        Args:
            task_content: Raw markdown content of the task file
            task_path: Path to the task file

        Returns:
            TaskContext with extracted information
        """
        frontmatter, body = self._parse_frontmatter(task_content)

        # Extract task ID from filename
        task_id = task_path.stem

        # Determine task type from frontmatter or content
        task_type = frontmatter.get("type", "task")
        platform = frontmatter.get("platform", self._detect_platform(task_content))

        # Extract title
        title = frontmatter.get("title", "")
        if not title:
            # Try to find first heading
            for line in body.split("\n"):
                if line.startswith("# "):
                    title = line[2:].strip()
                    break
            if not title:
                title = task_id.replace("-", " ").replace("_", " ").title()

        # Extract recipient if available
        recipient = frontmatter.get("recipient") or frontmatter.get("to")
        if not recipient:
            recipient = self._extract_recipient_from_content(body)

        # Extract subject if available
        subject = frontmatter.get("subject")
        if not subject:
            subject = self._extract_subject_from_content(body, title)

        # Extract description (body without metadata sections)
        description = self._extract_description(body)

        # Extract context hints from content
        context_hints = self._extract_context_hints(body, frontmatter)

        # Load company context
        company_context = self._load_company_context()

        return TaskContext(
            task_id=task_id,
            task_type=task_type,
            title=title,
            recipient=recipient,
            subject=subject,
            platform=platform,
            priority=frontmatter.get("priority", "normal"),
            raw_content=task_content,
            description=description,
            context_hints=context_hints,
            company_context=company_context,
        )

    def _parse_frontmatter(self, content: str) -> tuple[dict, str]:
        """Parse YAML frontmatter from markdown content.

        Args:
            content: Markdown content with optional YAML frontmatter

        Returns:
            Tuple of (frontmatter_dict, body_content)
        """
        if not content.startswith("---"):
            return {}, content

        parts = content.split("---", 2)
        if len(parts) < 3:
            return {}, content

        try:
            frontmatter = yaml.safe_load(parts[1]) or {}
        except yaml.YAMLError:
            frontmatter = {}

        body = parts[2].strip()
        return frontmatter, body

    def _detect_platform(self, content: str) -> str:
        """Detect platform from content keywords."""
        content_lower = content.lower()

        platform_keywords = {
            "email": ["email", "send email", "draft email", "mail"],
            "whatsapp": ["whatsapp", "message", "text message"],
            "linkedin": ["linkedin", "professional network"],
            "instagram": ["instagram", "ig post", "insta"],
            "facebook": ["facebook", "fb post"],
            "twitter": ["twitter", "tweet", "x post"],
        }

        for platform, keywords in platform_keywords.items():
            if any(kw in content_lower for kw in keywords):
                return platform

        return "unknown"

    def _extract_recipient_from_content(self, content: str) -> Optional[str]:
        """Extract recipient email or phone from content."""
        # Email pattern
        email_match = re.search(r"[\w.+-]+@[\w-]+\.[\w.-]+", content)
        if email_match:
            return email_match.group()

        # Phone pattern (international format)
        phone_match = re.search(r"\+\d{1,3}[\d\s-]{8,15}", content)
        if phone_match:
            return phone_match.group().replace(" ", "").replace("-", "")

        return None

    def _extract_subject_from_content(
        self, content: str, fallback_title: str
    ) -> Optional[str]:
        """Extract email subject from content."""
        # Look for explicit subject line
        subject_match = re.search(
            r"(?:subject|re|regarding):\s*(.+?)(?:\n|$)", content, re.IGNORECASE
        )
        if subject_match:
            return subject_match.group(1).strip()

        # Use title as fallback
        return fallback_title if fallback_title else None

    def _extract_description(self, body: str) -> str:
        """Extract main description from body content."""
        lines = []
        in_metadata_section = False

        for line in body.split("\n"):
            # Skip metadata sections
            if line.startswith("## Action") or line.startswith("## Notes"):
                in_metadata_section = True
                continue
            if line.startswith("## ") and in_metadata_section:
                in_metadata_section = False

            if not in_metadata_section and line.strip():
                # Skip checkbox items that are likely action items
                if not line.strip().startswith("- [ ]"):
                    lines.append(line)

        return "\n".join(lines).strip()

    def _extract_context_hints(self, body: str, frontmatter: dict) -> list[str]:
        """Extract context hints from content."""
        hints = []

        # Add priority as hint
        priority = frontmatter.get("priority")
        if priority and priority != "normal":
            hints.append(f"Priority: {priority}")

        # Add assignee as hint
        assignee = frontmatter.get("assignee")
        if assignee:
            hints.append(f"Assignee: {assignee}")

        # Extract any tags
        tags = frontmatter.get("tags", [])
        if tags:
            hints.extend([f"Tag: {tag}" for tag in tags])

        # Look for key phrases in body
        key_phrases = [
            "urgent",
            "deadline",
            "important",
            "follow up",
            "reminder",
            "meeting",
            "schedule",
            "appointment",
        ]
        body_lower = body.lower()
        for phrase in key_phrases:
            if phrase in body_lower:
                hints.append(f"Contains: {phrase}")

        return hints

    def _load_company_context(self) -> dict:
        """Load company context from Company_Handbook.md."""
        if self._company_context is not None:
            return self._company_context

        handbook_path = self.vault_path / "Company_Handbook.md"
        if not handbook_path.exists():
            self._company_context = {}
            return self._company_context

        try:
            content = handbook_path.read_text()

            # Extract key policies
            context = {
                "has_handbook": True,
                "email_policy": self._extract_section(content, "Email Policy"),
                "whatsapp_policy": self._extract_section(content, "WhatsApp Policy"),
                "linkedin_policy": self._extract_section(content, "LinkedIn Policy"),
                "communication_tone": "professional",
            }

            self._company_context = context
            return context

        except Exception as e:
            logger.warning(f"Failed to load company handbook: {e}")
            self._company_context = {}
            return self._company_context

    def _extract_section(self, content: str, section_name: str) -> str:
        """Extract a section from markdown content."""
        pattern = rf"###\s*{re.escape(section_name)}\s*\n(.*?)(?=\n###|\n##|\Z)"
        match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return ""

    async def generate_email_content(
        self, context: TaskContext
    ) -> GeneratedContent:
        """Generate email content using AI.

        Args:
            context: Extracted task context

        Returns:
            GeneratedContent with email body and subject
        """
        system_prompt = """You are an AI assistant drafting professional business emails.
Your task is to generate a well-structured, professional email based on the given context.

Guidelines:
- Use a professional but warm tone
- Be concise but complete
- Include proper greeting and sign-off
- Focus on the main purpose of the communication

Respond ONLY with valid JSON in this exact format:
{
    "subject": "Email subject line",
    "body": "Full email body with greeting and sign-off",
    "confidence": 0.85
}

The confidence score should reflect how well you understood the request (0.0-1.0).
"""

        user_prompt = f"""Generate an email based on this context:

Task Title: {context.title}
Description: {context.description}
Recipient: {context.recipient or 'Not specified'}
Subject Hint: {context.subject or 'Generate appropriate subject'}
Context Hints: {', '.join(context.context_hints) if context.context_hints else 'None'}
Priority: {context.priority}

Company Guidelines:
{context.company_context.get('email_policy', 'Use professional business communication standards.')}
"""

        response = await self._call_claude_api(user_prompt, system_prompt)

        if response:
            try:
                data = json.loads(response)
                return GeneratedContent(
                    content=data.get("body", ""),
                    subject=data.get("subject"),
                    confidence=float(data.get("confidence", 0.7)),
                    fallback_used=False,
                )
            except (json.JSONDecodeError, KeyError) as e:
                logger.warning(f"Failed to parse Claude response: {e}")

        # Fallback to template
        return self._generate_fallback_email(context)

    async def generate_whatsapp_message(
        self, context: TaskContext
    ) -> GeneratedContent:
        """Generate WhatsApp message content using AI.

        Args:
            context: Extracted task context

        Returns:
            GeneratedContent with message body
        """
        system_prompt = """You are an AI assistant drafting WhatsApp messages for business communication.
Your task is to generate a brief, professional yet friendly message.

Guidelines:
- Keep it under 500 characters
- Be friendly but professional
- Get to the point quickly
- No formal email-style greeting needed

Respond ONLY with valid JSON in this exact format:
{
    "content": "The WhatsApp message content",
    "confidence": 0.85
}

The confidence score should reflect how well you understood the request (0.0-1.0).
"""

        user_prompt = f"""Generate a WhatsApp message based on this context:

Task Title: {context.title}
Description: {context.description}
Recipient: {context.recipient or 'Not specified'}
Context Hints: {', '.join(context.context_hints) if context.context_hints else 'None'}
Priority: {context.priority}

Company Guidelines:
{context.company_context.get('whatsapp_policy', 'Keep messages brief and professional.')}
"""

        response = await self._call_claude_api(user_prompt, system_prompt)

        if response:
            try:
                data = json.loads(response)
                return GeneratedContent(
                    content=data.get("content", ""),
                    confidence=float(data.get("confidence", 0.7)),
                    fallback_used=False,
                )
            except (json.JSONDecodeError, KeyError) as e:
                logger.warning(f"Failed to parse Claude response: {e}")

        # Fallback to template
        return self._generate_fallback_whatsapp(context)

    async def generate_social_post(
        self, context: TaskContext, platform: str
    ) -> GeneratedContent:
        """Generate social media post content using AI.

        Args:
            context: Extracted task context
            platform: Social platform (linkedin, instagram, facebook, twitter)

        Returns:
            GeneratedContent with post content and hashtags
        """
        guidelines = self.PLATFORM_GUIDELINES.get(platform, {})

        system_prompt = f"""You are an AI assistant creating {platform} posts for business purposes.
Your task is to generate engaging, professional content optimized for {platform}.

Platform Guidelines:
- Tone: {guidelines.get('tone', 'professional')}
- Length: {guidelines.get('length', 'appropriate for platform')}
- Format: {guidelines.get('format', 'engaging content')}
- Hashtags: {guidelines.get('hashtags', 'relevant hashtags if applicable')}

Respond ONLY with valid JSON in this exact format:
{{
    "content": "The post content",
    "hashtags": ["hashtag1", "hashtag2"],
    "confidence": 0.85
}}

The confidence score should reflect how well you understood the request (0.0-1.0).
"""

        user_prompt = f"""Generate a {platform} post based on this context:

Task Title: {context.title}
Description: {context.description}
Context Hints: {', '.join(context.context_hints) if context.context_hints else 'None'}

Company Guidelines:
{context.company_context.get(f'{platform}_policy', f'Follow {platform} best practices.')}
"""

        response = await self._call_claude_api(user_prompt, system_prompt)

        if response:
            try:
                data = json.loads(response)
                return GeneratedContent(
                    content=data.get("content", ""),
                    hashtags=data.get("hashtags", []),
                    confidence=float(data.get("confidence", 0.7)),
                    fallback_used=False,
                )
            except (json.JSONDecodeError, KeyError) as e:
                logger.warning(f"Failed to parse Claude response: {e}")

        # Fallback to template
        return self._generate_fallback_social(context, platform)

    def _generate_fallback_email(self, context: TaskContext) -> GeneratedContent:
        """Generate fallback email when Claude is unavailable."""
        subject = context.subject or f"Re: {context.title}"

        body = f"""Hi,

Regarding: {context.title}

{context.description if context.description else '[Please add your message here]'}

Best regards,
[Your Name]"""

        return GeneratedContent(
            content=body.strip(),
            subject=subject,
            confidence=0.3,
            fallback_used=True,
        )

    def _generate_fallback_whatsapp(self, context: TaskContext) -> GeneratedContent:
        """Generate fallback WhatsApp message when Claude is unavailable."""
        message = f"""Hi! Regarding {context.title}:

{context.description if context.description else '[Please add your message here]'}"""

        return GeneratedContent(
            content=message.strip()[:500],  # WhatsApp limit
            confidence=0.3,
            fallback_used=True,
        )

    def _generate_fallback_social(
        self, context: TaskContext, platform: str
    ) -> GeneratedContent:
        """Generate fallback social post when Claude is unavailable."""
        content = f"""{context.title}

{context.description if context.description else '[Please add your post content here]'}"""

        # Default hashtags based on platform
        default_hashtags = {
            "linkedin": ["#business", "#professional"],
            "instagram": ["#business", "#instagram"],
            "facebook": [],
            "twitter": [],
        }

        return GeneratedContent(
            content=content.strip(),
            hashtags=default_hashtags.get(platform, []),
            confidence=0.3,
            fallback_used=True,
        )

    async def _call_claude_api(
        self, user_prompt: str, system_prompt: str
    ) -> Optional[str]:
        """Call Claude API for content generation.

        Args:
            user_prompt: The user message
            system_prompt: The system instructions

        Returns:
            Claude's response text or None if failed
        """
        # Check API key
        api_key = os.getenv("CLAUDE_API_KEY") or os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            logger.warning(
                "CLAUDE_API_KEY/ANTHROPIC_API_KEY not set, using fallback"
            )
            return None

        # Check circuit breaker
        if self._error_recovery.is_circuit_open("claude_api"):
            logger.warning("Claude API circuit breaker open, using fallback")
            return None

        try:
            headers = {
                "x-api-key": api_key,
                "anthropic-version": self.CLAUDE_API_VERSION,
                "content-type": "application/json",
            }

            data = {
                "model": self.CLAUDE_MODEL,
                "max_tokens": self.MAX_TOKENS,
                "system": system_prompt,
                "messages": [{"role": "user", "content": user_prompt}],
            }

            async with httpx.AsyncClient(timeout=self.API_TIMEOUT) as client:
                response = await client.post(
                    self.CLAUDE_API_URL, headers=headers, json=data
                )

                if response.status_code == 200:
                    result = response.json()
                    content = result.get("content", [])

                    if content and len(content) > 0:
                        text_response = content[0].get("text", "")
                        self._error_recovery.record_success("claude_api")

                        # Extract JSON from response (may be wrapped in markdown)
                        json_match = re.search(r"\{.*\}", text_response, re.DOTALL)
                        if json_match:
                            return json_match.group()
                        return text_response

                else:
                    logger.error(
                        f"Claude API error: {response.status_code} - {response.text}"
                    )
                    self._error_recovery.record_failure("claude_api")
                    return None

        except httpx.TimeoutException:
            logger.error("Claude API request timed out")
            self._error_recovery.record_failure("claude_api")
            return None

        except Exception as e:
            logger.error(f"Error calling Claude API: {e}")
            self._error_recovery.record_failure("claude_api")
            return None

        return None


# Global instance
_ai_reasoning: Optional[AIReasoningService] = None


def get_ai_reasoning_service(vault_path: Optional[str] = None) -> AIReasoningService:
    """Get or create the global AI Reasoning Service instance.

    Args:
        vault_path: Path to the vault directory (required on first call)

    Returns:
        AIReasoningService instance
    """
    global _ai_reasoning
    if _ai_reasoning is None:
        if vault_path is None:
            vault_path = os.getenv("VAULT_PATH", "./AI_Employee_Vault")
        _ai_reasoning = AIReasoningService(Path(vault_path))
    return _ai_reasoning
