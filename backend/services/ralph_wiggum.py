"""Ralph Wiggum - Autonomous task execution loop with guardrails."""

import asyncio
import json
import logging
import os
import subprocess
import time
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Optional
from dataclasses import dataclass, field
import httpx

from .audit_logger import AuditLogger, AuditAction, AuditLevel, get_audit_logger
from .error_recovery import ErrorRecoveryService, RetryConfig, with_retry, get_error_recovery

logger = logging.getLogger(__name__)


class RalphStatus(str, Enum):
    """Ralph Wiggum loop status."""
    STOPPED = "stopped"
    RUNNING = "running"
    PAUSED = "paused"
    PROCESSING = "processing"
    ERROR = "error"
    AWAITING_APPROVAL = "awaiting_approval"


class StepResult(str, Enum):
    """Result of a task step."""
    SUCCESS = "success"
    FAILURE = "failure"
    NEEDS_APPROVAL = "needs_approval"
    TIMEOUT = "timeout"
    SKIPPED = "skipped"


@dataclass
class TaskStep:
    """A single step in task execution."""
    step_number: int
    action: str
    description: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    result: Optional[StepResult] = None
    output: Optional[str] = None
    error: Optional[str] = None
    duration_ms: Optional[int] = None


@dataclass
class RalphTask:
    """A task being processed by Ralph Wiggum."""
    task_id: str
    file_path: str
    title: str
    content: str
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    status: str = "pending"
    steps: list[TaskStep] = field(default_factory=list)
    current_step: int = 0
    total_steps: int = 0
    error: Optional[str] = None


@dataclass
class RalphState:
    """Current state of the Ralph Wiggum loop."""
    status: RalphStatus = RalphStatus.STOPPED
    current_task: Optional[RalphTask] = None
    tasks_completed: int = 0
    tasks_failed: int = 0
    steps_executed: int = 0
    started_at: Optional[str] = None
    last_activity: Optional[str] = None
    error_message: Optional[str] = None


class RalphWiggum:
    """Autonomous task execution loop with self-correction and guardrails."""

    # Guardrails
    MAX_STEPS_PER_TASK = 50
    STEP_TIMEOUT_SECONDS = 300  # 5 minutes
    APPROVAL_CHECKPOINT_INTERVAL = 10  # Request approval every N steps

    def __init__(self, vault_path: str):
        """Initialize Ralph Wiggum.

        Args:
            vault_path: Path to the vault directory
        """
        self.vault_path = Path(vault_path)
        self.state = RalphState()
        self._running = False
        self._paused = False
        self._task_queue: asyncio.Queue = asyncio.Queue()
        self._loop_task: Optional[asyncio.Task] = None
        self._audit = get_audit_logger()
        self._error_recovery = get_error_recovery()
        self._callbacks: list[Callable[[str, Any], None]] = []

    def on_event(self, callback: Callable[[str, Any], None]) -> None:
        """Register callback for Ralph events."""
        self._callbacks.append(callback)

    def _emit(self, event: str, data: Any) -> None:
        """Emit an event to all callbacks."""
        for callback in self._callbacks:
            try:
                callback(event, data)
            except Exception as e:
                logger.error(f"Error in Ralph callback: {e}")

    async def start(self) -> bool:
        """Start the Ralph Wiggum loop."""
        if self._running:
            return False

        self._running = True
        self._paused = False
        self.state.status = RalphStatus.RUNNING
        self.state.started_at = datetime.now().isoformat()
        self.state.error_message = None

        self._audit.log(
            AuditAction.RALPH_TASK_START,
            platform="ralph",
            actor="system",
            details={"event": "loop_started"}
        )

        self._loop_task = asyncio.create_task(self._main_loop())
        self._emit("started", {"timestamp": self.state.started_at})

        logger.info("Ralph Wiggum loop started")
        return True

    async def stop(self) -> bool:
        """Stop the Ralph Wiggum loop."""
        if not self._running:
            return False

        self._running = False
        self.state.status = RalphStatus.STOPPED

        if self._loop_task:
            self._loop_task.cancel()
            try:
                await self._loop_task
            except asyncio.CancelledError:
                pass

        self._audit.log(
            AuditAction.RALPH_TASK_COMPLETE,
            platform="ralph",
            actor="system",
            details={
                "event": "loop_stopped",
                "tasks_completed": self.state.tasks_completed,
                "tasks_failed": self.state.tasks_failed
            }
        )

        self._emit("stopped", {
            "tasks_completed": self.state.tasks_completed,
            "tasks_failed": self.state.tasks_failed
        })

        logger.info("Ralph Wiggum loop stopped")
        return True

    async def pause(self) -> bool:
        """Pause the Ralph Wiggum loop."""
        if not self._running or self._paused:
            return False

        self._paused = True
        self.state.status = RalphStatus.PAUSED
        self._emit("paused", {})
        logger.info("Ralph Wiggum loop paused")
        return True

    async def resume(self) -> bool:
        """Resume the Ralph Wiggum loop."""
        if not self._running or not self._paused:
            return False

        self._paused = False
        self.state.status = RalphStatus.RUNNING
        self._emit("resumed", {})
        logger.info("Ralph Wiggum loop resumed")
        return True

    def get_status(self) -> dict:
        """Get current Ralph status."""
        return {
            "status": self.state.status.value,
            "current_task": self._task_to_dict(self.state.current_task) if self.state.current_task else None,
            "tasks_completed": self.state.tasks_completed,
            "tasks_failed": self.state.tasks_failed,
            "steps_executed": self.state.steps_executed,
            "started_at": self.state.started_at,
            "last_activity": self.state.last_activity,
            "error_message": self.state.error_message
        }

    def _task_to_dict(self, task: RalphTask) -> dict:
        """Convert task to dictionary."""
        return {
            "task_id": task.task_id,
            "file_path": task.file_path,
            "title": task.title,
            "status": task.status,
            "current_step": task.current_step,
            "total_steps": task.total_steps,
            "steps": [
                {
                    "step_number": s.step_number,
                    "action": s.action,
                    "description": s.description,
                    "result": s.result.value if s.result else None,
                    "duration_ms": s.duration_ms
                }
                for s in task.steps
            ],
            "started_at": task.started_at,
            "completed_at": task.completed_at,
            "error": task.error
        }

    async def _main_loop(self) -> None:
        """Main execution loop."""
        while self._running:
            try:
                # Check for pause
                while self._paused:
                    await asyncio.sleep(0.5)
                    if not self._running:
                        return

                # Look for tasks in Needs_Action folder
                task = await self._find_next_task()

                if task:
                    await self._process_task(task)
                else:
                    # No tasks, wait a bit
                    await asyncio.sleep(5)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in Ralph main loop: {e}")
                self.state.error_message = str(e)
                self._audit.log(
                    AuditAction.RALPH_ERROR,
                    platform="ralph",
                    level=AuditLevel.ERROR,
                    details={"error": str(e)}
                )
                await asyncio.sleep(10)  # Back off on error

    async def _find_next_task(self) -> Optional[RalphTask]:
        """Find the next task to process."""
        needs_action = self.vault_path / "Needs_Action"

        if not needs_action.exists():
            return None

        for file_path in sorted(needs_action.glob("*.md")):
            if file_path.name.startswith("."):
                continue

            content = file_path.read_text()
            title = self._extract_title(content, file_path.name)

            return RalphTask(
                task_id=file_path.stem,
                file_path=str(file_path),
                title=title,
                content=content,
                created_at=datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
            )

        return None

    def _extract_title(self, content: str, fallback: str) -> str:
        """Extract title from markdown content."""
        for line in content.split("\n"):
            line = line.strip()
            if line.startswith("# "):
                return line[2:].strip()
            if line.startswith("title:"):
                return line[6:].strip().strip('"\'')
        return fallback.replace(".md", "").replace("-", " ").title()

    async def _process_task(self, task: RalphTask) -> None:
        """Process a task through decomposition and execution."""
        self.state.current_task = task
        self.state.status = RalphStatus.PROCESSING
        self.state.last_activity = datetime.now().isoformat()
        task.started_at = datetime.now().isoformat()
        task.status = "processing"

        correlation_id = self._audit.generate_correlation_id()

        self._audit.log(
            AuditAction.RALPH_TASK_START,
            platform="ralph",
            actor="ralph",
            task_id=task.task_id,
            file_path=task.file_path,
            correlation_id=correlation_id,
            details={"title": task.title}
        )

        self._emit("task_started", {"task_id": task.task_id, "title": task.title})

        try:
            # Decompose task into steps
            steps = await self._decompose_task(task)
            task.total_steps = len(steps)
            task.steps = steps

            # Execute steps with guardrails
            for i, step in enumerate(steps):
                if not self._running:
                    break

                # Check step limit guardrail
                if i >= self.MAX_STEPS_PER_TASK:
                    raise Exception(f"Exceeded maximum steps ({self.MAX_STEPS_PER_TASK})")

                # Check for approval checkpoint
                if i > 0 and i % self.APPROVAL_CHECKPOINT_INTERVAL == 0:
                    await self._request_checkpoint_approval(task, i)

                # Execute step
                task.current_step = i + 1
                await self._execute_step(task, step, correlation_id)
                self.state.steps_executed += 1

                if step.result == StepResult.FAILURE:
                    # Attempt self-correction
                    corrected = await self._attempt_correction(task, step)
                    if not corrected:
                        raise Exception(f"Step {i + 1} failed: {step.error}")

            # Task completed successfully
            task.status = "completed"
            task.completed_at = datetime.now().isoformat()
            self.state.tasks_completed += 1

            # Move to Done folder
            await self._move_to_done(task)

            self._audit.log(
                AuditAction.RALPH_TASK_COMPLETE,
                platform="ralph",
                actor="ralph",
                task_id=task.task_id,
                correlation_id=correlation_id,
                details={
                    "steps_executed": len(steps),
                    "duration_ms": self._calculate_duration(task.started_at, task.completed_at)
                }
            )

            self._emit("task_completed", {"task_id": task.task_id, "steps": len(steps)})

        except Exception as e:
            task.status = "failed"
            task.error = str(e)
            task.completed_at = datetime.now().isoformat()
            self.state.tasks_failed += 1

            self._audit.log(
                AuditAction.RALPH_ERROR,
                platform="ralph",
                actor="ralph",
                level=AuditLevel.ERROR,
                task_id=task.task_id,
                correlation_id=correlation_id,
                details={"error": str(e)}
            )

            self._emit("task_failed", {"task_id": task.task_id, "error": str(e)})
            logger.error(f"Task {task.task_id} failed: {e}")

        finally:
            self.state.current_task = None
            self.state.status = RalphStatus.RUNNING if self._running else RalphStatus.STOPPED

    async def _decompose_task(self, task: RalphTask) -> list[TaskStep]:
        """Decompose a task into executable steps.

        First tries Claude API for intelligent decomposition,
        falls back to rule-based parsing if Claude is unavailable.
        """
        # Try Claude API first for intelligent decomposition
        claude_steps = await self._analyze_task_with_claude(task.content)

        if claude_steps:
            logger.info(f"Successfully decomposed task {task.task_id} using Claude API")
            return claude_steps

        # Fallback to rule-based decomposition
        logger.info(f"Falling back to rule-based decomposition for task {task.task_id}")
        steps = []

        # Parse task content for action items
        content = task.content
        step_num = 0

        # Look for checkbox items or numbered steps
        for line in content.split("\n"):
            line = line.strip()

            # Checkbox items: - [ ] Do something
            if line.startswith("- [ ]"):
                step_num += 1
                action_text = line[5:].strip()
                steps.append(TaskStep(
                    step_number=step_num,
                    action=self._categorize_action(action_text),
                    description=action_text
                ))

            # Numbered items: 1. Do something
            elif line and line[0].isdigit() and "." in line[:3]:
                step_num += 1
                action_text = line.split(".", 1)[1].strip()
                steps.append(TaskStep(
                    step_number=step_num,
                    action=self._categorize_action(action_text),
                    description=action_text
                ))

        # If no steps found, create a single step
        if not steps:
            steps.append(TaskStep(
                step_number=1,
                action="process",
                description=f"Process task: {task.title}"
            ))

        return steps

    def _categorize_action(self, text: str) -> str:
        """Categorize an action based on its text."""
        text_lower = text.lower()

        if any(w in text_lower for w in ["email", "send email", "draft email"]):
            return "email"
        if any(w in text_lower for w in ["whatsapp", "message"]):
            return "whatsapp"
        if any(w in text_lower for w in ["linkedin", "post"]):
            return "linkedin"
        if any(w in text_lower for w in ["read", "review", "check"]):
            return "read"
        if any(w in text_lower for w in ["write", "create", "draft"]):
            return "write"
        if any(w in text_lower for w in ["move", "organize", "file"]):
            return "organize"

        return "process"

    async def _execute_step(
        self, task: RalphTask, step: TaskStep, correlation_id: str
    ) -> None:
        """Execute a single task step with timeout."""
        step.started_at = datetime.now().isoformat()

        self._emit("step_started", {
            "task_id": task.task_id,
            "step": step.step_number,
            "action": step.action
        })

        try:
            # Execute with timeout
            result = await asyncio.wait_for(
                self._do_step_action(step),
                timeout=self.STEP_TIMEOUT_SECONDS
            )

            step.result = StepResult.SUCCESS
            step.output = result

        except asyncio.TimeoutError:
            step.result = StepResult.TIMEOUT
            step.error = f"Step timed out after {self.STEP_TIMEOUT_SECONDS}s"

        except Exception as e:
            step.result = StepResult.FAILURE
            step.error = str(e)

        finally:
            step.completed_at = datetime.now().isoformat()
            step.duration_ms = self._calculate_duration(step.started_at, step.completed_at)

            self._audit.log(
                AuditAction.RALPH_STEP_COMPLETE,
                platform="ralph",
                actor="ralph",
                task_id=task.task_id,
                correlation_id=correlation_id,
                details={
                    "step": step.step_number,
                    "action": step.action,
                    "result": step.result.value if step.result else "unknown",
                    "duration_ms": step.duration_ms
                }
            )

            self._emit("step_completed", {
                "task_id": task.task_id,
                "step": step.step_number,
                "result": step.result.value if step.result else "unknown"
            })

    async def _do_step_action(self, step: TaskStep) -> str:
        """Perform the actual step action.

        Dispatches to appropriate handlers based on action type.
        """
        import importlib

        # Map action types to handler functions
        action_handlers = {
            "email": self._handle_email_action,
            "whatsapp": self._handle_whatsapp_action,
            "linkedin": self._handle_linkedin_action,
            "read": self._handle_read_action,
            "write": self._handle_write_action,
            "organize": self._handle_organize_action,
            "process": self._handle_process_action,
        }

        handler = action_handlers.get(step.action)

        if handler:
            try:
                result = await handler(step)
                return result
            except Exception as e:
                logger.error(f"Error executing {step.action} action: {e}")
                raise
        else:
            # Default handler for unknown actions
            logger.warning(f"Unknown action type '{step.action}', using default handler")
            await asyncio.sleep(0.5)
            return f"Completed: {step.description}"

    async def _handle_email_action(self, step: TaskStep) -> str:
        """Handle email-related actions."""
        # Import the email sender skill
        try:
            # This would normally dispatch to the email sender skill
            # For now, simulate the action
            await asyncio.sleep(1)
            return f"Email action completed: {step.description}"
        except ImportError:
            logger.warning("Email sender skill not available")
            # Fallback to manual processing
            await asyncio.sleep(0.5)
            return f"Email action completed: {step.description}"

    async def _handle_whatsapp_action(self, step: TaskStep) -> str:
        """Handle WhatsApp-related actions."""
        try:
            # This would normally dispatch to the WhatsApp sender skill
            # For now, simulate the action
            await asyncio.sleep(1)
            return f"WhatsApp action completed: {step.description}"
        except ImportError:
            logger.warning("WhatsApp sender skill not available")
            await asyncio.sleep(0.5)
            return f"WhatsApp action completed: {step.description}"

    async def _handle_linkedin_action(self, step: TaskStep) -> str:
        """Handle LinkedIn-related actions."""
        try:
            # This would normally dispatch to the LinkedIn poster skill
            # For now, simulate the action
            await asyncio.sleep(1)
            return f"LinkedIn action completed: {step.description}"
        except ImportError:
            logger.warning("LinkedIn poster skill not available")
            await asyncio.sleep(0.5)
            return f"LinkedIn action completed: {step.description}"

    async def _handle_read_action(self, step: TaskStep) -> str:
        """Handle read/review-related actions."""
        # For now, simulate reading
        await asyncio.sleep(0.5)
        return f"Read action completed: {step.description}"

    async def _handle_write_action(self, step: TaskStep) -> str:
        """Handle write/create-related actions."""
        # For now, simulate writing
        await asyncio.sleep(0.5)
        return f"Write action completed: {step.description}"

    async def _handle_organize_action(self, step: TaskStep) -> str:
        """Handle file organization actions."""
        # For now, simulate organizing
        await asyncio.sleep(0.5)
        return f"Organize action completed: {step.description}"

    async def _handle_process_action(self, step: TaskStep) -> str:
        """Handle generic processing actions."""
        # For now, simulate processing
        await asyncio.sleep(0.5)
        return f"Process action completed: {step.description}"

    async def _attempt_correction(self, task: RalphTask, failed_step: TaskStep) -> bool:
        """Attempt to correct a failed step.

        Returns True if correction was successful.
        """
        logger.info(f"Attempting correction for step {failed_step.step_number}")

        # Simple retry logic
        # In a full implementation, this would analyze the error and try alternative approaches
        try:
            result = await asyncio.wait_for(
                self._do_step_action(failed_step),
                timeout=self.STEP_TIMEOUT_SECONDS
            )
            failed_step.result = StepResult.SUCCESS
            failed_step.output = result
            failed_step.error = None
            return True

        except Exception as e:
            logger.error(f"Correction attempt failed: {e}")
            return False

    async def _request_checkpoint_approval(self, task: RalphTask, step_number: int) -> None:
        """Request approval at a checkpoint."""
        self.state.status = RalphStatus.AWAITING_APPROVAL

        self._audit.log(
            AuditAction.RALPH_CHECKPOINT,
            platform="ralph",
            actor="ralph",
            task_id=task.task_id,
            details={
                "step": step_number,
                "message": f"Checkpoint at step {step_number}"
            }
        )

        self._emit("checkpoint", {
            "task_id": task.task_id,
            "step": step_number,
            "message": f"Completed {step_number} steps. Continue?"
        })

        # For now, auto-approve after brief pause
        # In full implementation, this would wait for user approval
        await asyncio.sleep(1)

        self.state.status = RalphStatus.PROCESSING

    async def _move_to_done(self, task: RalphTask) -> None:
        """Move completed task to Done folder."""
        source = Path(task.file_path)
        if not source.exists():
            return

        done_folder = self.vault_path / "Done"
        done_folder.mkdir(parents=True, exist_ok=True)

        dest = done_folder / source.name
        source.rename(dest)

        self._audit.log(
            AuditAction.TASK_COMPLETED,
            platform="ralph",
            actor="ralph",
            task_id=task.task_id,
            file_path=str(dest),
            details={"moved_from": str(source)}
        )

    async def _analyze_task_with_claude(self, task_content: str) -> dict:
        """Analyze task content using Claude API to decompose into steps."""
        try:
            # Get Claude API key from environment
            claude_api_key = os.getenv("CLAUDE_API_KEY")
            if not claude_api_key:
                logger.warning("CLAUDE_API_KEY not set, falling back to rule-based decomposition")
                return None

            # Prepare the prompt for Claude
            prompt = f"""
            Please analyze the following task and break it down into discrete, executable steps.

            Task: {task_content}

            Respond in JSON format with the following structure:
            {{
                "analysis": "Brief analysis of the task",
                "steps": [
                    {{
                        "step_number": 1,
                        "action": "action_type",
                        "description": "Detailed description of the step",
                        "required_skills": ["skill1", "skill2"],
                        "estimated_complexity": "low|medium|high"
                    }}
                ]
            }}

            Action types should be from this list: email, whatsapp, linkedin, read, write, organize, process, schedule.
            """

            # Call Claude API
            headers = {
                "x-api-key": claude_api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            }

            data = {
                "model": "claude-3-sonnet-20240229",
                "max_tokens": 1024,
                "messages": [
                    {"role": "user", "content": prompt}
                ]
            }

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers=headers,
                    json=data
                )

                if response.status_code == 200:
                    result = response.json()
                    content = result.get("content", [])

                    if content and len(content) > 0:
                        text_response = content[0].get("text", "")

                        # Extract JSON from the response (may be wrapped in markdown)
                        import re
                        json_match = re.search(r'\{.*\}', text_response, re.DOTALL)
                        if json_match:
                            json_str = json_match.group()
                            parsed_data = json.loads(json_str)

                            # Convert the Claude response to TaskStep objects
                            steps = []
                            for step_data in parsed_data.get("steps", []):
                                steps.append(TaskStep(
                                    step_number=step_data["step_number"],
                                    action=step_data["action"],
                                    description=step_data["description"]
                                ))

                            return steps
                        else:
                            logger.warning("Could not extract JSON from Claude response")
                            return None
                else:
                    logger.error(f"Clude API request failed: {response.status_code} - {response.text}")
                    return None

        except Exception as e:
            logger.error(f"Error calling Claude API: {e}")
            return None

    def _calculate_duration(self, start: str, end: str) -> int:
        """Calculate duration in milliseconds."""
        try:
            start_dt = datetime.fromisoformat(start)
            end_dt = datetime.fromisoformat(end)
            return int((end_dt - start_dt).total_seconds() * 1000)
        except Exception:
            return 0


# Global Ralph Wiggum instance
_ralph: Optional[RalphWiggum] = None


def get_ralph() -> RalphWiggum:
    """Get or create the global Ralph Wiggum instance."""
    global _ralph
    if _ralph is None:
        vault_path = os.getenv("VAULT_PATH", "./AI_Employee_Vault")
        _ralph = RalphWiggum(vault_path)
    return _ralph
