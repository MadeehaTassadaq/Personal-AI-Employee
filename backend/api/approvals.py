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
from ..services.publisher import get_publisher

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

    publish_result = None

    # Determine destination
    if request.approved:
        dest_folder = "Approved"
        frontmatter["status"] = "approved"
        frontmatter["approved_at"] = datetime.now().isoformat()

        # If this is a social post or whatsapp/email message, publish it immediately
        # Support both "social_post" and "social" types for backwards compatibility
        action_type = frontmatter.get("type", "")
        if action_type in ["social_post", "social", "whatsapp", "email"]:
            publisher = get_publisher()
            publish_result = await publisher.publish(source_path)
            publisher.log_publish_result(request.filename, publish_result)

            if publish_result.get("success"):
                frontmatter["published"] = True
                frontmatter["published_at"] = datetime.now().isoformat()
                if publish_result.get("post_id"):
                    frontmatter["post_id"] = publish_result.get("post_id")
                if publish_result.get("tweet_id"):
                    frontmatter["tweet_id"] = publish_result.get("tweet_id")
                if publish_result.get("media_id"):
                    frontmatter["media_id"] = publish_result.get("media_id")
                body += f"\n\n## Published\nSuccessfully published to {frontmatter.get('platform', 'platform')} at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                dest_folder = "Done"  # Move directly to Done if published
            else:
                frontmatter["publish_error"] = publish_result.get("error", "Unknown error")
                body += f"\n\n## Publish Error\n{publish_result.get('error', 'Unknown error')}\n"
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

    # Build response message
    message = f"Action {'approved' if request.approved else 'rejected'}"
    if publish_result:
        if publish_result.get("success"):
            message += f" and published to {frontmatter.get('platform', 'platform')}"
        else:
            message += f" but publishing failed: {publish_result.get('error', 'Unknown error')}"

    return ApprovalResponse(
        filename=request.filename,
        approved=request.approved,
        new_location=str(dest_path),
        message=message
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


@router.post("/publish/{filename}")
async def publish_approved(filename: str) -> dict:
    """Manually publish an approved post."""
    source_path = VAULT_PATH / "Approved" / filename
    if not source_path.exists():
        raise HTTPException(status_code=404, detail=f"Approved file '{filename}' not found")

    content = source_path.read_text()
    frontmatter, body = parse_frontmatter(content)

    # Support multiple action types
    action_type = frontmatter.get("type", "")
    if action_type not in ["social_post", "social", "whatsapp", "email"]:
        raise HTTPException(status_code=400, detail=f"This file type '{action_type}' cannot be published")

    publisher = get_publisher()
    result = await publisher.publish(source_path)
    publisher.log_publish_result(filename, result)

    if result.get("success"):
        # Update frontmatter and move to Done
        frontmatter["published"] = True
        frontmatter["published_at"] = datetime.now().isoformat()
        if result.get("post_id"):
            frontmatter["post_id"] = result.get("post_id")
        body += f"\n\n## Published\nSuccessfully published at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"

        new_content = f"---\n{yaml.dump(frontmatter, default_flow_style=False)}---\n\n{body}"

        dest_path = VAULT_PATH / "Done" / filename
        dest_path.write_text(new_content)
        source_path.unlink()

        return {
            "success": True,
            "message": f"Published to {frontmatter.get('platform')}",
            "new_location": str(dest_path)
        }
    else:
        return {
            "success": False,
            "error": result.get("error", "Unknown error"),
            "platform": result.get("platform")
        }


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


@router.post("/notify")
async def notify_pending_approvals() -> dict:
    """Send notifications for pending approvals.

    Returns a summary of pending approvals and their count.
    The dashboard can poll this endpoint or use it to trigger notifications.
    """
    folder_path = VAULT_PATH / "Pending_Approval"
    if not folder_path.exists():
        return {"count": 0, "items": [], "summary": "No pending approvals"}

    # Get all pending files
    pending_items = []
    for file_path in folder_path.glob("*.md"):
        if file_path.name == ".gitkeep":
            continue

        content = file_path.read_text()
        frontmatter, body = parse_frontmatter(content)

        action_type = frontmatter.get("type", "unknown")
        title = frontmatter.get("title", file_path.stem.replace("-", " ").title())
        priority = frontmatter.get("priority", "normal")
        platform = frontmatter.get("platform", "unknown")

        pending_items.append({
            "filename": file_path.name,
            "title": title,
            "type": action_type,
            "priority": priority,
            "platform": platform,
            "created": frontmatter.get("created", "")
        })

    # Sort by priority and created date
    priority_order = {"urgent": 0, "high": 1, "normal": 2, "low": 3}
    pending_items.sort(
        key=lambda x: (priority_order.get(x["priority"], 2), x.get("created", "")),
        reverse=False
    )

    # Build summary
    count = len(pending_items)
    summary_parts = []
    if count > 0:
        summary_parts.append(f"{count} pending approval(s)")
        type_counts = {}
        for item in pending_items:
            item_type = item["type"]
            type_counts[item_type] = type_counts.get(item_type, 0) + 1
        summary_parts.extend([f"{count} {t}" for t, count in type_counts.items()])

        # Count by priority
        urgent_count = sum(1 for i in pending_items if i["priority"] == "urgent")
        if urgent_count > 0:
            summary_parts.append(f"{urgent_count} urgent")

    return {
        "count": count,
        "items": pending_items,
        "summary": ", ".join(summary_parts) if summary_parts else "No pending approvals",
        "timestamp": datetime.now().isoformat()
    }


@router.get("/summary")
async def get_approval_summary() -> dict:
    """Get a summary of approval statistics.

    Returns counts of pending, approved, and completed items.
    """
    summary = {
        "pending": 0,
        "approved": 0,
        "completed": 0,
        "by_type": {},
        "by_platform": {}
    }

    # Check Pending_Approval
    for folder in ["Pending_Approval", "Approved"]:
        folder_path = VAULT_PATH / folder
        if folder_path.exists():
            count = len(list(folder_path.glob("*.md")))
            if folder == "Pending_Approval":
                summary["pending"] = count
            else:
                summary["approved"] = count

    # Check Done for completed today
    today = datetime.now().strftime("%Y-%m-%d")
    done_path = VAULT_PATH / "Done"
    if done_path.exists():
        for file_path in done_path.glob("*.md"):
            content = file_path.read_text()
            frontmatter, _ = parse_frontmatter(content)
            executed_at = frontmatter.get("executed_at", "")
            if executed_at and executed_at.startswith(today):
                summary["completed"] += 1

    return summary
