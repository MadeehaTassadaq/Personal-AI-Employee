"""Tests for AIReasoningService."""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, patch, MagicMock
import json
import tempfile
import shutil

from backend.services.ai_reasoning import (
    AIReasoningService,
    TaskContext,
    GeneratedContent,
    get_ai_reasoning_service,
)


@pytest.fixture
def temp_vault():
    """Create a temporary vault directory for testing."""
    temp_dir = tempfile.mkdtemp()
    vault_path = Path(temp_dir) / "AI_Employee_Vault"
    vault_path.mkdir()

    # Create required subdirectories
    for subdir in ["Inbox", "Needs_Action", "Pending_Approval", "Approved", "Done"]:
        (vault_path / subdir).mkdir()

    # Create a Company_Handbook.md file
    handbook_content = """# Company Handbook - Digital FTE Operations

## Communication Policies

### Email Policy

1. **Never send without approval** - Always create in `Pending_Approval/` first
2. **Use professional tone** - Formal business communication
3. **No sensitive data** - Never include passwords, tokens, or PII

### WhatsApp Policy

1. **Business hours only** - 9 AM to 6 PM local time
2. **Urgent only** - Use for time-sensitive matters
3. **Brief messages** - Keep under 500 characters

### LinkedIn Policy

1. **Professional content only** - Business-relevant posts
2. **No controversial topics** - Politics, religion, sensitive matters
3. **Maximum 2 posts per day** - Avoid spam behavior
"""
    (vault_path / "Company_Handbook.md").write_text(handbook_content)

    yield vault_path

    # Cleanup
    shutil.rmtree(temp_dir)


@pytest.fixture
def ai_reasoning_service(temp_vault):
    """Create an AIReasoningService instance for testing."""
    return AIReasoningService(temp_vault)


@pytest.fixture
def sample_task_content():
    """Sample task file content with frontmatter."""
    return """---
title: "Send quarterly report to team"
type: email
priority: high
recipient: team@example.com
subject: "Q4 2025 Performance Report"
tags:
  - quarterly
  - reporting
---

# Send quarterly report to team

## Description
Please send the Q4 2025 performance report to the entire team. Highlight the key achievements and areas for improvement.

## Action Items
- [ ] Attach the report PDF
- [ ] Include summary of key metrics
- [ ] Schedule follow-up meeting

## Notes
The report is available in the Reports folder.
"""


@pytest.fixture
def sample_task_path(temp_vault, sample_task_content):
    """Create a sample task file and return its path."""
    task_path = temp_vault / "Needs_Action" / "send-quarterly-report.md"
    task_path.write_text(sample_task_content)
    return task_path


class TestTaskContextParsing:
    """Tests for parse_task_context method."""

    def test_parse_task_context_with_frontmatter(
        self, ai_reasoning_service, sample_task_content, sample_task_path
    ):
        """Test parsing a task file with full frontmatter."""
        context = ai_reasoning_service.parse_task_context(
            sample_task_content, sample_task_path
        )

        assert context.task_id == "send-quarterly-report"
        assert context.task_type == "email"
        assert context.title == "Send quarterly report to team"
        assert context.recipient == "team@example.com"
        assert context.subject == "Q4 2025 Performance Report"
        assert context.priority == "high"
        assert "Tag: quarterly" in context.context_hints
        assert "Tag: reporting" in context.context_hints

    def test_parse_task_context_without_frontmatter(
        self, ai_reasoning_service, temp_vault
    ):
        """Test parsing a task file without frontmatter."""
        content = """# Simple Task

Just a simple task without any frontmatter.
"""
        task_path = temp_vault / "Needs_Action" / "simple-task.md"
        task_path.write_text(content)

        context = ai_reasoning_service.parse_task_context(content, task_path)

        assert context.task_id == "simple-task"
        assert context.title == "Simple Task"
        assert context.priority == "normal"

    def test_parse_task_context_extracts_email_from_content(
        self, ai_reasoning_service, temp_vault
    ):
        """Test that email addresses are extracted from content."""
        content = """# Contact client

Please reach out to john.doe@company.com about the project update.
"""
        task_path = temp_vault / "Needs_Action" / "contact-client.md"
        task_path.write_text(content)

        context = ai_reasoning_service.parse_task_context(content, task_path)

        assert context.recipient == "john.doe@company.com"

    def test_parse_task_context_extracts_phone_from_content(
        self, ai_reasoning_service, temp_vault
    ):
        """Test that phone numbers are extracted from content."""
        content = """# Call supplier

Contact the supplier at +1234567890123 regarding the delivery.
"""
        task_path = temp_vault / "Needs_Action" / "call-supplier.md"
        task_path.write_text(content)

        context = ai_reasoning_service.parse_task_context(content, task_path)

        assert context.recipient == "+1234567890123"

    def test_parse_task_context_loads_company_context(
        self, ai_reasoning_service, sample_task_content, sample_task_path
    ):
        """Test that company context is loaded from handbook."""
        context = ai_reasoning_service.parse_task_context(
            sample_task_content, sample_task_path
        )

        assert context.company_context.get("has_handbook") is True
        assert "Never send without approval" in context.company_context.get(
            "email_policy", ""
        )

    def test_detect_platform_from_content(self, ai_reasoning_service, temp_vault):
        """Test platform detection from content keywords."""
        test_cases = [
            ("Send an email to the team", "email"),
            ("Post on LinkedIn about the launch", "linkedin"),
            ("WhatsApp message to client", "whatsapp"),
            ("Share on Instagram", "instagram"),
            ("Tweet about the event", "twitter"),
            ("Random task without keywords", "unknown"),
        ]

        for content, expected_platform in test_cases:
            task_content = f"# Task\n\n{content}"
            task_path = temp_vault / "Needs_Action" / "detect-test.md"
            task_path.write_text(task_content)

            context = ai_reasoning_service.parse_task_context(task_content, task_path)
            assert context.platform == expected_platform, f"Failed for: {content}"


class TestEmailGeneration:
    """Tests for generate_email_content method."""

    @pytest.mark.asyncio
    async def test_generate_email_content_fallback(
        self, ai_reasoning_service, sample_task_content, sample_task_path
    ):
        """Test email generation falls back gracefully without API key."""
        context = ai_reasoning_service.parse_task_context(
            sample_task_content, sample_task_path
        )

        # Without CLAUDE_API_KEY set, should use fallback
        with patch.dict("os.environ", {}, clear=True):
            generated = await ai_reasoning_service.generate_email_content(context)

        assert generated.fallback_used is True
        assert generated.confidence == 0.3
        assert generated.subject == "Q4 2025 Performance Report"
        assert "Best regards" in generated.content

    @pytest.mark.asyncio
    async def test_generate_email_content_with_claude_api(
        self, ai_reasoning_service, sample_task_content, sample_task_path
    ):
        """Test email generation with mocked Claude API."""
        context = ai_reasoning_service.parse_task_context(
            sample_task_content, sample_task_path
        )

        mock_response = {
            "subject": "Q4 2025 Performance Report - Summary",
            "body": "Dear Team,\n\nI am pleased to share the Q4 2025 performance report.\n\nBest regards,\nTeam Lead",
            "confidence": 0.92,
        }

        with patch.dict("os.environ", {"CLAUDE_API_KEY": "test-key"}):
            with patch.object(
                ai_reasoning_service,
                "_call_claude_api",
                new_callable=AsyncMock,
                return_value=json.dumps(mock_response),
            ):
                generated = await ai_reasoning_service.generate_email_content(context)

        assert generated.fallback_used is False
        assert generated.confidence == 0.92
        assert generated.subject == "Q4 2025 Performance Report - Summary"
        assert "Dear Team" in generated.content


class TestWhatsAppGeneration:
    """Tests for generate_whatsapp_message method."""

    @pytest.mark.asyncio
    async def test_generate_whatsapp_fallback(self, ai_reasoning_service, temp_vault):
        """Test WhatsApp message generation falls back gracefully."""
        task_content = """---
title: "Remind about meeting"
type: whatsapp
recipient: +1234567890
---

# Remind about meeting

Send a reminder about tomorrow's meeting at 3 PM.
"""
        task_path = temp_vault / "Needs_Action" / "meeting-reminder.md"
        task_path.write_text(task_content)

        context = ai_reasoning_service.parse_task_context(task_content, task_path)

        with patch.dict("os.environ", {}, clear=True):
            generated = await ai_reasoning_service.generate_whatsapp_message(context)

        assert generated.fallback_used is True
        assert generated.confidence == 0.3
        assert len(generated.content) <= 500  # WhatsApp limit

    @pytest.mark.asyncio
    async def test_generate_whatsapp_with_claude_api(
        self, ai_reasoning_service, temp_vault
    ):
        """Test WhatsApp message generation with mocked Claude API."""
        task_content = """---
title: "Confirm appointment"
type: whatsapp
---

# Confirm appointment

Confirm the appointment for tomorrow at 2 PM.
"""
        task_path = temp_vault / "Needs_Action" / "confirm-appointment.md"
        task_path.write_text(task_content)

        context = ai_reasoning_service.parse_task_context(task_content, task_path)

        mock_response = {
            "content": "Hi! Just confirming our appointment tomorrow at 2 PM. Please let me know if you need to reschedule.",
            "confidence": 0.88,
        }

        with patch.dict("os.environ", {"CLAUDE_API_KEY": "test-key"}):
            with patch.object(
                ai_reasoning_service,
                "_call_claude_api",
                new_callable=AsyncMock,
                return_value=json.dumps(mock_response),
            ):
                generated = await ai_reasoning_service.generate_whatsapp_message(
                    context
                )

        assert generated.fallback_used is False
        assert generated.confidence == 0.88
        assert "appointment" in generated.content.lower()


class TestSocialPostGeneration:
    """Tests for generate_social_post method."""

    @pytest.mark.asyncio
    async def test_generate_linkedin_fallback(self, ai_reasoning_service, temp_vault):
        """Test LinkedIn post generation falls back gracefully."""
        task_content = """---
title: "Announce product launch"
type: social
platform: linkedin
---

# Announce product launch

Share exciting news about our new product launch on LinkedIn.
"""
        task_path = temp_vault / "Needs_Action" / "product-launch.md"
        task_path.write_text(task_content)

        context = ai_reasoning_service.parse_task_context(task_content, task_path)

        with patch.dict("os.environ", {}, clear=True):
            generated = await ai_reasoning_service.generate_social_post(
                context, "linkedin"
            )

        assert generated.fallback_used is True
        assert generated.confidence == 0.3
        assert "#business" in generated.hashtags
        assert "#professional" in generated.hashtags

    @pytest.mark.asyncio
    async def test_generate_instagram_fallback(self, ai_reasoning_service, temp_vault):
        """Test Instagram post generation falls back gracefully."""
        task_content = """---
title: "Share team photo"
type: social
platform: instagram
---

# Share team photo

Post the team retreat photo on Instagram.
"""
        task_path = temp_vault / "Needs_Action" / "team-photo.md"
        task_path.write_text(task_content)

        context = ai_reasoning_service.parse_task_context(task_content, task_path)

        with patch.dict("os.environ", {}, clear=True):
            generated = await ai_reasoning_service.generate_social_post(
                context, "instagram"
            )

        assert generated.fallback_used is True
        assert "#business" in generated.hashtags
        assert "#instagram" in generated.hashtags

    @pytest.mark.asyncio
    async def test_generate_social_with_claude_api(
        self, ai_reasoning_service, temp_vault
    ):
        """Test social post generation with mocked Claude API."""
        task_content = """---
title: "Celebrate milestone"
type: social
platform: linkedin
---

# Celebrate milestone

Share the exciting news about reaching 1000 customers.
"""
        task_path = temp_vault / "Needs_Action" / "milestone.md"
        task_path.write_text(task_content)

        context = ai_reasoning_service.parse_task_context(task_content, task_path)

        mock_response = {
            "content": "Thrilled to announce we've reached 1,000 customers! Thank you for your trust and support.",
            "hashtags": ["milestone", "growth", "thankyou", "business"],
            "confidence": 0.91,
        }

        with patch.dict("os.environ", {"CLAUDE_API_KEY": "test-key"}):
            with patch.object(
                ai_reasoning_service,
                "_call_claude_api",
                new_callable=AsyncMock,
                return_value=json.dumps(mock_response),
            ):
                generated = await ai_reasoning_service.generate_social_post(
                    context, "linkedin"
                )

        assert generated.fallback_used is False
        assert generated.confidence == 0.91
        assert "1,000 customers" in generated.content
        assert "milestone" in generated.hashtags


class TestClaudeAPICall:
    """Tests for _call_claude_api method."""

    @pytest.mark.asyncio
    async def test_api_call_without_key(self, ai_reasoning_service):
        """Test API call returns None without API key."""
        with patch.dict("os.environ", {}, clear=True):
            result = await ai_reasoning_service._call_claude_api(
                "Test prompt", "System prompt"
            )

        assert result is None

    @pytest.mark.asyncio
    async def test_api_call_with_circuit_breaker_open(self, ai_reasoning_service):
        """Test API call returns None when circuit breaker is open."""
        with patch.dict("os.environ", {"CLAUDE_API_KEY": "test-key"}):
            with patch.object(
                ai_reasoning_service._error_recovery,
                "is_circuit_open",
                return_value=True,
            ):
                result = await ai_reasoning_service._call_claude_api(
                    "Test prompt", "System prompt"
                )

        assert result is None

    @pytest.mark.asyncio
    async def test_api_call_success(self, ai_reasoning_service):
        """Test successful API call."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "content": [{"text": '{"result": "success"}'}]
        }

        with patch.dict("os.environ", {"CLAUDE_API_KEY": "test-key"}):
            with patch("httpx.AsyncClient") as mock_client:
                mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                    return_value=mock_response
                )

                result = await ai_reasoning_service._call_claude_api(
                    "Test prompt", "System prompt"
                )

        assert result == '{"result": "success"}'

    @pytest.mark.asyncio
    async def test_api_call_handles_error(self, ai_reasoning_service):
        """Test API call handles errors gracefully."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"

        with patch.dict("os.environ", {"CLAUDE_API_KEY": "test-key"}):
            with patch("httpx.AsyncClient") as mock_client:
                mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                    return_value=mock_response
                )

                result = await ai_reasoning_service._call_claude_api(
                    "Test prompt", "System prompt"
                )

        assert result is None


class TestGetAIReasoningService:
    """Tests for the global service getter."""

    def test_get_ai_reasoning_service_creates_instance(self, temp_vault):
        """Test that get_ai_reasoning_service creates an instance."""
        # Reset global instance for clean test
        import backend.services.ai_reasoning as module

        module._ai_reasoning = None

        service = get_ai_reasoning_service(str(temp_vault))

        assert isinstance(service, AIReasoningService)

    def test_get_ai_reasoning_service_returns_same_instance(self, temp_vault):
        """Test that get_ai_reasoning_service returns the same instance."""
        import backend.services.ai_reasoning as module

        module._ai_reasoning = None

        service1 = get_ai_reasoning_service(str(temp_vault))
        service2 = get_ai_reasoning_service(str(temp_vault))

        assert service1 is service2
