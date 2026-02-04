# MCP Tool Implementation Patterns

## Statelessness Patterns

### Pattern 1: Self-Contained Operations
Each tool call must contain all necessary information to complete the operation. Never rely on session state, cached data from previous calls, or in-memory variables.

```python
# CORRECT
@app.post("/mcp/tools/add_task")
async def add_task(user_id: str, title: str, description: Optional[str] = None):
    # All required information passed as parameters
    user = await get_user_from_db(user_id)
    task = await create_task_in_db(user_id, title, description)
    return {"success": True, "task": task}

# INCORRECT
@app.post("/mcp/tools/add_task")
async def add_task(title: str, description: Optional[str] = None):
    # Relies on cached user from previous call
    task = await create_task_in_db(cached_user_id, title, description)
    return {"success": True, "task": task}
```

### Pattern 2: Authentication Per Call
Always authenticate and authorize based on provided parameters in each tool call.

```python
# CORRECT
@app.post("/mcp/tools/update_task")
async def update_task(user_id: str, task_id: str, updates: dict):
    # Verify user has permission for this specific task
    if not await verify_user_owns_task(user_id, task_id):
        raise HTTPException(status_code=403, detail="Permission denied")

    updated_task = await update_task_in_db(task_id, updates)
    return {"success": True, "task": updated_task}
```

## Input Validation Patterns

### Pattern 3: Explicit Parameter Validation
Validate all inputs with clear error messages.

```python
from pydantic import BaseModel, validator

class AddTaskRequest(BaseModel):
    user_id: str
    title: str
    description: Optional[str] = ""
    priority: str = "medium"

    @validator('user_id')
    def validate_user_id(cls, v):
        if not v or len(v) < 5:
            raise ValueError('user_id must be at least 5 characters')
        return v

    @validator('title')
    def validate_title(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('title cannot be empty')
        if len(v) > 200:
            raise ValueError('title cannot exceed 200 characters')
        return v.strip()

    @validator('priority')
    def validate_priority(cls, v):
        allowed_priorities = ['low', 'medium', 'high', 'critical']
        if v not in allowed_priorities:
            raise ValueError(f'priority must be one of {allowed_priorities}')
        return v
```

## Output Standardization Patterns

### Pattern 4: Consistent Response Format
Maintain consistent output structure across all tools.

```python
from typing import Union, Dict, Any
from pydantic import BaseModel

class SuccessResponse(BaseModel):
    success: bool = True
    data: Dict[str, Any]

class ErrorResponse(BaseModel):
    success: bool = False
    error_code: str
    error_message: str
    recoverable: bool = True

# Example successful response
def list_tasks_response(tasks: list, total_count: int):
    return SuccessResponse(
        data={
            "tasks": tasks,
            "total_count": total_count,
            "has_more": len(tasks) < total_count
        }
    ).dict()

# Example error response
def error_response(code: str, message: str, recoverable: bool = True):
    return ErrorResponse(
        error_code=code,
        error_message=message,
        recoverable=recoverable
    ).dict()
```

## Database Persistence Patterns

### Pattern 5: Atomic Operations
Ensure database operations are atomic and properly handle transactions.

```python
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

async def create_task_with_validation(
    db_session: AsyncSession,
    user_id: str,
    title: str,
    description: str
):
    try:
        # Begin transaction
        async with db_session.begin():
            # Verify user exists
            user = await db_session.get(User, user_id)
            if not user:
                return error_response("USER_NOT_FOUND", "User does not exist")

            # Create task
            task = Task(
                user_id=user_id,
                title=title,
                description=description,
                status="pending"
            )
            db_session.add(task)
            await db_session.flush()  # Get the ID without committing

            # Log the creation
            log_entry = TaskLog(
                task_id=task.id,
                action="created",
                timestamp=datetime.utcnow()
            )
            db_session.add(log_entry)

            await db_session.commit()

            return SuccessResponse(data={"task": task.to_dict()}).dict()

    except IntegrityError as e:
        await db_session.rollback()
        return error_response("INTEGRITY_ERROR", "Database constraint violation")
    except Exception as e:
        await db_session.rollback()
        return error_response("INTERNAL_ERROR", "An unexpected error occurred")
```

## Error Handling Patterns

### Pattern 6: Structured Error Responses
Provide structured error information that agents can act upon.

```python
from enum import Enum

class ErrorCode(str, Enum):
    # Authentication errors
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"

    # Validation errors
    INVALID_INPUT = "INVALID_INPUT"
    MISSING_PARAMETER = "MISSING_PARAMETER"

    # Resource errors
    RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"
    RESOURCE_CONFLICT = "RESOURCE_CONFLICT"

    # System errors
    INTERNAL_ERROR = "INTERNAL_ERROR"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"

def handle_mcp_error(error: Exception) -> dict:
    """Convert exceptions to structured error responses"""

    if isinstance(error, ValueError):
        return ErrorResponse(
            error_code=ErrorCode.INVALID_INPUT,
            error_message=str(error),
            recoverable=True
        ).dict()

    elif isinstance(error, PermissionError):
        return ErrorResponse(
            error_code=ErrorCode.FORBIDDEN,
            error_message="Insufficient permissions for this operation",
            recoverable=False
        ).dict()

    elif isinstance(error, KeyError):
        return ErrorResponse(
            error_code=ErrorCode.MISSING_PARAMETER,
            error_message=f"Required parameter missing: {str(error)}",
            recoverable=True
        ).dict()

    else:
        # Log the actual error for debugging
        logger.error(f"Unexpected error in MCP tool: {error}")

        # Return generic error to prevent information leakage
        return ErrorResponse(
            error_code=ErrorCode.INTERNAL_ERROR,
            error_message="An internal error occurred",
            recoverable=True
        ).dict()
```

## Idempotency Patterns

### Pattern 7: Safe Retry Operations
Design operations that can be safely retried without unintended side effects.

```python
import uuid
from typing import Optional

async def create_task_idempotent(
    user_id: str,
    title: str,
    description: Optional[str],
    operation_id: Optional[str] = None
):
    """
    Create task with idempotency support using operation_id.
    If the same operation_id is used twice, return the same result.
    """
    if operation_id:
        # Check if this operation was already performed
        existing_result = await get_operation_result(operation_id)
        if existing_result:
            return existing_result

    # Perform the operation
    task = await create_task_in_db(user_id, title, description)

    # Store result with operation_id for future idempotency
    if operation_id:
        await store_operation_result(operation_id, task)

    return SuccessResponse(data={"task": task}).dict()

async def update_task_status_idempotent(task_id: str, new_status: str):
    """
    Update task status in an idempotent way.
    If the task is already in the target status, return success.
    """
    current_task = await get_task_from_db(task_id)
    if not current_task:
        return error_response("TASK_NOT_FOUND", "Task does not exist")

    # If already in target status, return success (idempotent)
    if current_task.status == new_status:
        return SuccessResponse(data={"task": current_task}).dict()

    # Otherwise, update the status
    updated_task = await update_task_status_in_db(task_id, new_status)
    return SuccessResponse(data={"task": updated_task}).dict()
```

## Tool Composition Patterns

### Pattern 8: Composable Tools
Design tools that can be safely chained by agents.

```python
# Example of composable tools
async def compose_create_and_assign_task(user_id: str, assignee_id: str, title: str):
    """
    Example of how an agent might compose multiple tools.
    Each individual tool remains atomic and stateless.
    """

    # Step 1: Create the task
    create_result = await add_task_tool(user_id, title)
    if not create_result["success"]:
        return create_result

    task_id = create_result["data"]["task"]["id"]

    # Step 2: Assign the task to someone else
    assign_result = await update_task_tool(user_id, task_id, {"assignee_id": assignee_id})

    return assign_result
```

## Performance Considerations

### Pattern 9: Efficient Queries
Optimize database queries for common tool usage patterns.

```python
# Efficient batch operations
async def batch_get_tasks(task_ids: list[str], user_id: str):
    """
    Efficiently retrieve multiple tasks in a single query.
    """
    query = select(Task).where(
        Task.id.in_(task_ids),
        Task.user_id == user_id
    )
    tasks = await db_session.execute(query)
    return [task.to_dict() for task in tasks.scalars().all()]

# Pagination for large datasets
async def paginated_list_tasks(
    user_id: str,
    page: int = 1,
    page_size: int = 50,
    filters: dict = None
):
    """
    Paginate results to prevent large payloads.
    """
    offset = (page - 1) * page_size

    query = select(Task).where(Task.user_id == user_id)

    # Apply filters if provided
    if filters:
        if filters.get("status"):
            query = query.where(Task.status == filters["status"])
        if filters.get("due_after"):
            query = query.where(Task.due_date >= filters["due_after"])

    # Count total before pagination
    count_query = select(func.count()).select_from(query.subquery())
    total_count = await db_session.scalar(count_query)

    # Apply pagination
    query = query.offset(offset).limit(page_size)
    tasks = await db_session.execute(query)

    return {
        "tasks": [task.to_dict() for task in tasks.scalars().all()],
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total_count": total_count,
            "has_more": offset + page_size < total_count
        }
    }
```