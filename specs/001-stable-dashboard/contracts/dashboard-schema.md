# Dashboard Schema Contract

**Feature**: 001-stable-dashboard
**Version**: 1.0.0
**Date**: 2026-02-01

## Overview

This document defines the structural contract for `Dashboard.md`. Any code that reads or writes the dashboard MUST conform to this schema.

---

## File Structure

```
Dashboard.md
├── Header (H1)
├── System Status (H2)
├── Pending Approvals (H2)
├── Active Tasks (H2)
├── Signals / Inputs (H2)
├── Recently Completed (H2)
├── Metrics (H2)
├── Weekly Summary (H2, collapsed)
└── Quick Actions (H2)
```

---

## Section Contracts

### 1. Header

**Marker**: `# Digital FTE Dashboard`

**Format**:
```markdown
# Digital FTE Dashboard

> Last Updated: {YYYY-MM-DD HH:MM:SS}

---
```

**Invariants**:
- MUST be first line of file
- Timestamp MUST use 24-hour format
- Horizontal rule MUST follow timestamp

---

### 2. System Status

**Marker**: `## System Status`

**Format**:
```markdown
## System Status

| Component | Status | Notes |
|-----------|--------|-------|
| {name} | {Active|Stopped|Error|Not Configured} | {notes} |

**Mode:** `DRY_RUN={true|false}` ({mode description})

---
```

**Invariants**:
- Table MUST have exactly 3 columns
- Status MUST be one of: Active, Stopped, Error, Not Configured
- Mode line MUST follow table

---

### 3. Pending Approvals

**Marker**: `## Pending Approvals`

**Format**:
```markdown
## Pending Approvals

> **{count} items awaiting your decision**

| Item | Type | Created | Action |
|------|------|---------|--------|
| {filename} | {type} | {YYYY-MM-DD HH:MM} | Move to `Approved/` or `Done/` |

**To approve:** Move file from `Pending_Approval/` to `Approved/`
**To reject:** Move file to `Done/` with rejection note

---
```

**Invariants**:
- Table MUST have exactly 4 columns
- Max 10 rows; if more, add overflow text before instructions
- Instructions MUST always be present

**Empty State**:
```markdown
## Pending Approvals

> **0 items awaiting your decision**

_No pending approvals_

---
```

---

### 4. Active Tasks

**Marker**: `## Active Tasks`

**Format**:
```markdown
## Active Tasks

| Task | Status | Started |
|------|--------|---------|
| {title} | {status} | {YYYY-MM-DD} |

---
```

**Invariants**:
- Table MUST have exactly 3 columns
- Max 10 rows

**Empty State**:
```markdown
## Active Tasks

| Task | Status | Started |
|------|--------|---------|
| _No tasks in progress_ | — | — |

---
```

---

### 5. Signals / Inputs

**Marker**: `## Signals / Inputs`

**Format**:
```markdown
## Signals / Inputs

> **{count} new items in Inbox/**

- [[Inbox/{filename}|{title}]]
- [[Inbox/{filename}|{title}]]

---
```

**Invariants**:
- Uses Obsidian wiki-link format
- Max 10 items
- Count in blockquote reflects total, not displayed

**Empty State**:
```markdown
## Signals / Inputs

> **0 new items in Inbox/**

_No new signals_

---
```

---

### 6. Recently Completed

**Marker**: `## Recently Completed`

**Format**:
```markdown
## Recently Completed

> Last 10 completed tasks

- [{YYYY-MM-DD}] {title}
- [{YYYY-MM-DD}] {title}

---
```

**Invariants**:
- Sorted by completion date, most recent first
- Max 10 items
- Date in brackets

**Empty State**:
```markdown
## Recently Completed

> Last 10 completed tasks

_No completed tasks_

---
```

---

### 7. Metrics

**Marker**: `## Metrics`

**Format**:
```markdown
## Metrics

| Metric | Today | This Week |
|--------|-------|-----------|
| Tasks Completed | {n} | {n} |
| Pending Approvals | {n} | — |
| Emails Sent | {n} | {n} |
| Social Posts | {n} | {n} |

---
```

**Invariants**:
- Table MUST have exactly 3 columns
- "This Week" for Pending Approvals is always "—" (not applicable)
- All values MUST be non-negative integers

---

### 8. Weekly Summary

**Marker**: `## Weekly Summary`

**Format**:
```markdown
<details>
<summary>## Weekly Summary (Week of {YYYY-MM-DD})</summary>

- **Total Tasks Completed**: {n}
- **Avg Time to Approval**: {n.n} hours
- **Actions by Type**: {type1} ({n}), {type2} ({n}), ...
- **System Uptime**: {n.n}%

</details>

---
```

**Invariants**:
- MUST use `<details>` tag for collapsibility
- Week start date is Monday of current week
- Metrics derived from Done/ folder and Logs/

---

### 9. Quick Actions

**Marker**: `## Quick Actions`

**Format**:
```markdown
## Quick Actions

- **Add task:** Create `.md` file in `Inbox/`
- **Approve action:** Move file from `Pending_Approval/` to `Approved/`
- **View logs:** Check `Logs/` folder
- **Reject action:** Move file from `Pending_Approval/` to `Done/`
```

**Invariants**:
- Static content (does not change between updates)
- No horizontal rule after (end of file)

---

## Validation Procedure

### Pre-Write Validation

Before writing Dashboard.md:

1. **Section Order Check**: Verify all 9 section markers appear in order
2. **Table Column Check**: Verify each table has correct column count
3. **Timestamp Check**: Verify Last Updated timestamp is valid
4. **Content Check**: Verify no raw HTML except `<details>` tags

### Post-Write Validation

After writing Dashboard.md:

1. **File Exists**: Dashboard.md was created/updated
2. **Readable**: File can be parsed as UTF-8 text
3. **Marker Integrity**: All section markers present

### Recovery Procedure

If validation fails:

1. Log error to `Logs/dashboard-recovery-{timestamp}.json`
2. Delete existing Dashboard.md
3. Regenerate entire dashboard from vault state
4. Re-run validation
5. If still fails, log critical error and preserve last-known-good backup

---

## Compatibility

### Obsidian

- Wiki-links use `[[path|display]]` format
- Mermaid diagrams NOT used (removed for simplicity)
- Standard Markdown tables

### LLM Processing

- Section markers enable reliable parsing
- No complex nested structures
- Clear separation between sections

### Version Control

- Single-line timestamp changes are expected
- Section boundaries enable clean diffs
- No binary content
