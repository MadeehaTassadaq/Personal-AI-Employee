---
name: mcp-tool-engineering
description: Design, validate, and implement Model Context Protocol (MCP) tools for AI agents. Ensures tools are stateless, deterministic, secure, database-backed, agent-friendly, and idempotent. Use when creating MCP tools for backend integration, designing tool interfaces, validating stateless execution, implementing database persistence, or ensuring agent-safe tool behavior.
---

# MCP Tool Engineering Skill

## Overview

This skill provides comprehensive guidance for designing, validating, and implementing Model Context Protocol (MCP) tools used by AI agents to interact with application backends. The skill ensures MCP tools meet production standards for statelessness, determinism, security, and agent-friendliness.

## Core Objectives

MCP tools must be:
- Stateless
- Deterministic
- Secure
- Database-backed
- Agent-friendly
- Idempotent where applicable

## MCP Tool Structure (Mandatory)

Each MCP tool MUST define:
- Tool name (snake_case)
- Clear purpose
- Explicit parameters with types
- Required vs optional parameters
- Deterministic behavior
- Structured JSON output

## Required Tool Execution Flow

For every MCP tool invocation:

1. Validate input schema
2. Authenticate or authorize using provided user_id
3. Fetch required entities from database
4. Perform exactly one responsibility
5. Persist database changes
6. Return structured output
7. Release all runtime state

## Strict Enforcement Rules

When implementing MCP tools, you MUST:

- Never store state in memory between tool calls
- Never assume prior tool calls happened
- Require all identifiers (user_id, task_id, etc.) as parameters
- Validate all inputs explicitly
- Return structured, machine-readable outputs
- Persist all changes to the database
- Fail fast on invalid inputs
- Never return raw ORM or exception objects

## Inputs the Skill Accepts

- MCP tool definitions
- FastAPI endpoints backing MCP tools
- ORM logic for tools
- Agent tool call plans
- Tool error responses

## Outputs the Skill Produces

- Valid MCP tool specification
- Input/output schemas
- Tool pseudocode or reference implementation
- Validation and error-handling patterns
- Warnings for non-compliant tools

## Error Handling Requirements

Tools must return structured errors:

```json
{
  "error_code": "string",
  "error_message": "string",
  "recoverable": true/false
}
```

Never throw unhandled exceptions to the agent.

## Idempotency & Safety

The skill enforces:
- Idempotent behavior for read operations
- Safe retries for write operations
- Protection against duplicate execution
- Clear side-effect boundaries

## Anti-Patterns to Block

- Tools relying on in-memory state
- Tools chaining hidden side effects
- Tools with ambiguous parameters
- Returning natural language instead of structured data
- Mixing business logic across multiple tools
- Multi-responsibility tools

## Example MCP Tools

### add_task

**Purpose:** Create a new task for a user

**Input Schema:**
```json
{
  "user_id": "string (required)",
  "title": "string (required)",
  "description": "string (optional)",
  "due_date": "string (optional, ISO 8601)"
}
```

**Output Schema:**
```json
{
  "success": true,
  "task": {
    "id": "string",
    "user_id": "string",
    "title": "string",
    "description": "string",
    "due_date": "string",
    "status": "string",
    "created_at": "string (ISO 8601)"
  }
}
```

**Pseudocode:**
```
1. Validate input parameters
2. Verify user_id exists and is valid
3. Create new task record in database
4. Return created task details
```

**Error Cases:**
- Invalid user_id → USER_NOT_FOUND
- Missing required fields → INVALID_INPUT
- Database error → INTERNAL_ERROR

### list_tasks

**Purpose:** Retrieve tasks for a user

**Input Schema:**
```json
{
  "user_id": "string (required)",
  "status_filter": "string (optional, enum: all, pending, completed)",
  "limit": "number (optional, default: 50)",
  "offset": "number (optional, default: 0)"
}
```

**Output Schema:**
```json
{
  "success": true,
  "tasks": [
    {
      "id": "string",
      "user_id": "string",
      "title": "string",
      "description": "string",
      "due_date": "string",
      "status": "string",
      "created_at": "string"
    }
  ],
  "total_count": "number"
}
```

**Pseudocode:**
```
1. Validate input parameters
2. Verify user_id exists and is valid
3. Query tasks from database with filters
4. Return tasks array and total count
```

**Error Cases:**
- Invalid user_id → USER_NOT_FOUND
- Database error → INTERNAL_ERROR

### update_task

**Purpose:** Update an existing task

**Input Schema:**
```json
{
  "user_id": "string (required)",
  "task_id": "string (required)",
  "title": "string (optional)",
  "description": "string (optional)",
  "due_date": "string (optional)",
  "status": "string (optional, enum: pending, completed)"
}
```

**Output Schema:**
```json
{
  "success": true,
  "task": {
    "id": "string",
    "user_id": "string",
    "title": "string",
    "description": "string",
    "due_date": "string",
    "status": "string",
    "updated_at": "string"
  }
}
```

**Pseudocode:**
```
1. Validate input parameters
2. Verify user_id and task_id exist and match
3. Apply updates to task record in database
4. Return updated task details
```

**Error Cases:**
- Invalid user_id → USER_NOT_FOUND
- Invalid task_id → TASK_NOT_FOUND
- Task/user mismatch → PERMISSION_DENIED
- Invalid status → INVALID_INPUT

### complete_task

**Purpose:** Mark a task as completed

**Input Schema:**
```json
{
  "user_id": "string (required)",
  "task_id": "string (required)"
}
```

**Output Schema:**
```json
{
  "success": true,
  "task": {
    "id": "string",
    "user_id": "string",
    "title": "string",
    "status": "completed",
    "completed_at": "string"
  }
}
```

**Pseudocode:**
```
1. Validate input parameters
2. Verify user_id and task_id exist and match
3. Update task status to completed in database
4. Return updated task details
```

**Error Cases:**
- Invalid user_id → USER_NOT_FOUND
- Invalid task_id → TASK_NOT_FOUND
- Task/user mismatch → PERMISSION_DENIED

### delete_task

**Purpose:** Delete a task

**Input Schema:**
```json
{
  "user_id": "string (required)",
  "task_id": "string (required)"
}
```

**Output Schema:**
```json
{
  "success": true,
  "deleted_task_id": "string"
}
```

**Pseudocode:**
```
1. Validate input parameters
2. Verify user_id and task_id exist and match
3. Delete task record from database
4. Return confirmation of deletion
```

**Error Cases:**
- Invalid user_id → USER_NOT_FOUND
- Invalid task_id → TASK_NOT_FOUND
- Task/user mismatch → PERMISSION_DENIED

## Agent Interaction Guidelines

Tools should be designed so that:
- Agents can reason about results
- Agents can chain tools safely
- Agents can recover from errors
- Agents can confirm actions to users

## Versioning & Evolution

Recommendations:
- Use semantic versioning for tools (v1, v2, etc.)
- Maintain backward compatibility for minor changes
- Clearly document breaking changes
- Support deprecation periods for old versions

## Validation Checklist

Before deploying MCP tools, verify:

- [ ] Tool is stateless (no in-memory state between calls)
- [ ] Output is deterministic (same inputs produce same outputs)
- [ ] Agent can retry safely without side effects
- [ ] Any server instance can run this tool
- [ ] Tool is easy for LLMs to understand
- [ ] Input schema is explicit with types and validation
- [ ] Output schema is structured and machine-readable
- [ ] All required identifiers are parameters
- [ ] Database changes are persisted
- [ ] Error handling returns structured responses
- [ ] Tool has single responsibility
- [ ] Tool parameters are unambiguous

## Evaluation Criteria

The skill answers:

- Is this tool stateless?
- Is the output deterministic?
- Can the agent retry safely?
- Can any server instance run this tool?
- Is the tool easy for LLMs to understand?

## Rejection Criteria

Reject MCP tools that:
- Store state in memory between calls
- Assume prior tool calls happened
- Have ambiguous or missing parameters
- Return natural language instead of structured data
- Mix multiple responsibilities
- Don't persist changes to database
- Throw raw exceptions to agents
- Have hidden side effects