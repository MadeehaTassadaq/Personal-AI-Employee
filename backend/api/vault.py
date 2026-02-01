"""Vault access API endpoints."""

import os
import re
import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional

import yaml
from fastapi import APIRouter, HTTPException

from ..models.schemas import (
    TaskFile,
    TaskContent,
    VaultFolderResponse,
    TaskPriority,
    TaskStatus,
    CreateTaskRequest,
    MoveTaskRequest,
    LogEntry,
    ActivityFeedResponse
)

router = APIRouter()

VAULT_PATH = Path(os.getenv("VAULT_PATH", "./vault"))
VALID_FOLDERS = ["Inbox", "Needs_Action", "Pending_Approval", "Approved", "Done", "Plans"]


def parse_frontmatter(content: str) -> tuple[dict, str]:
    """Parse YAML frontmatter from markdown content."""
    frontmatter = {}
    body = content

    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            try:
                frontmatter = yaml.safe_load(parts[1]) or {}
            except yaml.YAMLError:
                frontmatter = {}
            body = parts[2].strip()

    return frontmatter, body


def get_task_info(file_path: Path) -> TaskFile:
    """Get task info from a markdown file."""
    content = file_path.read_text()
    frontmatter, body = parse_frontmatter(content)

    # Extract title from first heading or filename
    title = None
    title_match = re.search(r'^#\s+(.+)$', body, re.MULTILINE)
    if title_match:
        title = title_match.group(1)

    # Parse dates
    created = None
    if "created" in frontmatter:
        try:
            date_val = frontmatter["created"]
            if isinstance(date_val, datetime):
                created = date_val
            else:
                date_str = str(date_val)
                if date_str.endswith('Z'):
                    date_str = date_str[:-1] + '+00:00'
                created = datetime.fromisoformat(date_str)
        except (ValueError, TypeError):
            pass

    # Parse priority
    priority = TaskPriority.MEDIUM
    if "priority" in frontmatter:
        try:
            priority = TaskPriority(frontmatter["priority"])
        except ValueError:
            pass

    # Parse status
    status = TaskStatus.NEW
    if "status" in frontmatter:
        status_map = {
            "new": TaskStatus.NEW,
            "pending": TaskStatus.NEW,
            "processing": TaskStatus.PROCESSING,
            "awaiting_approval": TaskStatus.AWAITING_APPROVAL,
            "pending_approval": TaskStatus.AWAITING_APPROVAL,
            "approved": TaskStatus.APPROVED,
            "completed": TaskStatus.COMPLETED,
            "done": TaskStatus.COMPLETED
        }
        status = status_map.get(frontmatter["status"], TaskStatus.NEW)

    return TaskFile(
        filename=file_path.name,
        path=str(file_path),
        folder=file_path.parent.name,
        created=created,
        priority=priority,
        status=status,
        title=title
    )


@router.get("/folders")
async def list_folders() -> list[str]:
    """List available vault folders."""
    return VALID_FOLDERS


@router.get("/folder/{folder_name}")
async def list_folder_contents(folder_name: str) -> VaultFolderResponse:
    """List contents of a vault folder."""
    if folder_name not in VALID_FOLDERS:
        raise HTTPException(status_code=404, detail=f"Folder '{folder_name}' not found")

    folder_path = VAULT_PATH / folder_name
    if not folder_path.exists():
        return VaultFolderResponse(folder=folder_name, files=[], count=0)

    files = []
    for file_path in folder_path.glob("*.md"):
        if file_path.name == ".gitkeep":
            continue
        try:
            files.append(get_task_info(file_path))
        except Exception as e:
            # Log error but continue
            print(f"Error reading {file_path}: {e}")

    # Sort by created date (newest first), handling timezone-aware dates
    def sort_key(f):
        if f.created is None:
            return datetime.min.replace(tzinfo=timezone.utc)
        if f.created.tzinfo is None:
            return f.created.replace(tzinfo=timezone.utc)
        return f.created

    files.sort(key=sort_key, reverse=True)

    return VaultFolderResponse(folder=folder_name, files=files, count=len(files))


@router.get("/task/{folder_name}/{filename}")
async def get_task(folder_name: str, filename: str) -> TaskContent:
    """Get full task content."""
    if folder_name not in VALID_FOLDERS:
        raise HTTPException(status_code=404, detail=f"Folder '{folder_name}' not found")

    file_path = VAULT_PATH / folder_name / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"Task '{filename}' not found")

    content = file_path.read_text()
    frontmatter, body = parse_frontmatter(content)

    return TaskContent(
        filename=filename,
        folder=folder_name,
        content=content,
        frontmatter=frontmatter,
        body=body
    )


@router.post("/task")
async def create_task(request: CreateTaskRequest) -> TaskFile:
    """Create a new task in Inbox."""
    # Create slug from title
    slug = request.title.lower().replace(" ", "-").replace("_", "-")
    slug = "".join(c for c in slug if c.isalnum() or c == "-")
    slug = slug[:50]  # Limit length

    # Create filename
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    filename = f"{timestamp}-{slug}.md"

    # Build frontmatter
    frontmatter = {
        "created": datetime.now().isoformat(),
        "priority": request.priority.value,
        "status": "new",
        "tags": request.tags
    }

    # Build content
    content = f"""---
created: {frontmatter['created']}
priority: {frontmatter['priority']}
status: {frontmatter['status']}
tags: {json.dumps(request.tags)}
---

# {request.title}

## Description
{request.description}

## Action Items
- [ ] Review task
- [ ] Complete required action

## Notes
<!-- AI processing notes go here -->
"""

    # Write file
    file_path = VAULT_PATH / "Inbox" / filename
    file_path.write_text(content)

    return get_task_info(file_path)


@router.post("/task/move")
async def move_task(request: MoveTaskRequest) -> TaskFile:
    """Move a task between folders."""
    if request.source_folder not in VALID_FOLDERS:
        raise HTTPException(status_code=404, detail=f"Source folder '{request.source_folder}' not found")
    if request.destination_folder not in VALID_FOLDERS:
        raise HTTPException(status_code=404, detail=f"Destination folder '{request.destination_folder}' not found")

    source_path = VAULT_PATH / request.source_folder / request.filename
    if not source_path.exists():
        raise HTTPException(status_code=404, detail=f"Task '{request.filename}' not found")

    # Read and update content
    content = source_path.read_text()
    frontmatter, body = parse_frontmatter(content)

    # Update status based on destination
    status_map = {
        "Inbox": "new",
        "Needs_Action": "processing",
        "Pending_Approval": "awaiting_approval",
        "Approved": "approved",
        "Done": "completed"
    }
    frontmatter["status"] = status_map.get(request.destination_folder, "processing")
    frontmatter["moved_at"] = datetime.now().isoformat()

    # Add move notes if provided
    if request.notes:
        body += f"\n\n## Move Notes ({datetime.now().strftime('%Y-%m-%d %H:%M')})\n{request.notes}\n"

    # Rebuild content
    new_content = f"---\n{yaml.dump(frontmatter, default_flow_style=False)}---\n\n{body}"

    # Move file
    dest_path = VAULT_PATH / request.destination_folder / request.filename
    dest_path.write_text(new_content)
    source_path.unlink()

    return get_task_info(dest_path)


@router.get("/activity")
async def get_activity_feed(limit: int = 50) -> ActivityFeedResponse:
    """Get recent activity from logs."""
    logs_dir = VAULT_PATH / "Logs"
    if not logs_dir.exists():
        return ActivityFeedResponse(entries=[], count=0)

    all_entries = []

    # Read recent log files
    log_files = sorted(logs_dir.glob("*.json"), reverse=True)[:7]  # Last 7 days

    for log_file in log_files:
        try:
            entries = json.loads(log_file.read_text())
            for entry in entries:
                all_entries.append(LogEntry(
                    timestamp=datetime.fromisoformat(entry["timestamp"]),
                    watcher=entry.get("watcher", "Unknown"),
                    event=entry.get("event", "unknown"),
                    details={k: v for k, v in entry.items() if k not in ["timestamp", "watcher", "event"]}
                ))
        except (json.JSONDecodeError, KeyError):
            continue

    # Sort by timestamp and limit
    all_entries.sort(key=lambda e: e.timestamp, reverse=True)
    all_entries = all_entries[:limit]

    return ActivityFeedResponse(entries=all_entries, count=len(all_entries))
