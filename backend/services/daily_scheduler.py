"""Daily scheduler for automated content processing and meeting reminders.

This service handles time-based daily tasks:
- Processing inbox at 9 AM for social content creation
- Checking meeting reminders at 8 AM
"""

import os
import asyncio
from datetime import datetime, time, timedelta
from pathlib import Path
from typing import Optional

import yaml

from backend.services.audit_logger import get_audit_logger, AuditAction


class DailyScheduler:
    """Scheduler for daily time-based tasks."""

    def __init__(self):
        """Initialize the daily scheduler."""
        self.vault_path = Path(os.getenv("VAULT_PATH", "./AI_Employee_Vault"))
        self.dry_run = os.getenv("DRY_RUN", "true").lower() == "true"
        self.audit_logger = get_audit_logger()

        # Schedule times (hour, minute)
        self.inbox_process_time = (9, 0)  # 9:00 AM
        self.meeting_reminder_time = (8, 0)  # 8:00 AM

        # Track if tasks have run today
        self.last_inbox_process_date: Optional[str] = None
        self.last_meeting_reminder_date: Optional[str] = None

    def get_today_date_str(self) -> str:
        """Get today's date as YYYY-MM-DD string."""
        return datetime.now().strftime("%Y-%m-%d")

    def should_run_inbox_process(self) -> bool:
        """Check if inbox processing should run now."""
        now = datetime.now()
        current_time = (now.hour, now.minute)
        today = self.get_today_date_str()

        # Check if it's the right time and hasn't run today
        return (
            current_time >= self.inbox_process_time and
            self.last_inbox_process_date != today
        )

    def should_run_meeting_reminders(self) -> bool:
        """Check if meeting reminders should run now."""
        now = datetime.now()
        current_time = (now.hour, now.minute)
        today = self.get_today_date_str()

        # Check if it's the right time and hasn't run today
        return (
            current_time >= self.meeting_reminder_time and
            self.last_meeting_reminder_date != today
        )

    async def process_daily_inbox(self):
        """Process inbox and create scheduled social posts.

        This runs at 9 AM daily to:
        1. Check calendar for today's events
        2. Generate social content for events
        3. Create posts in Pending_Approval
        4. Notify user of pending approvals
        """
        if self.last_inbox_process_date == self.get_today_date_str():
            return  # Already ran today

        print("[DAILY_SCHEDULER] Processing daily inbox at 9 AM")

        try:
            # Get today's events from calendar (if calendar integration is available)
            events = await self._get_today_events()

            # Generate social content based on events
            if events:
                for event in events[:3]:  # Limit to 3 events
                    await self._create_social_post_for_event(event)

            # Process any inbox tasks
            await self._process_inbox_tasks()

            # Log the action
            self.audit_logger.log(
                AuditAction.TASK_PROCESSED,
                platform="daily_scheduler",
                actor="system",
                details={"action": "daily_inbox_process", "events_count": len(events)}
            )

            self.last_inbox_process_date = self.get_today_date_str()
            print(f"[DAILY_SCHEDULER] Daily inbox processing completed")

        except Exception as e:
            print(f"[DAILY_SCHEDULER] Error processing daily inbox: {e}")
            self.audit_logger.log(
                AuditAction.ERROR,
                platform="daily_scheduler",
                actor="system",
                details={"error": str(e), "action": "daily_inbox_process"}
            )

    async def send_meeting_reminders(self):
        """Send reminders for meetings happening today/tomorrow.

        This runs at 8 AM daily to:
        1. Get today's events from calendar
        2. Find meetings requiring reminders
        3. Send to colleagues via WhatsApp/email
        4. Create approval tasks in Pending_Approval for bulk sends
        """
        if self.last_meeting_reminder_date == self.get_today_date_str():
            return  # Already ran today

        print("[DAILY_SCHEDULER] Sending meeting reminders at 8 AM")

        try:
            # Get today's and tomorrow's events
            today_events = await self._get_today_events()
            tomorrow_events = await self._get_tomorrow_events()

            all_events = today_events + tomorrow_events

            if not all_events:
                print("[DAILY_SCHEDULER] No meetings to remind about")
                self.last_meeting_reminder_date = self.get_today_date_str()
                return

            # Create reminder task for each event
            for event in all_events:
                await self._create_reminder_task(event)

            # Log the action
            self.audit_logger.log(
                AuditAction.TASK_PROCESSED,
                platform="daily_scheduler",
                actor="system",
                details={"action": "meeting_reminders", "reminders_count": len(all_events)}
            )

            self.last_meeting_reminder_date = self.get_today_date_str()
            print(f"[DAILY_SCHEDULER] Created {len(all_events)} meeting reminder tasks")

        except Exception as e:
            print(f"[DAILY_SCHEDULER] Error sending meeting reminders: {e}")
            self.audit_logger.log(
                AuditAction.ERROR,
                platform="daily_scheduler",
                actor="system",
                details={"error": str(e), "action": "meeting_reminders"}
            )

    async def _get_today_events(self) -> list:
        """Get today's calendar events.

        Returns a list of event dictionaries with keys:
        - title: str
        - start: datetime
        - end: datetime
        - attendees: list[str]
        - description: str
        """
        try:
            # Try to use calendar MCP if available
            from mcp.calendar_mcp import server as calendar_server

            # Get today's events
            events_response = await calendar_server._get_today_events()
            # Parse response and return events list
            return self._parse_calendar_events(events_response)

        except ImportError:
            print("[DAILY_SCHEDULER] Calendar MCP not available")
            return []
        except Exception as e:
            print(f"[DAILY_SCHEDULER] Error getting calendar events: {e}")
            return []

    async def _get_tomorrow_events(self) -> list:
        """Get tomorrow's calendar events."""
        try:
            tomorrow = datetime.now() + timedelta(days=1)
            # Similar to _get_today_events but for tomorrow
            # TODO: Implement when calendar MCP supports date range queries
            return []
        except Exception as e:
            print(f"[DAILY_SCHEDULER] Error getting tomorrow's events: {e}")
            return []

    def _parse_calendar_events(self, events_response: str) -> list:
        """Parse calendar events response into structured list."""
        # Parse the calendar response and extract event details
        # This is a placeholder - actual implementation depends on calendar MCP format
        try:
            # Try to parse as JSON
            import json
            data = json.loads(events_response)
            if isinstance(data, list):
                return data
            return []
        except (json.JSONDecodeError, TypeError):
            # If not JSON, return empty list
            return []

    async def _create_social_post_for_event(self, event: dict):
        """Create a social post task for an event."""
        title = event.get("title", "Upcoming Event")
        description = event.get("description", "")

        # Generate platform-specific content
        content = f"Join me for: {title}\n\n{description}"

        # Create task in Pending_Approval
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        filename = f"social_post_event_{timestamp}.md"

        frontmatter = {
            "title": f"Social Post: {title}",
            "created": datetime.now().isoformat(),
            "priority": "normal",
            "status": "pending_approval",
            "type": "linkedin",
            "platform": "linkedin",
            "assignee": "human"
        }

        body = f"""## Description
Automated social post for event: {title}

## Post Content
{content}

## Event Details
- Title: {title}
- Time: {event.get('start', 'TBD')}
- Attendees: {', '.join(event.get('attendees', []))}
"""

        # Write to Pending_Approval
        approval_path = self.vault_path / "Pending_Approval" / filename
        approval_path.parent.mkdir(parents=True, exist_ok=True)

        # Write with YAML frontmatter
        content_with_frontmatter = "---\n"
        for key, value in frontmatter.items():
            if isinstance(value, str):
                content_with_frontmatter += f'{key}: "{value}"\n'
            else:
                content_with_frontmatter += f"{key}: {value}\n"
        content_with_frontmatter += "---\n\n" + body

        approval_path.write_text(content_with_frontmatter)
        print(f"[DAILY_SCHEDULER] Created social post task: {filename}")

    async def _process_inbox_tasks(self):
        """Process tasks in the Inbox folder."""
        inbox_path = self.vault_path / "Inbox"

        if not inbox_path.exists():
            return

        # Get all markdown files in Inbox
        inbox_files = list(inbox_path.glob("*.md"))

        for file_path in inbox_files[:5]:  # Process up to 5 tasks
            try:
                # Move to Needs_Action for Ralph to process
                needs_action_path = self.vault_path / "Needs_Action" / file_path.name
                needs_action_path.parent.mkdir(parents=True, exist_ok=True)

                file_path.rename(needs_action_path)
                print(f"[DAILY_SCHEDULER] Moved {file_path.name} to Needs_Action")

            except Exception as e:
                print(f"[DAILY_SCHEDULER] Error processing {file_path.name}: {e}")

    async def _create_reminder_task(self, event: dict):
        """Create a reminder task for a meeting.

        Creates a task in Pending_Approval that will:
        - Send WhatsApp message to attendees
        - Send email reminder to attendees
        """
        title = event.get("title", "Meeting")
        start_time = event.get("start", datetime.now())
        attendees = event.get("attendees", [])

        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        filename = f"meeting_reminder_{timestamp}.md"

        frontmatter = {
            "title": f"Meeting Reminder: {title}",
            "created": datetime.now().isoformat(),
            "priority": "high",
            "status": "pending_approval",
            "type": "whatsapp",
            "platform": "whatsapp",
            "assignee": "human",
            "event_title": title,
            "event_time": start_time.isoformat() if isinstance(start_time, datetime) else str(start_time),
            "attendees": ",".join(attendees) if attendees else ""
        }

        body = f"""## Description
Send meeting reminder to attendees.

## Meeting Details
- Title: {title}
- Time: {start_time if isinstance(start_time, str) else start_time.strftime('%Y-%m-%d %H:%M')}
- Attendees: {', '.join(attendees) if attendees else 'None specified'}

## Reminder Message
Hi! Reminder about our meeting "{title}" at {start_time if isinstance(start_time, str) else start_time.strftime('%Y-%m-%d %H:%M')}.

Looking forward to it!

## Action Required
- [ ] Send WhatsApp reminders to attendees
- [ ] Send email follow-up to attendees
"""

        # Write to Pending_Approval
        approval_path = self.vault_path / "Pending_Approval" / filename
        approval_path.parent.mkdir(parents=True, exist_ok=True)

        # Write with YAML frontmatter
        content_with_frontmatter = "---\n"
        for key, value in frontmatter.items():
            if isinstance(value, str):
                content_with_frontmatter += f'{key}: "{value}"\n'
            else:
                content_with_frontmatter += f"{key}: {value}\n"
        content_with_frontmatter += "---\n\n" + body

        approval_path.write_text(content_with_frontmatter)
        print(f"[DAILY_SCHEDULER] Created reminder task: {filename}")


# Global instance
_daily_scheduler: Optional[DailyScheduler] = None


def get_daily_scheduler() -> DailyScheduler:
    """Get or create the daily scheduler instance."""
    global _daily_scheduler
    if _daily_scheduler is None:
        _daily_scheduler = DailyScheduler()
    return _daily_scheduler


async def run_daily_checks():
    """Run scheduled daily tasks if it's time.

    This function should be called periodically (e.g., every minute)
    to check if daily tasks need to run.
    """
    scheduler = get_daily_scheduler()

    # Check inbox processing
    if scheduler.should_run_inbox_process():
        await scheduler.process_daily_inbox()

    # Check meeting reminders
    if scheduler.should_run_meeting_reminders():
        await scheduler.send_meeting_reminders()
