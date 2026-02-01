# Data Model: Stable Executive Dashboard

**Feature**: 001-stable-dashboard
**Date**: 2026-02-01

## Entities

### 1. Dashboard Section

A discrete, labeled block of content in the dashboard with defined boundaries and formatting rules.

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Human-readable section name |
| `marker` | string | Markdown heading that identifies this section (e.g., `## System Status`) |
| `format` | enum | `table`, `list`, or `prose` |
| `columns` | string[] | Column headers for table format (null for list/prose) |
| `max_items` | int | Maximum items to display (null = unlimited) |
| `overflow_text` | string | Text to show when items exceed max_items |
| `collapsed` | bool | Whether to use `<details>` tag (default: false) |

**Validation Rules**:
- `marker` MUST be unique across all sections
- `marker` MUST start with `## ` (H2 heading)
- `max_items` MUST be positive integer or null

---

### 2. Task Item

A file in the vault representing work to be done.

| Field | Type | Source | Description |
|-------|------|--------|-------------|
| `filename` | string | File path | Name without extension |
| `title` | string | Frontmatter | Human-readable title |
| `type` | string | Frontmatter | Task type (email, social, file, etc.) |
| `status` | enum | Frontmatter | `pending`, `in_progress`, `approved`, `rejected`, `completed` |
| `created` | datetime | Frontmatter | When task was created |
| `completed_at` | datetime | Frontmatter | When task was completed (Done/ only) |

**Validation Rules**:
- `created` MUST be ISO 8601 format or YAML datetime
- Files without valid frontmatter are skipped with warning

---

### 3. System Component

A monitored service with operational state.

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Component identifier (Vault, File Watcher, Gmail MCP, etc.) |
| `status` | enum | `Active`, `Stopped`, `Error`, `Not Configured` |
| `notes` | string | Additional context (e.g., "QR scan required") |

**Components Tracked**:
- Vault (always Active if accessible)
- File Watcher
- Gmail MCP
- WhatsApp MCP
- LinkedIn MCP
- Facebook MCP
- Instagram MCP
- Twitter MCP
- Calendar MCP

---

### 4. Metrics

Aggregated counts for dashboard display.

| Field | Type | Source | Description |
|-------|------|--------|-------------|
| `tasks_completed_today` | int | Done/ folder | Tasks completed today |
| `tasks_completed_week` | int | Done/ folder | Tasks completed this week |
| `pending_approvals` | int | Pending_Approval/ folder | Items awaiting approval |
| `emails_sent` | int | Logs/*.json | Email actions logged |
| `whatsapp_messages` | int | Logs/*.json | WhatsApp actions logged |
| `linkedin_posts` | int | Logs/*.json | LinkedIn actions logged |
| `facebook_posts` | int | Logs/*.json | Facebook actions logged |
| `instagram_posts` | int | Logs/*.json | Instagram actions logged |
| `twitter_posts` | int | Logs/*.json | Twitter actions logged |

---

## Section Definitions

### Canonical Section Order

```yaml
sections:
  1:
    name: "Header"
    marker: "# Digital FTE Dashboard"
    format: prose

  2:
    name: "System Status"
    marker: "## System Status"
    format: table
    columns: ["Component", "Status", "Notes"]
    max_items: null

  3:
    name: "Pending Approvals"
    marker: "## Pending Approvals"
    format: table
    columns: ["Item", "Type", "Created", "Action"]
    max_items: 10
    overflow_text: "View all ({count}) in `Pending_Approval/`"

  4:
    name: "Active Tasks"
    marker: "## Active Tasks"
    format: table
    columns: ["Task", "Status", "Started"]
    max_items: 10
    overflow_text: "View all ({count}) in `Needs_Action/`"

  5:
    name: "Signals / Inputs"
    marker: "## Signals / Inputs"
    format: list
    max_items: 10
    overflow_text: "{count} new items in `Inbox/`"

  6:
    name: "Recently Completed"
    marker: "## Recently Completed"
    format: list
    max_items: 10

  7:
    name: "Metrics"
    marker: "## Metrics"
    format: table
    columns: ["Metric", "Today", "This Week"]

  8:
    name: "Weekly Summary"
    marker: "## Weekly Summary"
    format: prose
    collapsed: true

  9:
    name: "Quick Actions"
    marker: "## Quick Actions"
    format: list
```

---

## State Transitions

### Task Lifecycle

```
                    ┌─────────────┐
                    │   Inbox/    │
                    │ (Signals)   │
                    └──────┬──────┘
                           │
              ┌────────────┴────────────┐
              │                         │
              ▼                         ▼
    ┌─────────────────┐      ┌──────────────────┐
    │  Needs_Action/  │      │ Pending_Approval/│
    │ (Active Tasks)  │      │ (Needs Decision) │
    └────────┬────────┘      └────────┬─────────┘
             │                        │
             │               ┌────────┴────────┐
             │               │                 │
             │               ▼                 ▼
             │      ┌────────────┐    ┌────────────┐
             │      │ Approved/  │    │   Done/    │
             │      │(Execute)   │    │ (Rejected) │
             │      └─────┬──────┘    └────────────┘
             │            │
             └────────────┼────────────────────────┐
                          │                        │
                          ▼                        │
                    ┌──────────┐                   │
                    │  Done/   │◄──────────────────┘
                    │(Completed)
                    └──────────┘
```

---

## File Formats

### Task File (YAML Frontmatter)

```yaml
---
title: "Post AI Healthcare Update to Facebook"
type: social
platform: facebook
status: pending
created: 2026-02-01T12:00:00+00:00
approved_at: null
completed_at: null
---

## Content

Post content here...

## Notes

Additional context...
```

### Log Entry (JSON in Logs/*.json)

```json
{
  "timestamp": "2026-02-01T15:30:00Z",
  "action": "email_sent",
  "task_id": "email-meeting-2026-02-01",
  "status": "success",
  "details": {
    "recipient": "user@example.com",
    "subject": "Meeting Reminder"
  }
}
```

---

## Validation Rules

### Dashboard Validation

Before writing Dashboard.md, validate:

1. All section markers present in correct order
2. No duplicate section markers
3. Tables have consistent column counts
4. Timestamps are valid ISO 8601

### Recovery Behavior

If validation fails:
1. Log warning to `Logs/`
2. Regenerate entire dashboard from vault state
3. Write fresh dashboard
4. Log recovery success
