"""Approval workflow API endpoints."""

import os
import json
from pathlib import Path
from datetime import datetime
from typing import Optional

import yaml
from fastapi import APIRouter, HTTPException

from ..models.schemas import (
    TaskFile,
    ApprovalRequest,
    ApprovalResponse,
    VaultFolderResponse
)

router = APIRouter()

VAULT_PATH = Path(os.getenv("VAULT_PATH", "./vault"))


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


def log_approval(filename: str, approved: bool, notes: Optional[str]) -> None:
    """Log an approval action."""
    log_file = VAULT_PATH / "Logs" / f"{datetime.now().strftime('%Y-%m-%d')}.json"

    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "watcher": "ApprovalSystem",
        "event": "approval_granted" if approved else "approval_rejected",
        "file": filename,
        "notes": notes
    }

    logs = []
    if log_file.exists():
        try:
            logs = json.loads(log_file.read_text())
        except json.JSONDecodeError:
            logs = []

    logs.append(log_entry)
    log_file.write_text(json.dumps(logs, indent=2))


@router.get("/pending")
async def list_pending_approvals() -> VaultFolderResponse:
    """List all pending approval requests."""
    folder_path = VAULT_PATH / "Pending_Approval"
    if not folder_path.exists():
        return VaultFolderResponse(folder="Pending_Approval", files=[], count=0)

    files = []
    for file_path in folder_path.glob("*.md"):
        if file_path.name == ".gitkeep":
            continue

        content = file_path.read_text()
        frontmatter, body = parse_frontmatter(content)

        # Get action type from frontmatter
        action_type = frontmatter.get("type", "unknown")

        created_datetime = None
        if "created" in frontmatter:
            created_value = frontmatter["created"]
            if isinstance(created_value, str):
                try:
                    created_datetime = datetime.fromisoformat(created_value.replace('Z', '+00:00'))
                except ValueError:
                    # Handle other possible datetime formats
                    try:
                        created_datetime = datetime.fromisoformat(created_value)
                    except ValueError:
                        # If all parsing fails, set to None
                        created_datetime = None

        files.append(TaskFile(
            filename=file_path.name,
            path=str(file_path),
            folder="Pending_Approval",
            title=frontmatter.get("title", file_path.stem.replace("-", " ").title()),
            created=created_datetime
        ))

    # Sort by created date
    files.sort(key=lambda f: f.created or datetime.min, reverse=True)

    return VaultFolderResponse(folder="Pending_Approval", files=files, count=len(files))


@router.get("/pending/{filename}")
async def get_pending_approval(filename: str) -> dict:
    """Get details of a pending approval request."""
    file_path = VAULT_PATH / "Pending_Approval" / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"Approval request '{filename}' not found")

    content = file_path.read_text()
    frontmatter, body = parse_frontmatter(content)

    return {
        "filename": filename,
        "type": frontmatter.get("type", "unknown"),
        "created": frontmatter.get("created"),
        "frontmatter": frontmatter,
        "content": body
    }


@router.post("/approve")
async def approve_action(request: ApprovalRequest) -> ApprovalResponse:
    """Approve or reject an action."""
    source_path = VAULT_PATH / "Pending_Approval" / request.filename
    if not source_path.exists():
        raise HTTPException(status_code=404, detail=f"Approval request '{request.filename}' not found")

    # Read content
    content = source_path.read_text()
    frontmatter, body = parse_frontmatter(content)

    # Determine destination
    if request.approved:
        dest_folder = "Approved"
        frontmatter["status"] = "approved"
        frontmatter["approved_at"] = datetime.now().isoformat()
    else:
        dest_folder = "Done"  # Rejected items go to Done
        frontmatter["status"] = "rejected"
        frontmatter["rejected_at"] = datetime.now().isoformat()

    # Add approval notes
    if request.notes:
        frontmatter["approval_notes"] = request.notes
        body += f"\n\n## {'Approval' if request.approved else 'Rejection'} Notes\n{request.notes}\n"

    # Rebuild content
    new_content = f"---\n{yaml.dump(frontmatter, default_flow_style=False)}---\n\n{body}"

    # Move file
    dest_path = VAULT_PATH / dest_folder / request.filename
    dest_path.write_text(new_content)
    source_path.unlink()

    # Log the action
    log_approval(request.filename, request.approved, request.notes)

    return ApprovalResponse(
        filename=request.filename,
        approved=request.approved,
        new_location=str(dest_path),
        message=f"Action {'approved' if request.approved else 'rejected'}"
    )


@router.get("/approved")
async def list_approved_actions() -> VaultFolderResponse:
    """List approved actions ready for execution."""
    folder_path = VAULT_PATH / "Approved"
    if not folder_path.exists():
        return VaultFolderResponse(folder="Approved", files=[], count=0)

    files = []
    for file_path in folder_path.glob("*.md"):
        if file_path.name == ".gitkeep":
            continue

        content = file_path.read_text()
        frontmatter, body = parse_frontmatter(content)

        files.append(TaskFile(
            filename=file_path.name,
            path=str(file_path),
            folder="Approved",
            title=frontmatter.get("title", file_path.stem.replace("-", " ").title()),
            created=datetime.fromisoformat(frontmatter["approved_at"]) if "approved_at" in frontmatter else None
        ))

    return VaultFolderResponse(folder="Approved", files=files, count=len(files))


@router.post("/execute/{filename}")
async def mark_executed(filename: str, notes: Optional[str] = None) -> dict:
    """Mark an approved action as executed."""
    source_path = VAULT_PATH / "Approved" / filename
    if not source_path.exists():
        raise HTTPException(status_code=404, detail=f"Approved action '{filename}' not found")

    # Read and update content
    content = source_path.read_text()
    frontmatter, body = parse_frontmatter(content)

    frontmatter["status"] = "completed"
    frontmatter["executed_at"] = datetime.now().isoformat()

    if notes:
        body += f"\n\n## Execution Notes\n{notes}\n"

    # Rebuild content
    new_content = f"---\n{yaml.dump(frontmatter, default_flow_style=False)}---\n\n{body}"

    # Move to Done
    dest_path = VAULT_PATH / "Done" / filename
    dest_path.write_text(new_content)
    source_path.unlink()

    return {
        "filename": filename,
        "status": "completed",
        "new_location": str(dest_path)
    }
