"""Claude Code trigger service for task processing."""

import os
import json
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Optional


class ClaudeTrigger:
    """Triggers Claude Code to process tasks."""

    def __init__(self, vault_path: str):
        """Initialize the Claude trigger.

        Args:
            vault_path: Path to the Obsidian vault
        """
        self.vault_path = Path(vault_path)
        self.dry_run = os.getenv("DRY_RUN", "true").lower() == "true"

    def trigger_task_processing(self, task_file: str) -> dict:
        """Trigger Claude to process a specific task.

        Args:
            task_file: Path to the task file

        Returns:
            Result of the trigger
        """
        task_path = Path(task_file)
        if not task_path.exists():
            return {"success": False, "error": f"Task file not found: {task_file}"}

        # Read task content
        task_content = task_path.read_text()

        # Build Claude prompt
        prompt = f"""
Context:
A new task requires processing. The task file is at: {task_path}

Task Content:
{task_content}

Objective:
1. Read and analyze the task
2. Determine the appropriate action
3. If action requires approval (email, message, post):
   - Create an approval request in vault/Pending_Approval/
4. If action is auto-approved:
   - Execute the action
   - Move task to vault/Done/
5. Update vault/Dashboard.md with status

Constraints:
- Use only defined Agent Skills (read .claude/skills/ first)
- Follow Company_Handbook.md rules
- Document your reasoning
- Check DRY_RUN flag before real actions
"""

        if self.dry_run:
            self._log_event("claude_trigger_dry_run", {
                "task_file": str(task_path),
                "prompt_length": len(prompt)
            })
            return {
                "success": True,
                "dry_run": True,
                "message": f"[DRY RUN] Would trigger Claude for: {task_path.name}"
            }

        try:
            # Execute Claude Code
            result = subprocess.run(
                ["claude", prompt],
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )

            self._log_event("claude_triggered", {
                "task_file": str(task_path),
                "exit_code": result.returncode,
                "stdout_length": len(result.stdout)
            })

            return {
                "success": result.returncode == 0,
                "output": result.stdout,
                "error": result.stderr if result.returncode != 0 else None
            }

        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Claude execution timed out"}
        except FileNotFoundError:
            return {"success": False, "error": "Claude CLI not found"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def trigger_inbox_processing(self) -> dict:
        """Trigger Claude to process all inbox items.

        Returns:
            Result of the trigger
        """
        inbox = self.vault_path / "Inbox"
        tasks = [f for f in inbox.glob("*.md") if f.name != ".gitkeep"]

        if not tasks:
            return {"success": True, "message": "No tasks in inbox", "processed": 0}

        results = []
        for task in tasks:
            result = self.trigger_task_processing(str(task))
            results.append({
                "task": task.name,
                "result": result
            })

        success_count = sum(1 for r in results if r["result"].get("success"))

        return {
            "success": True,
            "processed": len(results),
            "successful": success_count,
            "results": results
        }

    def trigger_weekly_briefing(self) -> dict:
        """Trigger Claude to generate weekly briefing.

        Returns:
            Result of the trigger
        """
        prompt = """
Context:
Generate the weekly CEO briefing.

Objective:
1. Read vault/Done/ for completed tasks this week
2. Read vault/Needs_Action/ for pending tasks
3. Read vault/Logs/ for activity summary
4. Generate briefing following skills/weekly_briefing.md format
5. Save to vault/Plans/weekly-briefing-{date}.md
6. Update Dashboard.md

Use the Weekly CEO Briefing skill.
"""

        if self.dry_run:
            self._log_event("briefing_trigger_dry_run", {})
            return {
                "success": True,
                "dry_run": True,
                "message": "[DRY RUN] Would trigger weekly briefing generation"
            }

        try:
            result = subprocess.run(
                ["claude", prompt],
                capture_output=True,
                text=True,
                timeout=300
            )

            self._log_event("briefing_triggered", {
                "exit_code": result.returncode
            })

            return {
                "success": result.returncode == 0,
                "output": result.stdout,
                "error": result.stderr if result.returncode != 0 else None
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _log_event(self, event_type: str, details: dict) -> None:
        """Log an event.

        Args:
            event_type: Type of event
            details: Event details
        """
        log_file = self.vault_path / "Logs" / f"{datetime.now().strftime('%Y-%m-%d')}.json"

        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "watcher": "ClaudeTrigger",
            "event": event_type,
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


# Singleton instance
_trigger: Optional[ClaudeTrigger] = None


def get_claude_trigger() -> ClaudeTrigger:
    """Get or create the Claude trigger instance."""
    global _trigger
    if _trigger is None:
        vault_path = os.getenv("VAULT_PATH", "./vault")
        _trigger = ClaudeTrigger(vault_path)
    return _trigger
