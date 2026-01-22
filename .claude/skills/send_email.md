---
skill_name: Send Email
version: 1.0
requires_approval: true
mcp_tool: gmail_send_email
---

# SKILL: Send Email

## Purpose
Send emails via Gmail using the MCP Gmail server.

## Inputs
- `to`: Recipient email address
- `subject`: Email subject line
- `body`: Email body (plain text or HTML)
- `cc`: (optional) CC recipients
- `bcc`: (optional) BCC recipients

## Approval Requirement
**This skill ALWAYS requires human approval before execution.**

Before sending:
1. Create draft in vault/Pending_Approval/
2. Wait for file to be moved to vault/Approved/
3. Only then execute via MCP tool

## MCP Tool
```
Tool: gmail_send_email
Parameters:
  - to: string
  - subject: string
  - body: string
  - cc: string (optional)
  - bcc: string (optional)
```

## Approval File Format
```markdown
---
type: email_send
status: pending_approval
created: {{ISO_DATE}}
---

# Email Approval Request

**To:** recipient@example.com
**Subject:** Your subject here

## Email Body
{{The full email content}}

## Context
{{Why this email is being sent}}

## Approval
- [ ] Approved by CEO
```

## Rules
- NEVER send without approval
- Check DRY_RUN flag before actual send
- Log all sends in vault/Logs/
- Include original task reference
- Handle errors gracefully

## Example Usage
```
Prepare email for approval:
- To: client@example.com
- Subject: Project Update - Q1 2026
- Body: Dear Client, Here is your weekly update...

Create approval request in vault/Pending_Approval/email-project-update.md
```
