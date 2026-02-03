# Company Handbook - Digital FTE Operations

> Version: 1.0
> Last Updated: 2026-01-23

---

## Overview

This handbook defines the operational rules and policies for the Digital FTE (Full-Time Employee) system. All automated actions must comply with these guidelines.

---

## Task Lifecycle

Tasks flow through the following folders:

```
Inbox/ --> Needs_Action/ --> Pending_Approval/ --> Approved/ --> Done/
                                      |
                                      v
                                   (Execute)
```

### Folder Definitions

| Folder | Purpose |
|--------|---------|
| `Inbox/` | New incoming tasks, not yet processed |
| `Needs_Action/` | Tasks being actively worked on |
| `Pending_Approval/` | Actions requiring human approval before execution |
| `Approved/` | Approved actions ready for execution |
| `Done/` | Completed tasks (archive) |
| `Logs/` | Activity audit trail |
| `Plans/` | Generated briefings and reports |

---

## Task File Format

All tasks must be Markdown files with YAML frontmatter:

```yaml
---
title: "Task Title"
created: 2026-01-23
priority: normal  # low | normal | high | urgent
status: inbox     # inbox | in_progress | pending_approval | approved | done
type: task        # task | email | whatsapp | linkedin | report
assignee: claude  # claude | human
---

## Description
What needs to be done.

## Action Items
- [ ] Step 1
- [ ] Step 2

## Notes
Additional context.
```

---

## Approval Requirements

### Actions Requiring Human Approval

The following actions MUST be moved to `Pending_Approval/` before execution:

| Action | Reason |
|--------|--------|
| Send email | Irreversible, represents user |
| Send WhatsApp message | Irreversible, represents user |
| Post to LinkedIn | Public, irreversible |
| Delete files | Destructive action |
| Modify external systems | Potential side effects |

### Auto-Approved Actions

The following actions can proceed without explicit approval:

| Action | Condition |
|--------|-----------|
| Create draft email | Does not send |
| Read vault files | Non-destructive |
| Move task files | Internal organization |
| Generate reports | Creates files only |
| Update Dashboard | Internal tracking |

---

## Communication Policies

### Email Policy

1. **Never send without approval** - Always create in `Pending_Approval/` first
2. **Use professional tone** - Formal business communication
3. **No sensitive data** - Never include passwords, tokens, or PII
4. **Reply context** - Always include original email context when replying
5. **Rate limit** - Maximum 10 emails per hour

### WhatsApp Policy

1. **Business hours only** - 9 AM to 6 PM local time
2. **Urgent only** - Use for time-sensitive matters
3. **Brief messages** - Keep under 500 characters
4. **No automation spam** - Each message requires unique context

### LinkedIn Policy

1. **Professional content only** - Business-relevant posts
2. **No controversial topics** - Politics, religion, sensitive matters
3. **Maximum 2 posts per day** - Avoid spam behavior
4. **Engagement allowed** - Can draft comments for approval

---

## Security Constraints

### Never Do

- Store or log credentials in plain text
- Include API keys in task files
- Send sensitive information via external channels
- Execute code from untrusted sources
- Access files outside the vault directory
- Bypass approval workflow for restricted actions

### Always Do

- Validate file paths before access
- Log all external actions to `Logs/`
- Check `DRY_RUN` flag before real actions
- Sanitize content before external transmission
- Respect rate limits

---

## DRY_RUN Mode

When `DRY_RUN=true` in environment:

- External actions are simulated, not executed
- Logs indicate `[DRY_RUN]` prefix
- Approval workflow still applies
- Use for testing and validation

To enable real actions, set `DRY_RUN=false` in `.env` file.

---

## Error Handling

### On Error

1. Log error details to `Logs/` folder
2. Move task to `Needs_Action/` with error note
3. Do NOT retry automatically
4. Notify via Dashboard update

### Retry Policy

- Maximum 3 retries for transient errors
- Exponential backoff: 1min, 5min, 15min
- After 3 failures, mark as blocked

---

## Audit Trail

All actions must be logged in `Logs/` folder:

```markdown
## [2026-01-23 15:30:00] Action Log

**Action:** send_email
**Status:** success | failed | dry_run
**Task:** task-filename.md
**Details:** Brief description
**Duration:** 1.2s
```

---

## Weekly Briefing

Generated every Monday at 9 AM:

- Summary of completed tasks
- Pending items requiring attention
- Metrics and statistics
- Recommendations

Output location: `Plans/weekly-briefing-YYYY-MM-DD.md`

---

---

## Gold Tier Operational Rules

### Approval Thresholds

| Action Type | Threshold | Rule |
|-------------|-----------|------|
| Email | All | Requires approval |
| WhatsApp | All | Requires approval |
| LinkedIn Post | All | Requires approval |
| Facebook Post | All | Requires approval |
| Instagram Post | All | Requires approval |
| Twitter/X | All | Requires approval |
| Internal File Operations | None | Auto-approved |
| Dashboard Updates | None | Auto-approved |
| Report Generation | None | Auto-approved |

### Watchdog Guardrails

The watchdog service monitors system health with these thresholds:

| Metric | Threshold | Action |
|--------|-----------|--------|
| Consecutive Failures | 5 | Auto-pause Ralph |
| Errors per Hour | 10 | Alert + Investigate |
| Pending Approvals | 25 | Pause new intake |
| Needs Action Queue | 30 | Pause new intake |

### Odoo Integration (Optional)

If Odoo is configured, the system provides:

- Invoice creation with approval
- Expense recording with approval
- Balance inquiries (read-only)
- Financial audit reports

**Configuration:**
```
ODOO_URL=http://localhost:8069
ODOO_DB=odoo
ODOO_USERNAME=admin
ODOO_PASSWORD=<secure_password>
```

---

## Contact

For issues with this system:
- Check `Logs/` for error details
- Review [[Dashboard]] for status
- Manual intervention may be required for blocked tasks
