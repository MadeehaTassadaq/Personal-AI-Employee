"""Ralph Wiggum API endpoints."""

from fastapi import APIRouter, HTTPException

from ..services.ralph_wiggum import get_ralph, RalphStatus

router = APIRouter()


@router.get("/status")
async def get_ralph_status():
    """Get current Ralph Wiggum status.

    Returns:
        Current status including:
        - status: running/stopped/paused/processing/error
        - current_task: Current task being processed (if any)
        - tasks_completed: Number of tasks completed
        - tasks_failed: Number of tasks failed
        - steps_executed: Total steps executed
    """
    ralph = get_ralph()
    return ralph.get_status()


@router.post("/start")
async def start_ralph():
    """Start the Ralph Wiggum autonomous loop.

    The loop will:
    1. Monitor Needs_Action folder for tasks
    2. Decompose tasks into steps
    3. Execute steps with guardrails
    4. Move completed tasks to Done folder

    Returns:
        Success message and current status
    """
    ralph = get_ralph()

    if ralph.state.status == RalphStatus.RUNNING:
        raise HTTPException(
            status_code=400,
            detail="Ralph is already running"
        )

    success = await ralph.start()

    if not success:
        raise HTTPException(
            status_code=500,
            detail="Failed to start Ralph"
        )

    return {
        "message": "Ralph Wiggum loop started",
        "status": ralph.get_status()
    }


@router.post("/stop")
async def stop_ralph():
    """Stop the Ralph Wiggum autonomous loop.

    Any task currently being processed will be interrupted.

    Returns:
        Success message and final status
    """
    ralph = get_ralph()

    if ralph.state.status == RalphStatus.STOPPED:
        raise HTTPException(
            status_code=400,
            detail="Ralph is not running"
        )

    success = await ralph.stop()

    if not success:
        raise HTTPException(
            status_code=500,
            detail="Failed to stop Ralph"
        )

    return {
        "message": "Ralph Wiggum loop stopped",
        "status": ralph.get_status()
    }


@router.post("/pause")
async def pause_ralph():
    """Pause the Ralph Wiggum loop.

    The loop will pause after the current step completes.
    Use /resume to continue.

    Returns:
        Success message
    """
    ralph = get_ralph()

    if ralph.state.status != RalphStatus.RUNNING and \
       ralph.state.status != RalphStatus.PROCESSING:
        raise HTTPException(
            status_code=400,
            detail="Ralph is not running"
        )

    success = await ralph.pause()

    if not success:
        raise HTTPException(
            status_code=500,
            detail="Failed to pause Ralph"
        )

    return {
        "message": "Ralph Wiggum loop paused",
        "status": ralph.get_status()
    }


@router.post("/resume")
async def resume_ralph():
    """Resume the paused Ralph Wiggum loop.

    Returns:
        Success message
    """
    ralph = get_ralph()

    if ralph.state.status != RalphStatus.PAUSED:
        raise HTTPException(
            status_code=400,
            detail="Ralph is not paused"
        )

    success = await ralph.resume()

    if not success:
        raise HTTPException(
            status_code=500,
            detail="Failed to resume Ralph"
        )

    return {
        "message": "Ralph Wiggum loop resumed",
        "status": ralph.get_status()
    }


@router.get("/task")
async def get_current_task():
    """Get details of the current task being processed.

    Returns:
        Current task details or null if no task
    """
    ralph = get_ralph()
    status = ralph.get_status()

    return {
        "current_task": status.get("current_task"),
        "status": status.get("status")
    }


@router.get("/history")
async def get_task_history():
    """Get history of processed tasks.

    Returns:
        Summary of completed and failed tasks
    """
    ralph = get_ralph()
    status = ralph.get_status()

    return {
        "tasks_completed": status.get("tasks_completed", 0),
        "tasks_failed": status.get("tasks_failed", 0),
        "steps_executed": status.get("steps_executed", 0),
        "started_at": status.get("started_at"),
        "last_activity": status.get("last_activity")
    }


@router.get("/guardrails")
async def get_guardrails():
    """Get current guardrail settings.

    Returns:
        Guardrail configuration
    """
    ralph = get_ralph()

    return {
        "max_steps_per_task": ralph.MAX_STEPS_PER_TASK,
        "step_timeout_seconds": ralph.STEP_TIMEOUT_SECONDS,
        "approval_checkpoint_interval": ralph.APPROVAL_CHECKPOINT_INTERVAL
    }
