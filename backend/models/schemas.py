"""Pydantic models for API schemas."""

from datetime import datetime
from enum import Enum
from typing import Optional, Any

from pydantic import BaseModel, Field


class SystemStatus(str, Enum):
    """System status states."""
    RUNNING = "running"
    STOPPED = "stopped"
    ERROR = "error"


class WatcherStatus(str, Enum):
    """Watcher status states."""
    RUNNING = "running"
    STOPPED = "stopped"
    ERROR = "error"


class PlatformHealth(str, Enum):
    """Platform health states."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class RalphLoopStatus(str, Enum):
    """Ralph Wiggum loop status."""
    STOPPED = "stopped"
    RUNNING = "running"
    PAUSED = "paused"
    PROCESSING = "processing"
    ERROR = "error"
    AWAITING_APPROVAL = "awaiting_approval"


class AuditLevel(str, Enum):
    """Audit log levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class TaskStatus(str, Enum):
    """Task status states."""
    NEW = "new"
    PROCESSING = "processing"
    AWAITING_APPROVAL = "awaiting_approval"
    APPROVED = "approved"
    COMPLETED = "completed"


class TaskPriority(str, Enum):
    """Task priority levels."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


# Response Models

class StatusResponse(BaseModel):
    """System status response."""
    system: SystemStatus
    watchers: dict[str, WatcherStatus]
    pending_approvals: int
    inbox_count: int
    needs_action_count: int
    timestamp: datetime = Field(default_factory=datetime.now)


class WatcherInfo(BaseModel):
    """Watcher information."""
    name: str
    status: WatcherStatus
    last_event: Optional[datetime] = None
    events_today: int = 0


class WatcherResponse(BaseModel):
    """Watcher operation response."""
    name: str
    status: WatcherStatus
    message: str


class TaskFile(BaseModel):
    """Task file information."""
    filename: str
    path: str
    folder: str
    created: Optional[datetime] = None
    priority: TaskPriority = TaskPriority.MEDIUM
    status: TaskStatus = TaskStatus.NEW
    title: Optional[str] = None


class VaultFolderResponse(BaseModel):
    """Vault folder contents response."""
    folder: str
    files: list[TaskFile]
    count: int


class TaskContent(BaseModel):
    """Full task content."""
    filename: str
    folder: str
    content: str
    frontmatter: dict
    body: str


# Request Models

class CreateTaskRequest(BaseModel):
    """Request to create a new task."""
    title: str
    description: str
    priority: TaskPriority = TaskPriority.MEDIUM
    tags: list[str] = Field(default_factory=list)


class MoveTaskRequest(BaseModel):
    """Request to move a task."""
    filename: str
    source_folder: str
    destination_folder: str
    notes: Optional[str] = None


class ApprovalRequest(BaseModel):
    """Request to approve/reject a pending action."""
    filename: str
    approved: bool
    notes: Optional[str] = None


class ApprovalResponse(BaseModel):
    """Approval operation response."""
    filename: str
    approved: bool
    new_location: str
    message: str


# Event Models

class LogEntry(BaseModel):
    """Log entry."""
    timestamp: datetime
    watcher: str
    event: str
    details: dict = Field(default_factory=dict)


class ActivityFeedResponse(BaseModel):
    """Activity feed response."""
    entries: list[LogEntry]
    count: int


# Gold Tier Models

class PlatformStatus(BaseModel):
    """Status of a platform (Gmail, WhatsApp, LinkedIn)."""
    name: str
    health: PlatformHealth = PlatformHealth.UNKNOWN
    connected: bool = False
    last_sync: Optional[datetime] = None
    events_today: int = 0
    error_message: Optional[str] = None


class AuditEntry(BaseModel):
    """Audit log entry."""
    timestamp: datetime
    correlation_id: str
    action: str
    level: AuditLevel = AuditLevel.INFO
    platform: str
    actor: str = "system"
    details: dict = Field(default_factory=dict)
    task_id: Optional[str] = None
    file_path: Optional[str] = None
    duration_ms: Optional[int] = None


class AuditSearchRequest(BaseModel):
    """Request for searching audit logs."""
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    platform: Optional[str] = None
    action: Optional[str] = None
    correlation_id: Optional[str] = None
    limit: int = Field(default=100, ge=1, le=1000)


class AuditResponse(BaseModel):
    """Audit search response."""
    entries: list[AuditEntry]
    count: int
    filters: dict = Field(default_factory=dict)


class AuditStats(BaseModel):
    """Audit statistics."""
    total_entries: int = 0
    by_platform: dict[str, int] = Field(default_factory=dict)
    by_action: dict[str, int] = Field(default_factory=dict)
    by_level: dict[str, int] = Field(default_factory=dict)
    errors: int = 0
    warnings: int = 0


class RalphTaskStep(BaseModel):
    """A step in Ralph Wiggum task execution."""
    step_number: int
    action: str
    description: str
    result: Optional[str] = None
    duration_ms: Optional[int] = None


class RalphTask(BaseModel):
    """A task being processed by Ralph Wiggum."""
    task_id: str
    file_path: str
    title: str
    status: str = "pending"
    current_step: int = 0
    total_steps: int = 0
    steps: list[RalphTaskStep] = Field(default_factory=list)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None


class RalphStatusResponse(BaseModel):
    """Ralph Wiggum status response."""
    status: RalphLoopStatus
    current_task: Optional[RalphTask] = None
    tasks_completed: int = 0
    tasks_failed: int = 0
    steps_executed: int = 0
    started_at: Optional[datetime] = None
    last_activity: Optional[datetime] = None
    error_message: Optional[str] = None


class RalphGuardrails(BaseModel):
    """Ralph Wiggum guardrail settings."""
    max_steps_per_task: int = 50
    step_timeout_seconds: int = 300
    approval_checkpoint_interval: int = 10


class UnifiedActivityEvent(BaseModel):
    """Unified activity event from any platform."""
    timestamp: datetime
    platform: str
    event_type: str
    title: str
    details: dict = Field(default_factory=dict)
    correlation_id: Optional[str] = None
    icon: Optional[str] = None


class GoldStatusResponse(BaseModel):
    """Enhanced status response for Gold tier."""
    system: SystemStatus
    watchers: dict[str, WatcherStatus]
    platforms: list[PlatformStatus]
    ralph: RalphStatusResponse
    pending_approvals: int
    inbox_count: int
    needs_action_count: int
    audit_summary: AuditStats
    timestamp: datetime = Field(default_factory=datetime.now)
