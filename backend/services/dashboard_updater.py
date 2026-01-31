"""Service to automatically update Dashboard.md with real metrics."""

import os
from pathlib import Path
from datetime import datetime
import yaml
from typing import Dict, Any
import json


class DashboardUpdater:
    """Service to update the Dashboard.md file with real metrics."""

    def __init__(self, vault_path: Path):
        self.vault_path = vault_path
        self.dashboard_path = vault_path / "Dashboard.md"

    def count_files(self, folder: str) -> int:
        """Count .md files in a vault folder."""
        folder_path = self.vault_path / folder
        if not folder_path.exists():
            return 0
        return len([f for f in folder_path.glob("*.md") if f.name != ".gitkeep"])

    def get_recent_done_tasks(self, limit: int = 5) -> list:
        """Get recent completed tasks."""
        done_path = self.vault_path / "Done"
        if not done_path.exists():
            return []

        files = []
        for file_path in done_path.glob("*.md"):
            if file_path.name == ".gitkeep":
                continue

            content = file_path.read_text()
            # Extract frontmatter
            frontmatter = {}
            if content.startswith("---"):
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    try:
                        frontmatter = yaml.safe_load(parts[1]) or {}
                    except yaml.YAMLError:
                        pass

            # Get title from frontmatter or filename
            title = frontmatter.get("title", file_path.stem.replace('_', ' ').replace('-', ' '))
            created_str = frontmatter.get("created", "")

            # Parse the created date if it exists
            created_date = None
            if created_str:
                try:
                    from datetime import datetime
                    # Handle timezone info properly
                    str_to_parse = str(created_str)
                    if str_to_parse.endswith('Z'):
                        str_to_parse = str_to_parse[:-1] + '+00:00'
                    created_date = datetime.fromisoformat(str_to_parse)
                except ValueError:
                    try:
                        # Try alternative format
                        created_date = datetime.strptime(str(created_str), '%Y-%m-%d')
                    except ValueError:
                        pass

            files.append({
                "name": title,
                "created": created_date,
                "created_str": created_str,  # Keep original string for display
                "path": str(file_path)
            })

        # Sort by created date (most recent first), putting None values last
        from datetime import datetime, timezone
        def sort_key(x):
            dt = x["created"]
            if dt is None:
                return datetime.min.replace(tzinfo=timezone.utc)
            # Ensure consistent timezone awareness
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
            # Extract frontmatter
            frontmatter = {}
            if content.startswith("---"):
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    try:
                        frontmatter = yaml.safe_load(parts[1]) or {}
                    except yaml.YAMLError:
                        pass

            title = frontmatter.get("title", file_path.stem.replace('_', ' ').replace('-', ' '))
            created = frontmatter.get("created", "")

            files.append({
                "name": title,
                "created": created
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
            frontmatter = {}
            if content.startswith("---"):
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    try:
                        frontmatter = yaml.safe_load(parts[1]) or {}
                    except yaml.YAMLError:
                        pass

            title = frontmatter.get("title", file_path.stem.replace('_', ' ').replace('-', ' '))

            files.append({
                "name": title
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
            frontmatter = {}
            if content.startswith("---"):
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    try:
                        frontmatter = yaml.safe_load(parts[1]) or {}
                    except yaml.YAMLError:
                        pass

            title = frontmatter.get("title", file_path.stem.replace('_', ' ').replace('-', ' '))

            files.append({
                "name": title
            })

        return files

    def get_social_metrics(self) -> Dict[str, int]:
        """Get social media metrics from logs and MCP interactions."""
        # For now, we'll return placeholder values - in production, this would
        # connect to MCP servers to get real data
        metrics = {
            "emails_sent": 0,
            "whatsapp_messages": 0,
            "linkedin_posts": 0,
            "facebook_posts": 0,
            "instagram_posts": 0,
            "twitter_posts": 0
        }

        # Count from logs
        logs_path = self.vault_path / "Logs"
        if logs_path.exists():
            log_files = list(logs_path.glob("*.json"))
            for log_file in log_files[-7:]:  # Last 7 days
                try:
                    content = log_file.read_text()
                    entries = json.loads(content)

                    for entry in entries:
                        action_type = entry.get("action_type", "")
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
                except (json.JSONDecodeError, KeyError):
                    continue

        return metrics

    def update_dashboard(self):
        """Update the Dashboard.md file with current metrics."""
        # Get current counts
        inbox_count = self.count_files("Inbox")
        needs_action_count = self.count_files("Needs_Action")
        pending_count = self.count_files("Pending_Approval")
        done_count = self.count_files("Done")

        # Get recent completed tasks
        recent_done = self.get_recent_done_tasks(5)

        # Get pending approval tasks
        pending_tasks = self.get_pending_approval_tasks()

        # Get needs action tasks
        needs_action_tasks = self.get_needs_action_tasks()

        # Get inbox tasks
        inbox_tasks = self.get_inbox_tasks()

        # Get social metrics
        social_metrics = self.get_social_metrics()

        # Calculate tasks completed today
        today = datetime.now().date()
        tasks_completed_today = 0
        for task in recent_done:
            if task['created'] and hasattr(task['created'], 'date') and task['created'].date() == today:
                tasks_completed_today += 1
            elif task['created_str']:  # If we have a string representation
                try:
                    task_str = str(task['created_str'])
                    if task_str.endswith('Z'):
                        task_str = task_str[:-1] + '+00:00'
                    task_date = datetime.fromisoformat(task_str).date()
                    if task_date == today:
                        tasks_completed_today += 1
                except ValueError:
                    try:
                        task_date = datetime.strptime(str(task['created_str']), '%Y-%m-%d').date()
                        if task_date == today:
                            tasks_completed_today += 1
                    except ValueError:
                        pass

        # Create the dashboard content
        dashboard_content = f"""# Digital FTE Dashboard

> Last Updated: {datetime.now().strftime('%Y-%m-%d')}

---

## System Status

| Component | Status | Notes |
|-----------|--------|-------|
| Vault | Active | {self.vault_path.name} |
| File Watcher | {"Running" if self._is_watcher_running('file') else "Stopped"} | Check with `./scripts/run_watchers.sh` |
| Backend API | {"Running" if self._is_service_running('backend') else "Stopped"} | Start with `./scripts/run_backend.sh` |
| Gmail MCP | {"Configured" if os.getenv('GMAIL_CREDENTIALS') else "Not Configured"} | OAuth token required |
| WhatsApp MCP | {"Configured" if os.getenv('WHATSAPP_SESSION_PATH') else "Not Configured"} | QR scan required |
| LinkedIn MCP | {"Configured" if os.getenv('LINKEDIN_ACCESS_TOKEN') else "Not Configured"} | Token configured |

**Mode:** `DRY_RUN={'true' if os.getenv('DRY_RUN', '').lower() == 'true' else 'false'}` ({'Safe mode - no real actions' if os.getenv('DRY_RUN', '').lower() == 'true' else 'Live mode - real actions'})

---

## Today's Tasks

### Inbox (New)
<!-- Tasks in Inbox/ folder appear here -->
{f"_Found {len(inbox_tasks)} new tasks_" if inbox_tasks else "_No new tasks_"}

{chr(10).join([f"- {task['name']}" for task in inbox_tasks[:3]])}

### Needs Action (In Progress)
<!-- Tasks in Needs_Action/ folder appear here -->
{f"_Found {len(needs_action_tasks)} tasks in progress_" if needs_action_tasks else "_No tasks in progress_"}

{chr(10).join([f"- {task['name']}" for task in needs_action_tasks[:3]])}

---

## Pending Approval

<!-- Tasks in Pending_Approval/ folder appear here -->
{f"_Found {len(pending_tasks)} items awaiting approval_" if pending_tasks else "_No items awaiting approval_"}

{chr(10).join([f"- {task['name']} ({task['created_str'] if 'created_str' in task else task['created']})" for task in pending_tasks[:3]])}

**To approve:** Move task file from `Pending_Approval/` to `Approved/`

---

## Recently Completed

<!-- Tasks in Done/ folder appear here -->
{f"_Found {len(recent_done)} recently completed tasks_" if recent_done else "_No completed tasks yet_"}

{chr(10).join([f"- [{recent_done[i]['created_str'] if recent_done[i]['created_str'] else recent_done[i]['created']}] {recent_done[i]['name']}" for i in range(min(5, len(recent_done)))])}

---

## Quick Actions

- **Add new task:** Create `.md` file in `Inbox/`
- **View logs:** Check `Logs/` folder
- **View plans:** Check `Plans/` folder
- **Approve action:** Move file from `Pending_Approval/` to `Approved/`

---

## Metrics

| Metric | Value |
|--------|-------|
| Tasks Completed Today | {tasks_completed_today} |
| Tasks Pending | {needs_action_count} |
| Actions Awaiting Approval | {pending_count} |
| Emails Sent | {social_metrics['emails_sent']} |
| WhatsApp Messages | {social_metrics['whatsapp_messages']} |
| LinkedIn Posts | {social_metrics['linkedin_posts']} |
| Facebook Posts | {social_metrics['facebook_posts']} |
| Instagram Posts | {social_metrics['instagram_posts']} |
| Twitter Posts | {social_metrics['twitter_posts']} |

---

## Notes

This dashboard provides an overview of the Digital FTE system status.

For detailed operational rules, see [[Company_Handbook]].
"""

        # Write the updated dashboard
        self.dashboard_path.write_text(dashboard_content)

    def _is_watcher_running(self, watcher_name: str) -> bool:
        """Check if a specific watcher is running."""
        # This is a simplified check - in production, you'd check actual process status
        # For now, we'll return False since we don't have a real process checker
        return False

    def _is_service_running(self, service_name: str) -> bool:
        """Check if a specific service is running."""
        # This is a simplified check - in production, you'd check actual process status
        return False


def update_dashboard_now():
    """Convenience function to update dashboard immediately."""
    vault_path = Path(os.getenv("VAULT_PATH", "./AI_Employee_Vault"))
    updater = DashboardUpdater(vault_path)
    updater.update_dashboard()


if __name__ == "__main__":
    update_dashboard_now()