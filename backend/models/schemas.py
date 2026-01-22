"""Pydantic models for API schemas."""

from datetime import datetime
from enum import Enum
from typing import Optional

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
