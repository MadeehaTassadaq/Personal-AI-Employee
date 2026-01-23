---
name: email-sender
description: Send emails via Gmail MCP server with approval workflow. Use when Claude needs to (1) send emails on behalf of the user, (2) create email drafts for approval, (3) respond to client communications, or (4) send scheduled follow-ups. ALWAYS requires human approval before sending.
---

# Email Sender

Send emails via Gmail MCP with mandatory approval workflow.

## MCP Tool

```
Tool: gmail_send_email
Parameters:
  - to: string (recipient email)
  - subject: string
  - body: string (plain text or HTML)
  - cc: string (optional)
  - bcc: string (optional)
```

## Approval Workflow

**All emails require human approval before sending.**

1. **Create approval request**: Write file to `$VAULT_PATH/Pending_Approval/`
2. **Wait for approval**: File moved to `$VAULT_PATH/Approved/`
3. **Check DRY_RUN**: If true, log but don't send
4. **Execute via MCP**: Call `gmail_send_email` tool
5. **Log action**: Record in `$VAULT_PATH/Logs/`
6. **Move to Done**: Move approval file to Done folder

## Approval File Format

```markdown
---
type: email_send
status: pending_approval
created: {{ISO_DATE}}
---

# Email Approval Request

**To:** recipient@example.com
**CC:** (if any)
**Subject:** Your subject here

## Email Body
{{The full email content}}

## Context
{{Why this email is being sent, what task it relates to}}

## Approval
- [ ] Approved by CEO
```

## Filename Convention

`email-{{slug}}-{{DATE}}.md`

Example: `email-client-update-2026-01-22.md`

## Rules

- NEVER send without approval file in Approved folder
- Check DRY_RUN environment variable before actual send
- Log all send attempts in vault/Logs/
- Include original task reference in context
- Handle MCP errors gracefully and report to user
