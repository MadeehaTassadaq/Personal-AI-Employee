"""CEO Briefing API endpoints."""

import json
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException
import yaml

from ..services.audit_logger import get_audit_logger, AuditAction, AuditLevel

router = APIRouter()


class CEOBriefingGenerator:
    """Generates executive briefing reports from vault data."""

    def __init__(self, vault_path: Path):
        self.vault_path = vault_path

    def _parse_frontmatter(self, content: str) -> dict:
        """Extract YAML frontmatter from markdown content."""
        if not content.startswith("---"):
            return {}
        parts = content.split("---", 2)
        if len(parts) >= 3:
            try:
                return yaml.safe_load(parts[1]) or {}
            except yaml.YAMLError:
                return {}
        return {}

    def get_completed_tasks_this_week(self) -> list:
        """Get tasks completed this week."""
        done_path = self.vault_path / "Done"
        if not done_path.exists():
            return []

        today = datetime.now(timezone.utc)
        week_start = today - timedelta(days=today.weekday())  # Monday

        tasks = []
        for file_path in done_path.glob("*.md"):
            if file_path.name.startswith("."):
                continue

            content = file_path.read_text()
            frontmatter = self._parse_frontmatter(content)

            created_str = frontmatter.get("created", "")
            if created_str:
                try:
                    created = datetime.fromisoformat(str(created_str).replace('Z', '+00:00'))
                    if created.tzinfo is None:
                        created = created.replace(tzinfo=timezone.utc)
                    if created >= week_start:
                        tasks.append({
                            "title": frontmatter.get("title", file_path.stem),
                            "type": frontmatter.get("type", "unknown"),
                            "created": str(created_str)
                        })
                except ValueError:
                    pass

        return tasks

    def get_pending_approvals(self) -> list:
        """Get pending approval items."""
        pending_path = self.vault_path / "Pending_Approval"
        if not pending_path.exists():
            return []

        items = []
        for file_path in pending_path.glob("*.md"):
            if file_path.name.startswith("."):
                continue

            content = file_path.read_text()
            frontmatter = self._parse_frontmatter(content)

            items.append({
                "title": frontmatter.get("title", file_path.stem),
                "type": frontmatter.get("type", "unknown"),
                "platform": frontmatter.get("platform", "unknown")
            })

        return items

    def get_active_tasks(self) -> list:
        """Get tasks in Needs_Action folder."""
        needs_action_path = self.vault_path / "Needs_Action"
        if not needs_action_path.exists():
            return []

        tasks = []
        for file_path in needs_action_path.glob("*.md"):
            if file_path.name.startswith("."):
                continue

            content = file_path.read_text()
            frontmatter = self._parse_frontmatter(content)

            tasks.append({
                "title": frontmatter.get("title", file_path.stem),
                "status": frontmatter.get("status", "in_progress")
            })

        return tasks

    def get_social_metrics(self) -> dict:
        """Get social media metrics from logs."""
        metrics = {
            "emails_sent": 0,
            "whatsapp_messages": 0,
            "linkedin_posts": 0,
            "facebook_posts": 0,
            "instagram_posts": 0,
            "twitter_posts": 0
        }

        logs_path = self.vault_path / "Logs"
        if not logs_path.exists():
            return metrics

        log_files = list(logs_path.glob("*.json"))
        for log_file in log_files[-7:]:  # Last 7 days
            try:
                entries = json.loads(log_file.read_text())
                if not isinstance(entries, list):
                    entries = [entries]

                for entry in entries:
                    action_type = entry.get("action_type", "").lower()
                    platform = entry.get("platform", "").lower()

                    if "email" in action_type or platform == "email":
                        metrics["emails_sent"] += 1
                    elif "whatsapp" in action_type or platform == "whatsapp":
                        metrics["whatsapp_messages"] += 1
                    elif "linkedin" in action_type or platform == "linkedin":
                        metrics["linkedin_posts"] += 1
                    elif "facebook" in action_type or platform == "facebook":
                        metrics["facebook_posts"] += 1
                    elif "instagram" in action_type or platform == "instagram":
                        metrics["instagram_posts"] += 1
                    elif "twitter" in action_type or platform == "twitter":
                        metrics["twitter_posts"] += 1
            except (json.JSONDecodeError, KeyError):
                continue

        return metrics

    def get_bottlenecks(self) -> list:
        """Identify current bottlenecks."""
        bottlenecks = []

        # Check for stale pending approvals (older than 24 hours)
        pending_path = self.vault_path / "Pending_Approval"
        if pending_path.exists():
            for file_path in pending_path.glob("*.md"):
                if file_path.name.startswith("."):
                    continue

                stat = file_path.stat()
                age_hours = (datetime.now().timestamp() - stat.st_mtime) / 3600

                if age_hours > 24:
                    content = file_path.read_text()
                    frontmatter = self._parse_frontmatter(content)
                    bottlenecks.append({
                        "type": "stale_approval",
                        "item": frontmatter.get("title", file_path.stem),
                        "age_hours": round(age_hours, 1)
                    })

        # Check for high volume of needs_action items
        needs_action_path = self.vault_path / "Needs_Action"
        if needs_action_path.exists():
            count = len(list(needs_action_path.glob("*.md")))
            if count > 10:
                bottlenecks.append({
                    "type": "task_backlog",
                    "count": count,
                    "message": f"{count} tasks awaiting processing"
                })

        return bottlenecks

    def generate_briefing(self) -> str:
        """Generate the full CEO briefing report."""
        now = datetime.now()
        week_num = now.isocalendar()[1]

        completed_tasks = self.get_completed_tasks_this_week()
        pending_approvals = self.get_pending_approvals()
        active_tasks = self.get_active_tasks()
        social_metrics = self.get_social_metrics()
        bottlenecks = self.get_bottlenecks()

        # Build the briefing content
        briefing = f"""---
type: ceo_briefing
created: {now.isoformat()}
week: {week_num}
---

# CEO Weekly Briefing

**Generated:** {now.strftime('%Y-%m-%d %H:%M:%S')}
**Week:** {week_num} of {now.year}

---

## Executive Summary

This week, your AI Employee completed **{len(completed_tasks)}** tasks across various platforms.
Currently, **{len(pending_approvals)}** items await your approval and **{len(active_tasks)}** tasks are in progress.

---

## Tasks Completed This Week

"""

        if completed_tasks:
            for task in completed_tasks[:10]:
                briefing += f"- **{task['title']}** ({task['type']})\n"
        else:
            briefing += "_No tasks completed this week._\n"

        briefing += """
---

## Pending Approvals

"""

        if pending_approvals:
            briefing += "| Item | Type | Platform |\n"
            briefing += "|------|------|----------|\n"
            for item in pending_approvals[:10]:
                briefing += f"| {item['title']} | {item['type']} | {item['platform']} |\n"
        else:
            briefing += "_No items pending approval._\n"

        briefing += """
---

## Social Media Activity (Last 7 Days)

"""

        total_social = (social_metrics['linkedin_posts'] + social_metrics['facebook_posts'] +
                       social_metrics['instagram_posts'] + social_metrics['twitter_posts'])

        briefing += f"""| Platform | Count |
|----------|-------|
| LinkedIn | {social_metrics['linkedin_posts']} |
| Facebook | {social_metrics['facebook_posts']} |
| Instagram | {social_metrics['instagram_posts']} |
| Twitter/X | {social_metrics['twitter_posts']} |
| **Total Posts** | **{total_social}** |

**Communications:**
- Emails Sent: {social_metrics['emails_sent']}
- WhatsApp Messages: {social_metrics['whatsapp_messages']}

---

## Bottlenecks & Attention Required

"""

        if bottlenecks:
            for b in bottlenecks:
                if b['type'] == 'stale_approval':
                    briefing += f"- ⚠️ **Stale Approval:** {b['item']} has been waiting for {b['age_hours']} hours\n"
                elif b['type'] == 'task_backlog':
                    briefing += f"- ⚠️ **Task Backlog:** {b['message']}\n"
        else:
            briefing += "✅ _No bottlenecks identified._\n"

        briefing += """
---

## Recommendations

"""

        # Generate recommendations based on data
        recommendations = []

        if len(pending_approvals) > 5:
            recommendations.append("Review and clear pending approvals to keep workflow moving")

        if social_metrics['linkedin_posts'] == 0:
            recommendations.append("Consider posting to LinkedIn to maintain professional presence")

        if len(completed_tasks) < 3:
            recommendations.append("Task completion is low - check if Ralph Wiggum is running")

        if bottlenecks:
            recommendations.append("Address the bottlenecks above to improve throughput")

        if recommendations:
            for rec in recommendations:
                briefing += f"1. {rec}\n"
        else:
            briefing += "_No specific recommendations at this time._\n"

        briefing += """
---

## Quick Actions

- [View Dashboard](Dashboard.md)
- [Check Pending Approvals](Pending_Approval/)
- [Review Active Tasks](Needs_Action/)
- [View Logs](Logs/)

---

*This briefing was automatically generated by your Personal AI Employee.*
"""

        return briefing

    def save_briefing(self, content: str) -> str:
        """Save briefing to Reports folder."""
        reports_path = self.vault_path / "Reports"
        reports_path.mkdir(parents=True, exist_ok=True)

        filename = f"CEO_Briefing_{datetime.now().strftime('%Y-%m-%d_%H%M%S')}.md"
        file_path = reports_path / filename

        file_path.write_text(content)

        return str(file_path)


@router.post("/generate")
async def generate_ceo_briefing():
    """Generate a CEO briefing report.

    Returns:
        Path to the generated report file
    """
    try:
        vault_path = Path(os.getenv("VAULT_PATH", "./AI_Employee_Vault"))

        generator = CEOBriefingGenerator(vault_path)
        briefing_content = generator.generate_briefing()
        report_path = generator.save_briefing(briefing_content)

        # Log the action
        audit_logger = get_audit_logger()
        audit_logger.log(
            AuditAction.INFO,
            platform="system",
            actor="ceo_briefing",
            details={
                "action": "briefing_generated",
                "report_path": report_path
            }
        )

        return {
            "message": "CEO briefing generated successfully",
            "report_path": report_path,
            "generated_at": datetime.now().isoformat()
        }

    except Exception as e:
        # Log the error
        audit_logger = get_audit_logger()
        audit_logger.log(
            AuditAction.ERROR,
            platform="system",
            level=AuditLevel.ERROR,
            actor="ceo_briefing",
            details={
                "action": "briefing_generation_failed",
                "error": str(e)
            }
        )

        raise HTTPException(status_code=500, detail=f"Failed to generate briefing: {str(e)}")


@router.get("/latest")
async def get_latest_briefing():
    """Get the most recent CEO briefing report.

    Returns:
        Content of the latest briefing report
    """
    vault_path = Path(os.getenv("VAULT_PATH", "./AI_Employee_Vault"))
    reports_dir = vault_path / "Reports"

    if not reports_dir.exists():
        raise HTTPException(status_code=404, detail="No reports directory found")

    # Find the most recent CEO briefing file
    briefing_files = list(reports_dir.glob("CEO_Briefing_*.md"))

    if not briefing_files:
        raise HTTPException(status_code=404, detail="No CEO briefings found")

    # Sort by modification time to get the most recent
    latest_file = max(briefing_files, key=lambda f: f.stat().st_mtime)

    try:
        content = latest_file.read_text()

        return {
            "file_path": str(latest_file),
            "content": content,
            "modified_at": datetime.fromtimestamp(latest_file.stat().st_mtime).isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read briefing: {str(e)}")
