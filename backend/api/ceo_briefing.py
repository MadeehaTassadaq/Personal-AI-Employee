"""CEO Briefing API endpoints."""

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException

from ..services.audit_logger import get_audit_logger, AuditAction, AuditLevel
from ..services.ralph_wiggum import get_ralph

router = APIRouter()


@router.post("/generate")
async def generate_ceo_briefing():
    """Generate a CEO briefing report.

    Returns:
        Path to the generated report file
    """
    try:
        # Import and run the CEO briefing implementation
        import sys
        from pathlib import Path
        import os

        # Add the skills directory to the Python path
        skills_path = Path(os.getcwd()) / ".claude/skills/ceo-briefing-gold"
        sys.path.insert(0, str(skills_path))

        # Import the implementation
        from implementation import main
        report_path = main()

        if not report_path:
            raise HTTPException(status_code=500, detail="Failed to generate briefing")

        # Log the action
        audit_logger = get_audit_logger()
        audit_logger.log(
            AuditAction.INFO,
            platform="system",
            actor="ceo_briefing",
            details={
                "action": "briefing_generated",
                "report_path": report_path
            }
        )

        return {
            "message": "CEO briefing generated successfully",
            "report_path": report_path,
            "generated_at": datetime.now().isoformat()
        }
    except Exception as e:
        # Log the error
        audit_logger = get_audit_logger()
        audit_logger.log(
            AuditAction.ERROR,
            platform="system",
            level=AuditLevel.ERROR,
            actor="ceo_briefing",
            details={
                "action": "briefing_generation_failed",
                "error": str(e)
            }
        )

        raise HTTPException(status_code=500, detail=f"Failed to generate briefing: {str(e)}")


@router.get("/latest")
async def get_latest_briefing():
    """Get the most recent CEO briefing report.

    Returns:
        Content of the latest briefing report
    """
    from pathlib import Path
    import os

    vault_path = os.getenv("VAULT_PATH", "./AI_Employee_Vault")
    reports_dir = Path(vault_path) / "Reports"

    if not reports_dir.exists():
        raise HTTPException(status_code=404, detail="No reports directory found")

    # Find the most recent CEO briefing file
    briefing_files = list(reports_dir.glob("CEO_Briefing_*.md"))

    if not briefing_files:
        raise HTTPException(status_code=404, detail="No CEO briefings found")

    # Sort by modification time to get the most recent
    latest_file = max(briefing_files, key=lambda f: f.stat().st_mtime)

    try:
        content = latest_file.read_text()

        return {
            "file_path": str(latest_file),
            "content": content,
            "modified_at": datetime.fromtimestamp(latest_file.stat().st_mtime).isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read briefing: {str(e)}")