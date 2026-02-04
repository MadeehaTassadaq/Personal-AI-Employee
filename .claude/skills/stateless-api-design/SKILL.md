---
name: stateless-api-design
description: Enforce and validate stateless API design patterns for production-grade backend systems (FastAPI, MCP servers, AI agents, microservices). Use when designing APIs, reviewing endpoint code, implementing MCP tools, building chat-based systems, or validating horizontal scalability. Triggers include mentions of stateless architecture, API design review, session handling, scalability concerns, MCP tool implementation, restart-safe systems, or conversation replay patterns.
---

# Stateless API Design

## Overview

Enforce stateless architecture principles in API design, ensuring systems are horizontally scalable, restart-safe, and context-independent. Every request must be independently executable without relying on server memory.

## Core Statelessness Principles

A stateless API must:

1. **Store NO session or user state in memory** - All state lives in external storage
2. **Reconstruct context from each request** - Use request payload or database lookup
3. **Persist all state in external storage** - Database, cache (Redis), or distributed store
4. **Be horizontally scalable** - Any server instance can handle any request
5. **Be restart-safe** - Server restart causes zero data loss

## Request Lifecycle Template

Every API endpoint or tool MUST follow this lifecycle:

```
1. Authenticate request (validate token/API key)
2. Extract identifiers (user_id, conversation_id, resource_id)
3. Fetch required state from database/cache
4. Perform action (business logic)
5. Persist updated state to database/cache
6. Return response
7. Discard ALL runtime context (no lingering state)
```

## Stateless Design Checklist

Before approving any API design, verify:

- [ ] **No global variables** holding user/session data
- [ ] **No in-memory collections** storing request state across calls
- [ ] **Token-based authentication** (JWT/API key) not server-session
- [ ] **All identifiers in request** - user_id, conversation_id via payload or token
- [ ] **Database-backed state** - all mutable state persists externally
- [ ] **Idempotent operations** where possible (same request = same result)
- [ ] **No cached mutable user state** - cache must be optional enhancement
- [ ] **Request isolation** - concurrent requests don't share memory state

## Anti-Patterns to Detect and Block

### REJECT: Global State

```python
# VIOLATION: Global dictionary holding user data
active_users = {}  # Survives requests, lost on restart

@app.post("/login")
async def login(user_id: str):
    active_users[user_id] = {"logged_in": True}  # Memory-only state
```

### REJECT: In-Memory Conversation History

```python
# VIOLATION: Conversation stored in memory
conversations = {}

@app.post("/chat")
async def chat(user_id: str, message: str):
    if user_id not in conversations:
        conversations[user_id] = []
    conversations[user_id].append(message)  # Lost on restart
```

### REJECT: Session-Based Auth Tied to Server

```python
# VIOLATION: Session stored in server memory
sessions = {}

@app.post("/login")
async def login(username: str):
    session_id = create_session()
    sessions[session_id] = {"user": username}  # Memory-only
    return {"session_id": session_id}
```

### REJECT: Cached Mutable User State

```python
# VIOLATION: User preferences cached mutably
user_cache = {}

@app.put("/preferences")
async def update_preferences(user_id: str, prefs: dict):
    user_cache[user_id] = prefs  # Only in memory, never persisted
```

### REJECT: Long-Lived Request Context

```python
# VIOLATION: Object storing cross-request context
class UserHandler:
    def __init__(self):
        self.current_user = None  # Survives between requests

    async def handle(self, request):
        self.current_user = request.user  # Shared across requests
```

## Approved Patterns

### Pattern 1: Database-Backed State

```python
from sqlmodel import Session, select

@app.get("/user/{user_id}/profile")
async def get_profile(user_id: str, db: Session = Depends(get_db)):
    # Fetch state from database - no memory dependency
    user = db.exec(select(User).where(User.id == user_id)).first()
    if not user:
        raise HTTPException(404, "User not found")
    return user
```

### Pattern 2: Token-Based Authentication

```python
from jose import jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    # Decode user from token - no server session
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    user_id = payload.get("sub")
    # Fetch user from database
    return await fetch_user_from_db(user_id)
```

### Pattern 3: Conversation Replay (Chat APIs)

```python
@app.post("/chat/{conversation_id}")
async def chat(
    conversation_id: str,
    message: str,
    db: Session = Depends(get_db)
):
    # Fetch full conversation from database
    conversation = db.exec(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at)
    ).all()

    # Build context from persisted messages
    context = [{"role": m.role, "content": m.content} for m in conversation]
    context.append({"role": "user", "content": message})

    # Generate response
    response = await generate_response(context)

    # Persist new messages
    db.add(Message(conversation_id=conversation_id, role="user", content=message))
    db.add(Message(conversation_id=conversation_id, role="assistant", content=response))
    db.commit()

    return {"response": response}
```

### Pattern 4: MCP Tool Implementation

```python
@mcp.tool()
async def add_task(
    user_id: str,
    title: str,
    description: str | None = None
) -> dict:
    """Add task - stateless, pure function pattern."""
    async with get_db_session() as db:
        # No in-memory state - fetch/persist via database
        task = Task(
            user_id=user_id,
            title=title,
            description=description
        )
        db.add(task)
        await db.commit()
        return {"id": task.id, "title": task.title, "status": "created"}
```

### Pattern 5: Idempotent Operations

```python
@app.put("/orders/{order_id}")
async def update_order(
    order_id: str,
    idempotency_key: str = Header(...),
    update: OrderUpdate = Body(...),
    db: Session = Depends(get_db)
):
    # Check for existing operation with same idempotency key
    existing = db.exec(
        select(IdempotencyRecord)
        .where(IdempotencyRecord.key == idempotency_key)
    ).first()

    if existing:
        return existing.response  # Return cached response

    # Perform update
    order = update_order_in_db(db, order_id, update)

    # Record idempotency
    db.add(IdempotencyRecord(key=idempotency_key, response=order.dict()))
    db.commit()

    return order
```

## Evaluation Criteria

When reviewing APIs, answer these questions:

| Question | Expected Answer |
|----------|-----------------|
| Is this API restart-safe? | Yes - no data loss on restart |
| Can this API scale horizontally? | Yes - any instance handles any request |
| Can any server instance handle any request? | Yes - no instance affinity |
| Is user context fully reconstructible? | Yes - from token + database |
| Does state survive server restart? | Yes - all in database |
| Are operations idempotent where applicable? | Yes - retry-safe |

## Integration Workflows

### Reviewing Existing Code

1. Scan for global variables and module-level state
2. Identify in-memory collections (dict, list, set)
3. Check authentication flow for session storage
4. Verify database usage for all mutable state
5. Flag any cached user-specific data

### Designing New Endpoints

1. Define request inputs (all context must come from request or token)
2. Identify database entities needed
3. Implement fetch-process-persist lifecycle
4. Ensure no state lingers after response
5. Add idempotency for mutation operations

### MCP Tool Design

1. Treat each tool as a pure function
2. Accept all required identifiers as parameters
3. Fetch state at start, persist at end
4. Return complete response (no partial state)
5. No cross-call dependencies

## Reference Documentation

- **[statelessness-principles.md](references/statelessness-principles.md)** - Deep dive on statelessness theory
- **[anti-patterns.md](references/anti-patterns.md)** - Comprehensive anti-pattern catalog with detection strategies
- **[examples.md](references/examples.md)** - Complete FastAPI, MCP, and chat-based API examples

## Quick Reference

### Must Have
- Token/key authentication (JWT, API key)
- Database-backed state
- Request-scoped context
- Idempotency keys for mutations

### Must NOT Have
- Global variables with user data
- In-memory session storage
- Cached mutable user state
- Cross-request object state
- Server-affinity requirements

## Validation Script

Use the stateless validator to check code:

```bash
python scripts/stateless_validator.py <path-to-code>
```

Flags violations and suggests fixes.
