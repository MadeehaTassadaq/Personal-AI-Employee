# MCP Tool Engineering - Quick Reference

## Purpose
This skill helps design, validate, and implement Model Context Protocol (MCP) tools that are:
- Stateless
- Deterministic
- Secure
- Database-backed
- Agent-friendly
- Idempotent where applicable

## Key Principles

### 1. Statelessness
- Never store state in memory between tool calls
- Never assume prior tool calls happened
- Always pass required identifiers (user_id, task_id, etc.) as parameters

### 2. Deterministic Output
- Same inputs should always produce same outputs
- No hidden dependencies or side effects

### 3. Proper Error Handling
- Return structured errors with error_code, error_message, and recoverable flag
- Never throw raw exceptions to agents

### 4. Database Persistence
- Persist all changes to the database
- Use atomic operations where needed

## Validation Checklist

Before deploying an MCP tool, ensure it:
- [ ] Is stateless (no in-memory state between calls)
- [ ] Has deterministic output
- [ ] Can be retried safely by agents
- [ ] Includes proper error handling
- [ ] Has clear input/output schemas
- [ ] Follows idempotency principles where appropriate

## Example Usage

```python
# Valid MCP tool structure
async def add_task(user_id: str, title: str, description: str = None):
    # 1. Validate inputs
    # 2. Authenticate using user_id
    # 3. Perform operation
    # 4. Persist to database
    # 5. Return structured output
    return {
        "success": True,
        "task": {
            "id": "task_id",
            "user_id": user_id,
            "title": title,
            # ... other fields
        }
    }
```

## Common Anti-Patterns to Avoid

- Tools relying on in-memory state
- Tools with ambiguous parameters
- Returning natural language instead of structured data
- Mixing multiple responsibilities in one tool
- Tools chaining hidden side effects