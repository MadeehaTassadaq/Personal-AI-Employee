"""Comprehensive audit logging service with structured JSON and correlation IDs."""

import json
import logging
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Optional
from dataclasses import dataclass, field, asdict
from enum import Enum
from contextvars import ContextVar

logger = logging.getLogger(__name__)

# Context variable for correlation ID
_correlation_id: ContextVar[Optional[str]] = ContextVar("correlation_id", default=None)


class AuditAction(str, Enum):
    """Types of auditable actions."""
    # Task lifecycle
    TASK_CREATED = "task_created"
    TASK_MOVED = "task_moved"
    TASK_COMPLETED = "task_completed"
    TASK_DELETED = "task_deleted"

    # Approvals
    APPROVAL_REQUESTED = "approval_requested"
    APPROVAL_GRANTED = "approval_granted"
    APPROVAL_DENIED = "approval_denied"

    # External actions
    EMAIL_SENT = "email_sent"
    EMAIL_DRAFTED = "email_drafted"
    WHATSAPP_SENT = "whatsapp_sent"
    LINKEDIN_POSTED = "linkedin_posted"

    # System
    SYSTEM_START = "system_start"
    SYSTEM_STOP = "system_stop"
    WATCHER_START = "watcher_start"
    WATCHER_STOP = "watcher_stop"
    WATCHER_ERROR = "watcher_error"

    # Ralph Wiggum
    RALPH_TASK_START = "ralph_task_start"
    RALPH_STEP_COMPLETE = "ralph_step_complete"
    RALPH_TASK_COMPLETE = "ralph_task_complete"
    RALPH_ERROR = "ralph_error"
    RALPH_CHECKPOINT = "ralph_checkpoint"

    # Generic
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class AuditLevel(str, Enum):
    """Audit log levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class AuditEntry:
    """A single audit log entry."""
    timestamp: str
    correlation_id: str
    action: str
    level: str
    platform: str
    actor: str
    details: dict = field(default_factory=dict)
    task_id: Optional[str] = None
    file_path: Optional[str] = None
    duration_ms: Optional[int] = None

    def to_dict(self) -> dict:
        """Convert to dictionary, excluding None values."""
        result = asdict(self)
        return {k: v for k, v in result.items() if v is not None}


class AuditLogger:
    """Manages audit logging to structured JSON files."""

    def __init__(self, vault_path: str):
        """Initialize the audit logger.

        Args:
            vault_path: Path to the vault directory
        """
        self.vault_path = Path(vault_path)
        self.audit_path = self.vault_path / "Audit"
        self.audit_path.mkdir(parents=True, exist_ok=True)
        self._in_memory_buffer: list[AuditEntry] = []
        self._buffer_limit = 100

    def generate_correlation_id(self) -> str:
        """Generate a new correlation ID and set it in context."""
        correlation_id = str(uuid.uuid4())[:8]
        _correlation_id.set(correlation_id)
        return correlation_id

    def get_correlation_id(self) -> str:
        """Get current correlation ID or generate one."""
        current = _correlation_id.get()
        if current is None:
            return self.generate_correlation_id()
        return current

    def set_correlation_id(self, correlation_id: str) -> None:
        """Set the correlation ID for the current context."""
        _correlation_id.set(correlation_id)

    def log(
        self,
        action: AuditAction,
        platform: str,
        actor: str = "system",
        level: AuditLevel = AuditLevel.INFO,
        details: Optional[dict] = None,
        task_id: Optional[str] = None,
        file_path: Optional[str] = None,
        duration_ms: Optional[int] = None,
        correlation_id: Optional[str] = None
    ) -> AuditEntry:
        """Log an audit entry.

        Args:
            action: The action being logged
            platform: Platform (gmail, whatsapp, linkedin, system, ralph)
            actor: Who performed the action (system, user, ralph)
            level: Log level
            details: Additional details
            task_id: Associated task ID
            file_path: Associated file path
            duration_ms: Duration in milliseconds
            correlation_id: Correlation ID (uses context if not provided)

        Returns:
            The created audit entry
        """
        entry = AuditEntry(
            timestamp=datetime.now().isoformat(),
            correlation_id=correlation_id or self.get_correlation_id(),
            action=action.value,
            level=level.value,
            platform=platform,
            actor=actor,
            details=details or {},
            task_id=task_id,
            file_path=file_path,
            duration_ms=duration_ms
        )

        # Add to buffer
        self._in_memory_buffer.append(entry)

        # Write to file
        self._write_entry(entry)

        # Log to standard logger too
        log_msg = f"[AUDIT] [{entry.correlation_id}] {action.value} | {platform} | {actor}"
        if level == AuditLevel.ERROR or level == AuditLevel.CRITICAL:
            logger.error(log_msg)
        elif level == AuditLevel.WARNING:
            logger.warning(log_msg)
        else:
            logger.info(log_msg)

        # Trim buffer if needed
        if len(self._in_memory_buffer) > self._buffer_limit:
            self._in_memory_buffer = self._in_memory_buffer[-self._buffer_limit:]

        return entry

    def _write_entry(self, entry: AuditEntry) -> None:
        """Write an entry to the daily audit file."""
        date_str = datetime.now().strftime("%Y-%m-%d")
        audit_file = self.audit_path / f"{date_str}.json"

        entries = []
        if audit_file.exists():
            try:
                entries = json.loads(audit_file.read_text())
            except json.JSONDecodeError:
                entries = []

        entries.append(entry.to_dict())
        audit_file.write_text(json.dumps(entries, indent=2))

    def get_recent(self, limit: int = 50) -> list[AuditEntry]:
        """Get recent audit entries from memory buffer."""
        return list(reversed(self._in_memory_buffer[-limit:]))

    def search(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        platform: Optional[str] = None,
        action: Optional[AuditAction] = None,
        correlation_id: Optional[str] = None,
        limit: int = 100
    ) -> list[dict]:
        """Search audit entries.

        Args:
            start_date: Start of date range
            end_date: End of date range
            platform: Filter by platform
            action: Filter by action type
            correlation_id: Filter by correlation ID
            limit: Maximum entries to return

        Returns:
            List of matching audit entries
        """
        results = []

        # Default to last 7 days
        if start_date is None:
            start_date = datetime.now().replace(hour=0, minute=0, second=0) - \
                        __import__("datetime").timedelta(days=7)
        if end_date is None:
            end_date = datetime.now()

        # Iterate through date range
        current = start_date
        while current <= end_date and len(results) < limit:
            date_str = current.strftime("%Y-%m-%d")
            audit_file = self.audit_path / f"{date_str}.json"

            if audit_file.exists():
                try:
                    entries = json.loads(audit_file.read_text())
                    for entry in entries:
                        # Apply filters
                        if platform and entry.get("platform") != platform:
                            continue
                        if action and entry.get("action") != action.value:
                            continue
                        if correlation_id and entry.get("correlation_id") != correlation_id:
                            continue

                        results.append(entry)
                        if len(results) >= limit:
                            break
                except json.JSONDecodeError:
                    pass

            current += __import__("datetime").timedelta(days=1)

        return results

    def get_stats(self, days: int = 7) -> dict:
        """Get audit statistics for the last N days.

        Args:
            days: Number of days to analyze

        Returns:
            Statistics dictionary
        """
        stats = {
            "total_entries": 0,
            "by_platform": {},
            "by_action": {},
            "by_level": {},
            "by_actor": {},
            "errors": 0,
            "warnings": 0,
            "daily_counts": {},
            "trends": {}
        }

        start_date = datetime.now().replace(hour=0, minute=0, second=0) - \
                    __import__("datetime").timedelta(days=days)

        for entry in self.search(start_date=start_date, limit=10000):
            stats["total_entries"] += 1

            # Track platform usage
            platform = entry.get("platform", "unknown")
            stats["by_platform"][platform] = stats["by_platform"].get(platform, 0) + 1

            # Track action types
            action = entry.get("action", "unknown")
            stats["by_action"][action] = stats["by_action"].get(action, 0) + 1

            # Track log levels
            level = entry.get("level", "info")
            stats["by_level"][level] = stats["by_level"].get(level, 0) + 1

            # Track actors
            actor = entry.get("actor", "unknown")
            stats["by_actor"][actor] = stats["by_actor"].get(actor, 0) + 1

            # Count errors and warnings
            if level == "error" or level == "critical":
                stats["errors"] += 1
            elif level == "warning":
                stats["warnings"] += 1

            # Daily counts
            day_key = datetime.fromisoformat(entry.get("timestamp", "")).strftime("%Y-%m-%d") if entry.get("timestamp") else "unknown"
            stats["daily_counts"][day_key] = stats["daily_counts"].get(day_key, 0) + 1

        # Calculate trends
        if stats["daily_counts"]:
            dates = sorted(stats["daily_counts"].keys())
            if len(dates) > 1:
                recent_count = stats["daily_counts"][dates[-1]]
                prev_count = stats["daily_counts"][dates[-2]]

                if prev_count > 0:
                    change_pct = ((recent_count - prev_count) / prev_count) * 100
                    stats["trends"]["activity_change_pct"] = round(change_pct, 2)
                    stats["trends"]["direction"] = "increasing" if change_pct > 0 else "decreasing"
                else:
                    stats["trends"]["activity_change_pct"] = float('inf')
                    stats["trends"]["direction"] = "increasing"

        return stats

    def get_analytics(self, days: int = 30) -> dict:
        """Get advanced analytics for the last N days.

        Args:
            days: Number of days to analyze

        Returns:
            Analytics dictionary with patterns and insights
        """
        analytics = {
            "period_start": (datetime.now() - __import__("datetime").timedelta(days=days)).isoformat(),
            "period_end": datetime.now().isoformat(),
            "peak_activity_times": [],
            "platform_usage_patterns": {},
            "error_rate_by_platform": {},
            "task_completion_rates": {},
            "top_actions": [],
            "anomalies": []
        }

        start_date = datetime.now().replace(hour=0, minute=0, second=0) - \
                    __import__("datetime").timedelta(days=days)

        entries = self.search(start_date=start_date, limit=10000)

        # Group entries by hour for peak activity analysis
        hourly_counts = {}
        platform_errors = {}
        platform_total = {}

        for entry in entries:
            timestamp = datetime.fromisoformat(entry.get("timestamp", ""))
            hour = timestamp.hour

            # Count by hour
            hourly_counts[hour] = hourly_counts.get(hour, 0) + 1

            # Track errors by platform
            platform = entry.get("platform", "unknown")
            level = entry.get("level", "info")

            platform_total[platform] = platform_total.get(platform, 0) + 1

            if level in ["error", "critical"]:
                platform_errors[platform] = platform_errors.get(platform, 0) + 1

        # Find peak activity hours
        if hourly_counts:
            sorted_hours = sorted(hourly_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            analytics["peak_activity_times"] = [{"hour": h, "count": c} for h, c in sorted_hours]

        # Calculate error rates by platform
        for platform in platform_total:
            total = platform_total[platform]
            errors = platform_errors.get(platform, 0)
            error_rate = (errors / total) * 100 if total > 0 else 0
            analytics["error_rate_by_platform"][platform] = round(error_rate, 2)

        # Top actions
        action_counts = {}
        for entry in entries:
            action = entry.get("action", "unknown")
            action_counts[action] = action_counts.get(action, 0) + 1

        sorted_actions = sorted(action_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        analytics["top_actions"] = [{"action": a, "count": c} for a, c in sorted_actions]

        return analytics


# Global audit logger instance
_audit_logger: Optional[AuditLogger] = None


def get_audit_logger() -> AuditLogger:
    """Get or create the global audit logger instance."""
    global _audit_logger
    if _audit_logger is None:
        vault_path = os.getenv("VAULT_PATH", "./AI_Employee_Vault")
        _audit_logger = AuditLogger(vault_path)
    return _audit_logger


def audit(
    action: AuditAction,
    platform: str,
    **kwargs
) -> AuditEntry:
    """Convenience function to log an audit entry."""
    return get_audit_logger().log(action, platform, **kwargs)
