"""Watchdog service for monitoring system health and preventing runaway processes."""

import json
import os
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field

from .audit_logger import get_audit_logger, AuditAction, AuditLevel

logger = logging.getLogger(__name__)


@dataclass
class HealthMetrics:
    """System health metrics snapshot."""
    timestamp: str
    ralph_status: str
    ralph_tasks_completed: int
    ralph_tasks_failed: int
    ralph_consecutive_failures: int
    pending_approvals: int
    needs_action_count: int
    error_count_last_hour: int
    is_healthy: bool
    alerts: list = field(default_factory=list)


class Watchdog:
    """Monitors system health and provides guardrails for autonomous operations."""

    # Thresholds
    MAX_CONSECUTIVE_FAILURES = 5
    MAX_ERRORS_PER_HOUR = 10
    MAX_PENDING_APPROVALS = 25
    MAX_NEEDS_ACTION = 30
    CHECK_INTERVAL_SECONDS = 30

    def __init__(self, vault_path: str):
        """Initialize the watchdog.

        Args:
            vault_path: Path to the vault directory
        """
        self.vault_path = Path(vault_path)
        self.audit = get_audit_logger()
        self._consecutive_failures = 0
        self._last_check = None
        self._ralph_paused_by_watchdog = False

    def _count_folder_files(self, folder: str) -> int:
        """Count markdown files in a vault folder."""
        folder_path = self.vault_path / folder
        if not folder_path.exists():
            return 0
        return len([f for f in folder_path.glob("*.md") if not f.name.startswith(".")])

    def _count_errors_last_hour(self) -> int:
        """Count errors in the last hour from audit logs."""
        logs_path = self.vault_path / "Audit"
        if not logs_path.exists():
            logs_path = self.vault_path / "Logs"

        if not logs_path.exists():
            return 0

        one_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)
        error_count = 0

        # Check today's log file
        today_log = logs_path / f"{datetime.now().strftime('%Y-%m-%d')}.json"
        if today_log.exists():
            try:
                entries = json.loads(today_log.read_text())
                if not isinstance(entries, list):
                    entries = [entries]

                for entry in entries:
                    timestamp_str = entry.get("timestamp", "")
                    level = entry.get("level", "").lower()

                    if level in ["error", "critical"]:
                        try:
                            entry_time = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                            if entry_time.tzinfo is None:
                                entry_time = entry_time.replace(tzinfo=timezone.utc)
                            if entry_time >= one_hour_ago:
                                error_count += 1
                        except ValueError:
                            pass
            except (json.JSONDecodeError, KeyError):
                pass

        return error_count

    def _get_ralph_status(self) -> dict:
        """Get current Ralph Wiggum status."""
        try:
            from .ralph_wiggum import get_ralph
            ralph = get_ralph()
            status = ralph.get_status()
            return status
        except Exception as e:
            logger.error(f"Error getting Ralph status: {e}")
            return {
                "status": "unknown",
                "tasks_completed": 0,
                "tasks_failed": 0
            }

    def check_health(self) -> HealthMetrics:
        """Perform a health check on the system.

        Returns:
            HealthMetrics with current system state
        """
        alerts = []
        is_healthy = True

        # Get Ralph status
        ralph_status = self._get_ralph_status()
        ralph_state = ralph_status.get("status", "unknown")
        tasks_completed = ralph_status.get("tasks_completed", 0)
        tasks_failed = ralph_status.get("tasks_failed", 0)

        # Track consecutive failures
        if ralph_state == "error":
            self._consecutive_failures += 1
        else:
            self._consecutive_failures = 0

        # Count vault items
        pending_approvals = self._count_folder_files("Pending_Approval")
        needs_action_count = self._count_folder_files("Needs_Action")

        # Count recent errors
        error_count = self._count_errors_last_hour()

        # Check thresholds and generate alerts
        if self._consecutive_failures >= self.MAX_CONSECUTIVE_FAILURES:
            is_healthy = False
            alerts.append({
                "level": "critical",
                "type": "consecutive_failures",
                "message": f"Ralph Wiggum has failed {self._consecutive_failures} times consecutively",
                "action": "auto_pause"
            })

        if error_count >= self.MAX_ERRORS_PER_HOUR:
            is_healthy = False
            alerts.append({
                "level": "critical",
                "type": "high_error_rate",
                "message": f"{error_count} errors in the last hour (threshold: {self.MAX_ERRORS_PER_HOUR})",
                "action": "investigate"
            })

        if pending_approvals >= self.MAX_PENDING_APPROVALS:
            alerts.append({
                "level": "warning",
                "type": "approval_backlog",
                "message": f"{pending_approvals} pending approvals (threshold: {self.MAX_PENDING_APPROVALS})",
                "action": "pause_intake"
            })

        if needs_action_count >= self.MAX_NEEDS_ACTION:
            alerts.append({
                "level": "warning",
                "type": "task_overflow",
                "message": f"{needs_action_count} tasks in Needs_Action (threshold: {self.MAX_NEEDS_ACTION})",
                "action": "pause_intake"
            })

        metrics = HealthMetrics(
            timestamp=datetime.now(timezone.utc).isoformat(),
            ralph_status=ralph_state,
            ralph_tasks_completed=tasks_completed,
            ralph_tasks_failed=tasks_failed,
            ralph_consecutive_failures=self._consecutive_failures,
            pending_approvals=pending_approvals,
            needs_action_count=needs_action_count,
            error_count_last_hour=error_count,
            is_healthy=is_healthy,
            alerts=alerts
        )

        self._last_check = metrics
        return metrics

    async def enforce_guardrails(self, metrics: HealthMetrics) -> list:
        """Enforce guardrails based on health metrics.

        Args:
            metrics: Current health metrics

        Returns:
            List of actions taken
        """
        actions_taken = []

        for alert in metrics.alerts:
            if alert.get("action") == "auto_pause" and not self._ralph_paused_by_watchdog:
                # Auto-pause Ralph Wiggum
                try:
                    from .ralph_wiggum import get_ralph
                    ralph = get_ralph()
                    await ralph.pause()
                    self._ralph_paused_by_watchdog = True

                    actions_taken.append({
                        "action": "ralph_paused",
                        "reason": alert["message"],
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    })

                    self.audit.log(
                        AuditAction.RALPH_PAUSED,
                        platform="watchdog",
                        actor="watchdog",
                        level=AuditLevel.WARNING,
                        details={
                            "reason": alert["message"],
                            "action": "auto_pause"
                        }
                    )

                    logger.warning(f"Watchdog paused Ralph Wiggum: {alert['message']}")

                except Exception as e:
                    logger.error(f"Error pausing Ralph: {e}")

        # Log health check
        self.audit.log(
            AuditAction.INFO,
            platform="watchdog",
            actor="watchdog",
            level=AuditLevel.WARNING if not metrics.is_healthy else AuditLevel.INFO,
            details={
                "is_healthy": metrics.is_healthy,
                "alert_count": len(metrics.alerts),
                "actions_taken": len(actions_taken)
            }
        )

        return actions_taken

    def get_status(self) -> dict:
        """Get current watchdog status.

        Returns:
            Dict with watchdog status and last metrics
        """
        return {
            "running": True,
            "check_interval_seconds": self.CHECK_INTERVAL_SECONDS,
            "ralph_paused_by_watchdog": self._ralph_paused_by_watchdog,
            "consecutive_failures": self._consecutive_failures,
            "last_check": self._last_check.timestamp if self._last_check else None,
            "thresholds": {
                "max_consecutive_failures": self.MAX_CONSECUTIVE_FAILURES,
                "max_errors_per_hour": self.MAX_ERRORS_PER_HOUR,
                "max_pending_approvals": self.MAX_PENDING_APPROVALS,
                "max_needs_action": self.MAX_NEEDS_ACTION
            }
        }

    def reset_ralph_pause(self):
        """Reset the Ralph pause flag (after manual intervention)."""
        self._ralph_paused_by_watchdog = False
        self._consecutive_failures = 0
        logger.info("Watchdog Ralph pause flag reset")


# Global watchdog instance
_watchdog: Optional[Watchdog] = None


def get_watchdog() -> Watchdog:
    """Get or create the global watchdog instance."""
    global _watchdog
    if _watchdog is None:
        vault_path = os.getenv("VAULT_PATH", "./AI_Employee_Vault")
        _watchdog = Watchdog(vault_path)
    return _watchdog


def run_watchdog_check():
    """Run a watchdog health check (called by scheduler)."""
    import asyncio

    watchdog = get_watchdog()
    metrics = watchdog.check_health()

    # Run async enforcement in sync context
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(watchdog.enforce_guardrails(metrics))
    finally:
        loop.close()

    # Log summary
    if not metrics.is_healthy:
        logger.warning(f"Watchdog health check: UNHEALTHY - {len(metrics.alerts)} alerts")
    else:
        logger.debug("Watchdog health check: healthy")
