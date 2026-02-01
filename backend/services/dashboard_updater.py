"""Service to automatically update Dashboard.md with real metrics.

Refactored for Stable Executive Dashboard (001-stable-dashboard):
- Section-based generation with fixed order
- Item limits with overflow indicators
- Validation and recovery support
- Weekly summary aggregation
"""

import os
import json
import logging
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
import yaml

# Configure logging
logger = logging.getLogger(__name__)

# =============================================================================
# CONSTANTS (T004, T005)
# =============================================================================

# Canonical section order - DO NOT CHANGE without updating validation
SECTION_ORDER = [
    "# Digital FTE Dashboard",
    "## System Status",
    "## Pending Approvals",
    "## Active Tasks",
    "## Signals / Inputs",
    "## Recently Completed",
    "## Metrics",
    "## Weekly Summary",
    "## Quick Actions",
]

# Maximum items per section to keep dashboard concise
MAX_ITEMS_PER_SECTION = 10


class DashboardUpdater:
    """Service to update the Dashboard.md file with real metrics.

    This is the SINGLE WRITER for Dashboard.md. All dashboard updates
    MUST go through this class to prevent write collisions.
    """

    def __init__(self, vault_path: Path):
        self.vault_path = vault_path
        self.dashboard_path = vault_path / "Dashboard.md"

    # =========================================================================
    # DATA COLLECTION METHODS (existing, preserved)
    # =========================================================================

    def count_files(self, folder: str) -> int:
        """Count .md files in a vault folder."""
        folder_path = self.vault_path / folder
        if not folder_path.exists():
            return 0
        return len([f for f in folder_path.glob("*.md") if f.name != ".gitkeep"])

    def get_recent_done_tasks(self, limit: int = 10) -> list:
        """Get recent completed tasks."""
        done_path = self.vault_path / "Done"
        if not done_path.exists():
            return []

        files = []
        for file_path in done_path.glob("*.md"):
            if file_path.name == ".gitkeep":
                continue

            content = file_path.read_text()
            frontmatter = self._parse_frontmatter(content)

            title = frontmatter.get("title", file_path.stem.replace('_', ' ').replace('-', ' '))
            created_str = frontmatter.get("created", "")
            created_date = self._parse_datetime(created_str)
            task_type = frontmatter.get("type", "unknown")

            files.append({
                "name": title,
                "created": created_date,
                "created_str": str(created_str) if created_str else "",
                "type": task_type,
                "path": str(file_path),
                "filename": file_path.stem
            })

        # Sort by created date (most recent first), handling mixed timezone awareness
        def sort_key(x):
            dt = x["created"]
            if dt is None:
                return datetime.min.replace(tzinfo=timezone.utc)
            if dt.tzinfo is None:
                return dt.replace(tzinfo=timezone.utc)
            return dt

        files.sort(key=sort_key, reverse=True)
        return files[:limit]

    def get_pending_approval_tasks(self) -> list:
        """Get tasks awaiting approval."""
        pending_path = self.vault_path / "Pending_Approval"
        if not pending_path.exists():
            return []

        files = []
        for file_path in pending_path.glob("*.md"):
            if file_path.name == ".gitkeep":
                continue

            content = file_path.read_text()
            frontmatter = self._parse_frontmatter(content)

            title = frontmatter.get("title", file_path.stem.replace('_', ' ').replace('-', ' '))
            created_str = frontmatter.get("created", "")
            task_type = frontmatter.get("type", "Unknown")

            files.append({
                "name": title,
                "created": created_str,
                "type": task_type,
                "filename": file_path.stem
            })

        return files

    def get_needs_action_tasks(self) -> list:
        """Get tasks in Needs_Action folder."""
        needs_action_path = self.vault_path / "Needs_Action"
        if not needs_action_path.exists():
            return []

        files = []
        for file_path in needs_action_path.glob("*.md"):
            if file_path.name == ".gitkeep":
                continue

            content = file_path.read_text()
            frontmatter = self._parse_frontmatter(content)

            title = frontmatter.get("title", file_path.stem.replace('_', ' ').replace('-', ' '))
            status = frontmatter.get("status", "in_progress")
            created_str = frontmatter.get("created", "")

            files.append({
                "name": title,
                "status": status,
                "created": created_str,
                "filename": file_path.stem
            })

        return files

    def get_inbox_tasks(self) -> list:
        """Get tasks in Inbox folder."""
        inbox_path = self.vault_path / "Inbox"
        if not inbox_path.exists():
            return []

        files = []
        for file_path in inbox_path.glob("*.md"):
            if file_path.name == ".gitkeep":
                continue

            content = file_path.read_text()
            frontmatter = self._parse_frontmatter(content)

            title = frontmatter.get("title", file_path.stem.replace('_', ' ').replace('-', ' '))

            files.append({
                "name": title,
                "filename": file_path.stem
            })

        return files

    def get_social_metrics(self) -> Dict[str, int]:
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
        if logs_path.exists():
            log_files = list(logs_path.glob("*.json"))
            for log_file in log_files[-7:]:  # Last 7 days
                try:
                    content = log_file.read_text()
                    entries = json.loads(content)
                    if not isinstance(entries, list):
                        entries = [entries]

                    for entry in entries:
                        action_type = entry.get("action_type", "").lower()
                        if "email" in action_type:
                            metrics["emails_sent"] += 1
                        elif "whatsapp" in action_type:
                            metrics["whatsapp_messages"] += 1
                        elif "linkedin" in action_type:
                            metrics["linkedin_posts"] += 1
                        elif "facebook" in action_type:
                            metrics["facebook_posts"] += 1
                        elif "instagram" in action_type:
                            metrics["instagram_posts"] += 1
                        elif "twitter" in action_type:
                            metrics["twitter_posts"] += 1
                except (json.JSONDecodeError, KeyError, TypeError):
                    continue

        return metrics

    # =========================================================================
    # HELPER METHODS
    # =========================================================================

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

    def _parse_datetime(self, date_str: Any) -> Optional[datetime]:
        """Parse various datetime formats."""
        if not date_str:
            return None
        try:
            str_to_parse = str(date_str)
            if str_to_parse.endswith('Z'):
                str_to_parse = str_to_parse[:-1] + '+00:00'
            return datetime.fromisoformat(str_to_parse)
        except ValueError:
            try:
                return datetime.strptime(str(date_str), '%Y-%m-%d').replace(tzinfo=timezone.utc)
            except ValueError:
                return None

    def _is_watcher_running(self, watcher_name: str) -> bool:
        """Check if a specific watcher is running."""
        # Simplified check - in production, check actual process status
        return False

    def _is_service_running(self, service_name: str) -> bool:
        """Check if a specific service is running."""
        return False

    # =========================================================================
    # SECTION GENERATORS (T006, T007, T008, T011-T015, T028)
    # =========================================================================

    def _generate_header_section(self) -> str:
        """Generate header with timestamp (T006)."""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        return f"""# Digital FTE Dashboard

> Last Updated: {timestamp}

---"""

    def _generate_system_status_section(self) -> str:
        """Generate System Status table (T007)."""
        vault_name = self.vault_path.name
        file_watcher_status = "Active" if self._is_watcher_running('file') else "Stopped"
        backend_status = "Active" if self._is_service_running('backend') else "Stopped"
        gmail_status = "Configured" if os.getenv('GMAIL_CREDENTIALS') else "Not Configured"
        whatsapp_status = "Configured" if os.getenv('WHATSAPP_SESSION_PATH') else "Not Configured"
        linkedin_status = "Configured" if os.getenv('LINKEDIN_ACCESS_TOKEN') else "Not Configured"

        dry_run = os.getenv('DRY_RUN', '').lower() == 'true'
        mode_text = "Safe mode - no real actions" if dry_run else "Live mode - real actions"

        return f"""## System Status

| Component | Status | Notes |
|-----------|--------|-------|
| Vault | Active | {vault_name} |
| File Watcher | {file_watcher_status} | Check with `./scripts/run_watchers.sh` |
| Backend API | {backend_status} | Start with `./scripts/run_backend.sh` |
| Gmail MCP | {gmail_status} | OAuth token required |
| WhatsApp MCP | {whatsapp_status} | QR scan required |
| LinkedIn MCP | {linkedin_status} | Token configured |

**Mode:** `DRY_RUN={'true' if dry_run else 'false'}` ({mode_text})

---"""

    def _generate_pending_approvals_section(self) -> str:
        """Generate Pending Approvals section with item limit (T011)."""
        tasks = self.get_pending_approval_tasks()
        total_count = len(tasks)
        display_tasks = tasks[:MAX_ITEMS_PER_SECTION]

        if not tasks:
            return """## Pending Approvals

> **0 items awaiting your decision**

_No pending approvals_

**To approve:** Move file from `Pending_Approval/` to `Approved/`
**To reject:** Move file to `Done/` with rejection note

---"""

        rows = []
        for task in display_tasks:
            name = task['name'][:50]
            task_type = task.get('type', 'Unknown')
            created = task.get('created', '')
            rows.append(f"| {name} | {task_type} | {created} | Move to `Approved/` or `Done/` |")

        table = "\n".join(rows)

        overflow = ""
        if total_count > MAX_ITEMS_PER_SECTION:
            overflow = f"\n\n_View all ({total_count}) in `Pending_Approval/`_"

        return f"""## Pending Approvals

> **{total_count} items awaiting your decision**

| Item | Type | Created | Action |
|------|------|---------|--------|
{table}{overflow}

**To approve:** Move file from `Pending_Approval/` to `Approved/`
**To reject:** Move file to `Done/` with rejection note

---"""

    def _generate_active_tasks_section(self) -> str:
        """Generate Active Tasks section with table format (T012)."""
        tasks = self.get_needs_action_tasks()
        total_count = len(tasks)
        display_tasks = tasks[:MAX_ITEMS_PER_SECTION]

        if not tasks:
            return """## Active Tasks

| Task | Status | Started |
|------|--------|---------|
| _No tasks in progress_ | — | — |

---"""

        rows = []
        for task in display_tasks:
            name = task['name'][:50]
            status = task.get('status', 'in_progress')
            created = task.get('created', '—')
            if created:
                created = str(created)[:10]  # Just date part
            rows.append(f"| {name} | {status} | {created} |")

        table = "\n".join(rows)

        overflow = ""
        if total_count > MAX_ITEMS_PER_SECTION:
            overflow = f"\n\n_View all ({total_count}) in `Needs_Action/`_"

        return f"""## Active Tasks

| Task | Status | Started |
|------|--------|---------|
{table}{overflow}

---"""

    def _generate_signals_inputs_section(self) -> str:
        """Generate Signals/Inputs section with wiki-links (T013)."""
        tasks = self.get_inbox_tasks()
        total_count = len(tasks)
        display_tasks = tasks[:MAX_ITEMS_PER_SECTION]

        if not tasks:
            return """## Signals / Inputs

> **0 new items in Inbox/**

_No new signals_

---"""

        items = []
        for task in display_tasks:
            filename = task.get('filename', task['name'].replace(' ', '-'))
            title = task['name']
            items.append(f"- [[Inbox/{filename}|{title}]]")

        item_list = "\n".join(items)

        overflow = ""
        if total_count > MAX_ITEMS_PER_SECTION:
            overflow = f"\n\n_View all ({total_count}) in `Inbox/`_"

        return f"""## Signals / Inputs

> **{total_count} new items in Inbox/**

{item_list}{overflow}

---"""

    def _generate_recently_completed_section(self) -> str:
        """Generate Recently Completed section with date prefix (T014)."""
        tasks = self.get_recent_done_tasks(MAX_ITEMS_PER_SECTION)

        if not tasks:
            return """## Recently Completed

> Last 10 completed tasks

_No completed tasks_

---"""

        items = []
        for task in tasks:
            created = task.get('created_str', '')
            if created:
                date_str = str(created)[:10]  # Just date part
            else:
                date_str = "Unknown"
            title = task['name']
            items.append(f"- [{date_str}] {title}")

        item_list = "\n".join(items)

        return f"""## Recently Completed

> Last 10 completed tasks

{item_list}

---"""

    def _generate_metrics_section(self) -> str:
        """Generate Metrics section with Today/This Week columns (T015)."""
        social_metrics = self.get_social_metrics()
        pending_count = self.count_files("Pending_Approval")

        # Calculate tasks completed today and this week
        recent_tasks = self.get_recent_done_tasks(100)  # Get more for weekly count
        today = datetime.now(timezone.utc).date()
        week_start = today - timedelta(days=today.weekday())  # Monday

        tasks_today = 0
        tasks_week = 0
        social_today = 0
        social_week = 0

        for task in recent_tasks:
            task_date = task.get('created')
            if task_date:
                task_date_only = task_date.date() if hasattr(task_date, 'date') else None
                if task_date_only:
                    if task_date_only == today:
                        tasks_today += 1
                        if task.get('type') in ['social', 'email']:
                            social_today += 1
                    if task_date_only >= week_start:
                        tasks_week += 1
                        if task.get('type') in ['social', 'email']:
                            social_week += 1

        emails_week = social_metrics['emails_sent']
        social_posts_week = (social_metrics['linkedin_posts'] +
                           social_metrics['facebook_posts'] +
                           social_metrics['instagram_posts'] +
                           social_metrics['twitter_posts'])

        return f"""## Metrics

| Metric | Today | This Week |
|--------|-------|-----------|
| Tasks Completed | {tasks_today} | {tasks_week} |
| Pending Approvals | {pending_count} | — |
| Emails Sent | 0 | {emails_week} |
| Social Posts | 0 | {social_posts_week} |

---"""

    def _get_week_start_date(self) -> datetime:
        """Get Monday of current week (T026)."""
        today = datetime.now(timezone.utc)
        days_since_monday = today.weekday()
        return today - timedelta(days=days_since_monday)

    def _calculate_weekly_metrics(self) -> Dict[str, Any]:
        """Calculate weekly aggregated metrics (T027)."""
        week_start = self._get_week_start_date()
        recent_tasks = self.get_recent_done_tasks(100)

        tasks_this_week = []
        for task in recent_tasks:
            task_date = task.get('created')
            if task_date:
                # Normalize timezone awareness
                if task_date.tzinfo is None:
                    task_date = task_date.replace(tzinfo=timezone.utc)
                if task_date >= week_start:
                    tasks_this_week.append(task)

        # Count by type
        type_counts = {}
        for task in tasks_this_week:
            task_type = task.get('type', 'other')
            type_counts[task_type] = type_counts.get(task_type, 0) + 1

        return {
            "total_completed": len(tasks_this_week),
            "by_type": type_counts,
            "week_start": week_start.strftime('%Y-%m-%d')
        }

    def _generate_weekly_summary_section(self) -> str:
        """Generate collapsible Weekly Summary section (T028)."""
        metrics = self._calculate_weekly_metrics()
        week_start = metrics['week_start']
        total = metrics['total_completed']

        if total == 0:
            return f"""<details>
<summary>## Weekly Summary (Week of {week_start})</summary>

_No completed tasks this period_

</details>

---"""

        # Format type breakdown
        type_breakdown = []
        for task_type, count in metrics['by_type'].items():
            type_breakdown.append(f"{task_type.title()} ({count})")
        type_str = ", ".join(type_breakdown) if type_breakdown else "None"

        return f"""<details>
<summary>## Weekly Summary (Week of {week_start})</summary>

- **Total Tasks Completed**: {total}
- **Actions by Type**: {type_str}

</details>

---"""

    def _generate_quick_actions_section(self) -> str:
        """Generate static Quick Actions section (T008)."""
        return """## Quick Actions

- **Add task:** Create `.md` file in `Inbox/`
- **Approve action:** Move file from `Pending_Approval/` to `Approved/`
- **View logs:** Check `Logs/` folder
- **Reject action:** Move file from `Pending_Approval/` to `Done/`"""

    # =========================================================================
    # VALIDATION AND RECOVERY (T009, T022, T023, T024)
    # =========================================================================

    def _validate_dashboard_content(self, content: str) -> bool:
        """Validate dashboard has all section markers in correct order (T009)."""
        last_pos = -1
        for marker in SECTION_ORDER:
            pos = content.find(marker)
            if pos == -1:
                logger.warning(f"Missing section marker: {marker}")
                return False
            if pos < last_pos:
                logger.warning(f"Section marker out of order: {marker}")
                return False
            last_pos = pos
        return True

    def _recover_dashboard(self) -> str:
        """Regenerate dashboard from vault state (T022)."""
        logger.info("Recovering dashboard from vault state")
        return self._generate_full_dashboard()

    def _log_recovery_event(self, reason: str):
        """Log dashboard recovery event (T024)."""
        logs_path = self.vault_path / "Logs"
        logs_path.mkdir(exist_ok=True)

        recovery_log = logs_path / "dashboard-recovery.json"

        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event": "dashboard_recovery",
            "reason": reason
        }

        try:
            existing = []
            if recovery_log.exists():
                content = recovery_log.read_text()
                if content.strip():
                    existing = json.loads(content)
                    if not isinstance(existing, list):
                        existing = [existing]
            existing.append(event)
            recovery_log.write_text(json.dumps(existing, indent=2))
        except Exception as e:
            logger.error(f"Failed to log recovery event: {e}")

    # =========================================================================
    # MAIN UPDATE METHOD (T010, T016, T017, T023)
    # =========================================================================

    def _generate_full_dashboard(self) -> str:
        """Generate complete dashboard content with all sections (T016)."""
        sections = [
            self._generate_header_section(),
            self._generate_system_status_section(),
            self._generate_pending_approvals_section(),
            self._generate_active_tasks_section(),
            self._generate_signals_inputs_section(),
            self._generate_recently_completed_section(),
            self._generate_metrics_section(),
            self._generate_weekly_summary_section(),
            self._generate_quick_actions_section(),
        ]
        return "\n\n".join(sections)

    def update_dashboard(self):
        """Update the Dashboard.md file with current metrics (T010, T023).

        This method:
        1. Generates new dashboard content using section generators
        2. Validates the content structure
        3. Recovers if validation fails
        4. Writes only if content changed
        """
        # Generate new dashboard content
        dashboard_content = self._generate_full_dashboard()

        # Validate content structure
        if not self._validate_dashboard_content(dashboard_content):
            logger.error("Generated dashboard failed validation, attempting recovery")
            self._log_recovery_event("validation_failed")
            dashboard_content = self._recover_dashboard()

        # Read existing content
        current_content = ""
        if self.dashboard_path.exists():
            current_content = self.dashboard_path.read_text()

        # Write only if content changed (smart write)
        if current_content != dashboard_content:
            self.dashboard_path.write_text(dashboard_content)
            logger.debug("Dashboard updated")


def update_dashboard_now():
    """Convenience function to update dashboard immediately."""
    vault_path = Path(os.getenv("VAULT_PATH", "./AI_Employee_Vault"))
    updater = DashboardUpdater(vault_path)
    updater.update_dashboard()


if __name__ == "__main__":
    update_dashboard_now()
