"""Audit log API endpoints."""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Query

from ..services.audit_logger import get_audit_logger, AuditAction

router = APIRouter()


@router.get("")
async def get_audit_entries(
    limit: int = Query(50, ge=1, le=500),
    platform: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    correlation_id: Optional[str] = Query(None),
    days: int = Query(7, ge=1, le=90)
):
    """Get audit log entries.

    Args:
        limit: Maximum entries to return
        platform: Filter by platform (gmail, whatsapp, linkedin, ralph, system)
        action: Filter by action type
        correlation_id: Filter by correlation ID
        days: Number of days to search

    Returns:
        List of audit entries
    """
    audit_logger = get_audit_logger()

    start_date = datetime.now().replace(hour=0, minute=0, second=0)
    start_date = start_date - __import__("datetime").timedelta(days=days)

    action_enum = None
    if action:
        try:
            action_enum = AuditAction(action)
        except ValueError:
            pass

    entries = audit_logger.search(
        start_date=start_date,
        platform=platform,
        action=action_enum,
        correlation_id=correlation_id,
        limit=limit
    )

    return {
        "entries": entries,
        "count": len(entries),
        "filters": {
            "platform": platform,
            "action": action,
            "correlation_id": correlation_id,
            "days": days
        }
    }


@router.get("/recent")
async def get_recent_audit():
    """Get recent audit entries from memory buffer."""
    audit_logger = get_audit_logger()
    entries = audit_logger.get_recent(limit=50)

    return {
        "entries": [e.to_dict() for e in entries],
        "count": len(entries)
    }


@router.get("/stats")
async def get_audit_stats(days: int = Query(7, ge=1, le=90)):
    """Get audit statistics.

    Args:
        days: Number of days to analyze

    Returns:
        Statistics dictionary
    """
    audit_logger = get_audit_logger()
    stats = audit_logger.get_stats(days=days)

    return {
        "stats": stats,
        "period_days": days
    }


@router.get("/actions")
async def get_audit_actions():
    """Get list of available audit actions."""
    return {
        "actions": [action.value for action in AuditAction]
    }


@router.get("/platforms")
async def get_audit_platforms():
    """Get list of known platforms."""
    return {
        "platforms": [
            "gmail",
            "whatsapp",
            "linkedin",
            "system",
            "ralph",
            "file_watcher",
            "orchestrator"
        ]
    }


@router.get("/analytics")
async def get_audit_analytics(days: int = Query(30, ge=1, le=365)):
    """Get advanced audit analytics.

    Args:
        days: Number of days to analyze (default 30, max 365)

    Returns:
        Analytics dictionary with patterns and insights
    """
    audit_logger = get_audit_logger()
    analytics = audit_logger.get_analytics(days=days)

    return {
        "analytics": analytics,
        "period_days": days
    }
