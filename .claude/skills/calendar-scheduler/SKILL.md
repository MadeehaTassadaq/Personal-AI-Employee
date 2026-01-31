---
name: calendar-scheduler
description: Manage Google Calendar events via MCP server with approval workflow. Use when Claude needs to (1) view upcoming events, (2) check availability, (3) schedule new meetings (requires approval), (4) update existing events (requires approval), or (5) delete events (requires approval). Read operations are auto-approved, write operations require human approval.
---

# Calendar Scheduler

Manage Google Calendar events via MCP with approval workflow for write operations.

## MCP Tools

### Read Operations (Auto-approved)

```
Tool: list_events
Parameters:
  - days: integer (number of days to look ahead, default: 7)
  - max_results: integer (max events to return, default: 20)

Tool: get_today_events
Parameters: none

Tool: get_free_busy
Parameters:
  - days: integer (number of days to check, default: 1)
```

### Write Operations (Require Approval)

```
Tool: create_event
Parameters:
  - summary: string (event title) [required]
  - start_time: string (ISO format, e.g., 2026-02-01T10:00:00) [required]
  - end_time: string (ISO format, e.g., 2026-02-01T11:00:00) [required]
  - description: string (event notes)
  - location: string (event location)
  - attendees: string (comma-separated emails)

Tool: update_event
Parameters:
  - event_id: string [required]
  - summary: string (new title)
  - start_time: string (new start time)
  - end_time: string (new end time)
  - description: string (new notes)
  - location: string (new location)

Tool: delete_event
Parameters:
  - event_id: string [required]
```

## Approval Workflow

**Event creation, updates, and deletions require human approval.**

1. **Create approval request**: Write file to `$VAULT_PATH/Pending_Approval/`
2. **Wait for approval**: File moved to `$VAULT_PATH/Approved/`
3. **Check DRY_RUN**: If true, log but don't execute
4. **Execute via MCP**: Call appropriate calendar tool
5. **Log action**: Record in `$VAULT_PATH/Logs/`
6. **Move to Done**: Move approval file to Done folder

## Approval File Format

### For Creating Events

```markdown
---
type: calendar_event
action: create
status: pending_approval
created: {{ISO_DATE}}
---

# Calendar Event: {{Event Title}}

**Start:** {{YYYY-MM-DD HH:MM AM/PM}}
**End:** {{YYYY-MM-DD HH:MM AM/PM}}
**Location:** {{Location if any}}
**Attendees:** {{Comma-separated emails}}

## Description
{{Event description/notes}}

## Context
{{Why this event is being scheduled, what task it relates to}}

## Approval
- [ ] Approved by CEO
```

### For Updating Events

```markdown
---
type: calendar_event
action: update
status: pending_approval
created: {{ISO_DATE}}
event_id: {{EVENT_ID}}
---

# Update Calendar Event

**Event ID:** {{EVENT_ID}}
**Current Title:** {{Current event title}}

## Changes
- **New Title:** {{if changed}}
- **New Start:** {{if changed}}
- **New End:** {{if changed}}
- **New Location:** {{if changed}}

## Context
{{Why this event is being updated}}

## Approval
- [ ] Approved by CEO
```

### For Deleting Events

```markdown
---
type: calendar_event
action: delete
status: pending_approval
created: {{ISO_DATE}}
event_id: {{EVENT_ID}}
---

# Delete Calendar Event

**Event ID:** {{EVENT_ID}}
**Event Title:** {{Current event title}}
**Scheduled:** {{Event date/time}}

## Reason
{{Why this event is being deleted}}

## Approval
- [ ] Approved by CEO
```

## Filename Convention

`calendar-{{action}}-{{slug}}-{{DATE}}.md`

Examples:
- `calendar-create-team-standup-2026-01-31.md`
- `calendar-update-client-call-2026-01-31.md`
- `calendar-delete-cancelled-meeting-2026-01-31.md`

## Usage Examples

### View Today's Schedule
```
Use get_today_events tool to see today's agenda.
No approval needed - read-only operation.
```

### Check Availability
```
Use get_free_busy tool with days=1 to check tomorrow's availability.
Use list_events with days=7 to see the week ahead.
```

### Schedule a Meeting
```
1. Create approval file in Pending_Approval/
2. Wait for file to appear in Approved/
3. Call create_event with all parameters
4. Log result and move file to Done/
```

## Rules

- NEVER create/update/delete events without approval file in Approved folder
- Read operations (list_events, get_today_events, get_free_busy) are always allowed
- Check DRY_RUN environment variable before actual modifications
- Log all actions in vault/Logs/
- Include timezone in approval files (user's local time preferred)
- For recurring events, specify in description how recurrence should work
- Handle MCP errors gracefully and report to user
