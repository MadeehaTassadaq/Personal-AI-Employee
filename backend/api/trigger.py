"""API endpoints for trigger operations."""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any

from ..services.orchestrator import get_orchestrator
from ..services.claude_trigger import get_claude_trigger
from ..services.audit_logger import get_audit_logger, AuditAction

router = APIRouter(prefix="/api/trigger", tags=["Trigger"])

@router.post("/process-inbox")
async def trigger_process_inbox() -> Dict[str, Any]:
    """Trigger manual processing of the inbox folder.

    This endpoint moves all files from the Inbox folder to the Needs_Action folder,
    allowing the system to process new tasks manually without waiting for scheduled triggers.
    """
    try:
        # Get orchestrator instance
        orchestrator = get_orchestrator()

        # Process the inbox (move files from Inbox to Needs_Action)
        processed_files = orchestrator.process_inbox()

        # Log the action
        audit_logger = get_audit_logger()
        audit_logger.log(
            AuditAction.TASK_PROCESS,
            platform="orchestrator",
            actor="user",
            details={
                "action": "manual_inbox_processing",
                "processed_count": len(processed_files),
                "files": processed_files
            }
        )

        return {
            "success": True,
            "processed_count": len(processed_files),
            "processed_files": processed_files,
            "message": f"Successfully processed {len(processed_files)} files from inbox"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process inbox: {str(e)}")


@router.post("/claude-process-inbox")
async def trigger_claude_process_inbox() -> Dict[str, Any]:
    """Trigger Claude to process all inbox items.

    This endpoint uses Claude Code to process all files in the inbox folder,
    following the defined task processing workflow.
    """
    try:
        # Get Claude trigger instance
        claude_trigger = get_claude_trigger()

        # Trigger Claude to process inbox
        result = claude_trigger.trigger_inbox_processing()

        # Log the action
        audit_logger = get_audit_logger()
        audit_logger.log(
            AuditAction.TASK_PROCESS,
            platform="claude",
            actor="user",
            details={
                "action": "claude_inbox_processing",
                "processed_count": result.get("processed", 0),
                "successful_count": result.get("successful", 0)
            }
        )

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to trigger Claude processing: {str(e)}")


@router.post("/weekly-briefing")
async def trigger_weekly_briefing() -> Dict[str, Any]:
    """Trigger generation of weekly CEO briefing.

    This endpoint uses Claude Code to generate the weekly CEO briefing report.
    """
    try:
        # Get Claude trigger instance
        claude_trigger = get_claude_trigger()

        # Trigger weekly briefing generation
        result = claude_trigger.trigger_weekly_briefing()

        # Log the action
        audit_logger = get_audit_logger()
        audit_logger.log(
            AuditAction.REPORT_GENERATE,
            platform="claude",
            actor="user",
            details={
                "action": "weekly_briefing_generation",
                "success": result.get("success", False)
            }
        )

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to trigger weekly briefing: {str(e)}")