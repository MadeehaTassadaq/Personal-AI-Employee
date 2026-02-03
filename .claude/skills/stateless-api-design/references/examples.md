# Stateless API Examples

## Table of Contents

1. [FastAPI Stateless Endpoint](#fastapi-stateless-endpoint)
2. [MCP Tool Implementation](#mcp-tool-implementation)
3. [Chat API with Conversation Replay](#chat-api-with-conversation-replay)
4. [AI Agent Orchestrator](#ai-agent-orchestrator)
5. [Complete Application Example](#complete-application-example)

---

## FastAPI Stateless Endpoint

### Complete CRUD API

```python
from fastapi import FastAPI, Depends, HTTPException, Header
from sqlmodel import Session, select
from pydantic import BaseModel
from uuid import UUID, uuid4
from datetime import datetime
from jose import jwt

app = FastAPI()

# --- Models ---

class TaskBase(BaseModel):
    title: str
    description: str | None = None

class TaskCreate(TaskBase):
    pass

class TaskUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    completed: bool | None = None

class TaskResponse(TaskBase):
    id: UUID
    user_id: UUID
    completed: bool
    created_at: datetime

# --- Dependencies (all stateless) ---

def get_db():
    """Database session - scoped to request."""
    with Session(engine) as session:
        yield session

async def get_current_user(
    authorization: str = Header(...)
) -> UUID:
    """Extract user from JWT - no server state."""
    try:
        token = authorization.replace("Bearer ", "")
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return UUID(payload["sub"])
    except Exception:
        raise HTTPException(401, "Invalid token")

# --- Endpoints (all stateless) ---

@app.post("/tasks", response_model=TaskResponse, status_code=201)
async def create_task(
    task: TaskCreate,
    user_id: UUID = Depends(get_current_user),
    db: Session = Depends(get_db),
    idempotency_key: str | None = Header(None)
):
    """
    Create task - stateless pattern:
    1. Auth from token (no session lookup)
    2. Optional idempotency check from database
    3. Create in database
    4. Return complete response
    5. No lingering state
    """
    # Idempotency check
    if idempotency_key:
        existing = db.exec(
            select(IdempotencyRecord)
            .where(IdempotencyRecord.key == idempotency_key)
        ).first()
        if existing:
            return existing.response

    # Create task
    db_task = Task(
        id=uuid4(),
        user_id=user_id,
        title=task.title,
        description=task.description,
        completed=False,
        created_at=datetime.utcnow()
    )
    db.add(db_task)

    # Record idempotency
    if idempotency_key:
        db.add(IdempotencyRecord(key=idempotency_key, response=db_task.dict()))

    db.commit()
    db.refresh(db_task)

    return db_task

@app.get("/tasks", response_model=list[TaskResponse])
async def list_tasks(
    user_id: UUID = Depends(get_current_user),
    db: Session = Depends(get_db),
    completed: bool | None = None,
    limit: int = 50,
    offset: int = 0
):
    """
    List tasks - stateless pattern:
    1. User ID from token
    2. All filtering via query params
    3. Pagination via query params
    4. Fresh data from database
    """
    query = select(Task).where(Task.user_id == user_id)

    if completed is not None:
        query = query.where(Task.completed == completed)

    query = query.offset(offset).limit(limit)

    return db.exec(query).all()

@app.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: UUID,
    user_id: UUID = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get single task - stateless pattern:
    1. Task ID from path
    2. User ID from token for authorization
    3. Fetch from database
    """
    task = db.exec(
        select(Task)
        .where(Task.id == task_id)
        .where(Task.user_id == user_id)
    ).first()

    if not task:
        raise HTTPException(404, "Task not found")

    return task

@app.patch("/tasks/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: UUID,
    update: TaskUpdate,
    user_id: UUID = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update task - stateless pattern:
    1. Fetch current state from database
    2. Apply updates
    3. Persist to database
    4. Return complete updated object
    """
    task = db.exec(
        select(Task)
        .where(Task.id == task_id)
        .where(Task.user_id == user_id)
    ).first()

    if not task:
        raise HTTPException(404, "Task not found")

    # Apply updates
    update_data = update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(task, key, value)

    db.commit()
    db.refresh(task)

    return task

@app.delete("/tasks/{task_id}", status_code=204)
async def delete_task(
    task_id: UUID,
    user_id: UUID = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete task - idempotent (can be called multiple times safely)."""
    task = db.exec(
        select(Task)
        .where(Task.id == task_id)
        .where(Task.user_id == user_id)
    ).first()

    if task:
        db.delete(task)
        db.commit()

    # Return 204 whether task existed or not (idempotent)
```

---

## MCP Tool Implementation

### Stateless MCP Server for Task Management

```python
from mcp import FastMCPServer
from sqlmodel import Session, select
from uuid import UUID, uuid4
from datetime import datetime

mcp = FastMCPServer("task-manager")

@mcp.tool()
async def add_task(
    user_id: str,
    title: str,
    description: str | None = None
) -> dict:
    """
    Add a new task.

    Stateless design:
    - user_id passed explicitly (not from session)
    - Creates in database
    - Returns complete result
    - No server state modified

    Args:
        user_id: The user's ID
        title: Task title
        description: Optional task description

    Returns:
        Created task with ID and status
    """
    async with get_async_session() as db:
        task = Task(
            id=uuid4(),
            user_id=UUID(user_id),
            title=title,
            description=description,
            completed=False,
            created_at=datetime.utcnow()
        )
        db.add(task)
        await db.commit()

        return {
            "id": str(task.id),
            "title": task.title,
            "description": task.description,
            "completed": task.completed,
            "created_at": task.created_at.isoformat()
        }

@mcp.tool()
async def list_tasks(
    user_id: str,
    completed: bool | None = None
) -> list[dict]:
    """
    List tasks for a user.

    Stateless design:
    - Fetches fresh from database each call
    - No cached task lists
    - Filters applied via query

    Args:
        user_id: The user's ID
        completed: Optional filter for completion status

    Returns:
        List of tasks
    """
    async with get_async_session() as db:
        query = select(Task).where(Task.user_id == UUID(user_id))

        if completed is not None:
            query = query.where(Task.completed == completed)

        result = await db.exec(query)
        tasks = result.all()

        return [
            {
                "id": str(t.id),
                "title": t.title,
                "description": t.description,
                "completed": t.completed
            }
            for t in tasks
        ]

@mcp.tool()
async def complete_task(
    user_id: str,
    task_id: str
) -> dict:
    """
    Mark a task as completed.

    Stateless design:
    - Fetch task from database
    - Verify ownership
    - Update in database
    - Return result

    Args:
        user_id: The user's ID (for authorization)
        task_id: The task ID to complete

    Returns:
        Updated task or error
    """
    async with get_async_session() as db:
        task = await db.exec(
            select(Task)
            .where(Task.id == UUID(task_id))
            .where(Task.user_id == UUID(user_id))
        ).first()

        if not task:
            return {"error": "Task not found", "success": False}

        task.completed = True
        await db.commit()

        return {
            "success": True,
            "id": str(task.id),
            "title": task.title,
            "completed": True
        }

@mcp.tool()
async def delete_task(
    user_id: str,
    task_id: str
) -> dict:
    """
    Delete a task.

    Idempotent: Returns success even if task doesn't exist.

    Args:
        user_id: The user's ID (for authorization)
        task_id: The task ID to delete

    Returns:
        Deletion result
    """
    async with get_async_session() as db:
        task = await db.exec(
            select(Task)
            .where(Task.id == UUID(task_id))
            .where(Task.user_id == UUID(user_id))
        ).first()

        if task:
            await db.delete(task)
            await db.commit()

        return {"success": True, "deleted": task is not None}
```

---

## Chat API with Conversation Replay

### Stateless Chat Implementation

```python
from fastapi import FastAPI, Depends
from sqlmodel import Session, select
from pydantic import BaseModel
from uuid import UUID, uuid4
from datetime import datetime
import openai

app = FastAPI()

# --- Models ---

class Message(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    conversation_id: UUID = Field(index=True)
    role: str  # "user" | "assistant" | "system"
    content: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    conversation_id: UUID
    response: str
    message_count: int

# --- Endpoints ---

@app.post("/conversations", response_model=dict)
async def create_conversation(
    user_id: UUID = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create new conversation - just returns an ID."""
    conversation_id = uuid4()

    # Optionally add system message
    system_msg = Message(
        conversation_id=conversation_id,
        role="system",
        content="You are a helpful assistant."
    )
    db.add(system_msg)
    db.commit()

    return {"conversation_id": str(conversation_id)}

@app.post("/conversations/{conversation_id}/chat", response_model=ChatResponse)
async def chat(
    conversation_id: UUID,
    request: ChatRequest,
    user_id: UUID = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Send message and get response.

    Stateless conversation replay pattern:
    1. Fetch ALL previous messages from database
    2. Build context array
    3. Append new user message
    4. Call AI with full context
    5. Persist both messages
    6. Return response
    7. Discard all in-memory context (garbage collected)
    """
    # Step 1: Fetch conversation history from database
    history = db.exec(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at)
    ).all()

    # Step 2: Build context array for AI
    messages = [
        {"role": msg.role, "content": msg.content}
        for msg in history
    ]

    # Step 3: Add new user message to context
    messages.append({"role": "user", "content": request.message})

    # Step 4: Call AI (stateless - no conversation memory in AI service)
    ai_response = await openai.ChatCompletion.acreate(
        model="gpt-4",
        messages=messages
    )
    response_content = ai_response.choices[0].message.content

    # Step 5: Persist both messages to database
    user_msg = Message(
        conversation_id=conversation_id,
        role="user",
        content=request.message
    )
    assistant_msg = Message(
        conversation_id=conversation_id,
        role="assistant",
        content=response_content
    )
    db.add(user_msg)
    db.add(assistant_msg)
    db.commit()

    # Step 6: Return response
    return ChatResponse(
        conversation_id=conversation_id,
        response=response_content,
        message_count=len(history) + 2
    )

    # Step 7: All local variables garbage collected
    # No state persists in server memory

@app.get("/conversations/{conversation_id}/history")
async def get_history(
    conversation_id: UUID,
    user_id: UUID = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get conversation history - always fresh from database."""
    messages = db.exec(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at)
    ).all()

    return {
        "conversation_id": str(conversation_id),
        "messages": [
            {
                "role": m.role,
                "content": m.content,
                "timestamp": m.created_at.isoformat()
            }
            for m in messages
        ]
    }
```

---

## AI Agent Orchestrator

### Stateless Agent Tool Execution

```python
from fastapi import FastAPI, Depends
from sqlmodel import Session, select
from pydantic import BaseModel
from uuid import UUID, uuid4
from datetime import datetime
from enum import Enum

app = FastAPI()

class AgentState(str, Enum):
    THINKING = "thinking"
    TOOL_CALL = "tool_call"
    COMPLETED = "completed"
    FAILED = "failed"

# --- Stateless Agent Execution ---

@app.post("/agent/execute")
async def execute_agent(
    task: str,
    user_id: UUID = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Execute agent task - stateless orchestration.

    Pattern:
    1. Create execution record in database
    2. Run agent loop
    3. Persist each step
    4. Return final result

    Can resume from any step if server crashes.
    """
    execution_id = uuid4()

    # Create execution record
    execution = AgentExecution(
        id=execution_id,
        user_id=user_id,
        task=task,
        state=AgentState.THINKING,
        created_at=datetime.utcnow()
    )
    db.add(execution)
    db.commit()

    # Agent loop
    max_steps = 10
    for step_num in range(max_steps):
        # Fetch current execution state (stateless - could be different server)
        execution = db.get(AgentExecution, execution_id)

        if execution.state == AgentState.COMPLETED:
            break

        # Get all previous steps from database
        steps = db.exec(
            select(AgentStep)
            .where(AgentStep.execution_id == execution_id)
            .order_by(AgentStep.step_number)
        ).all()

        # Build context from history
        context = build_agent_context(task, steps)

        # Get next action from AI
        action = await get_next_action(context)

        # Execute and persist step
        step = AgentStep(
            execution_id=execution_id,
            step_number=step_num,
            action_type=action.type,
            action_input=action.input,
            result=await execute_action(action),
            created_at=datetime.utcnow()
        )
        db.add(step)

        # Update execution state
        if action.type == "final_answer":
            execution.state = AgentState.COMPLETED
            execution.result = step.result

        db.commit()

    return {
        "execution_id": str(execution_id),
        "state": execution.state,
        "result": execution.result
    }

@app.get("/agent/execution/{execution_id}")
async def get_execution(
    execution_id: UUID,
    user_id: UUID = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get execution status - always from database."""
    execution = db.exec(
        select(AgentExecution)
        .where(AgentExecution.id == execution_id)
        .where(AgentExecution.user_id == user_id)
    ).first()

    if not execution:
        raise HTTPException(404, "Execution not found")

    steps = db.exec(
        select(AgentStep)
        .where(AgentStep.execution_id == execution_id)
        .order_by(AgentStep.step_number)
    ).all()

    return {
        "execution_id": str(execution_id),
        "task": execution.task,
        "state": execution.state,
        "result": execution.result,
        "steps": [
            {
                "step": s.step_number,
                "action": s.action_type,
                "result": s.result
            }
            for s in steps
        ]
    }
```

---

## Complete Application Example

### Full Stateless Application Structure

```
project/
├── app/
│   ├── main.py              # Application entry point
│   ├── api/
│   │   └── v1/
│   │       ├── tasks.py     # Task endpoints
│   │       ├── chat.py      # Chat endpoints
│   │       └── auth.py      # Auth endpoints
│   ├── core/
│   │   ├── config.py        # Environment config
│   │   ├── security.py      # JWT utilities
│   │   └── database.py      # Database session
│   ├── models/
│   │   ├── task.py
│   │   ├── message.py
│   │   └── user.py
│   └── schemas/
│       ├── task.py
│       └── chat.py
├── tests/
└── alembic/
```

### Key Files

**app/core/database.py** - Stateless session management:
```python
from sqlmodel import create_engine, Session
from contextlib import contextmanager

engine = create_engine(settings.DATABASE_URL)

def get_db():
    """
    Request-scoped database session.
    New session for each request, closed after response.
    No state persists between requests.
    """
    with Session(engine) as session:
        yield session
```

**app/core/security.py** - Stateless authentication:
```python
from jose import jwt
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_user(token: str = Depends(oauth2_scheme)):
    """
    Stateless user extraction.
    User identity comes from JWT, not server session.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(401)
        return user_id
    except JWTError:
        raise HTTPException(401)
```

**app/main.py** - No startup state:
```python
from fastapi import FastAPI

app = FastAPI()

# No global state initialization
# No in-memory caches
# No user registries

@app.on_event("startup")
async def startup():
    # Only setup database connections
    # Never initialize user state
    pass
```
